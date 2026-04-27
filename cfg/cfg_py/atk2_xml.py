# -*- coding: utf-8 -*-
#
#  TOPPERS ATK2 cfg (Python port) -- ARXML object model
#
#  C++ 版 toppers/xml/{xml_parser,cfg1_out,factory}.cpp の Python 移植．
#  pass1/2/3 の共通インフラとして:
#    - .arxml を Object / Parameter ツリーに展開
#    - 複数 .arxml の同名コンテナをマージ
#    - api-table CSV と照合して型と多重度を確定
#    - tfname (TSK / PRIORITY / ...) へのリネーム
#    - container 単位のレベル別 ID 振り分け
#    - INCLUDE 抽出 / valueof_* マクロ生成
#  を提供する．
#

import csv
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ----- AUTOSAR 名前空間 -----

_NS_R40 = "http://autosar.org/schema/r4.0"


def _ns(version: str) -> str:
    if version.startswith("4"):
        return _NS_R40
    if version.startswith("3"):
        return "http://autosar.org/3.1.4"
    raise ValueError(f"unsupported AUTOSARVersion {version!r}")


# ----- 型 -----

# Parameter.type の取りうる値．C++ 側 enum と対応．
TYPE_INT = "INT"
TYPE_FLOAT = "FLOAT"
TYPE_STRING = "STRING"
TYPE_BOOLEAN = "BOOLEAN"
TYPE_ENUM = "ENUM"
TYPE_REF = "REF"
TYPE_FUNCTION = "FUNCTION"
TYPE_INCLUDE = "INCLUDE"
TYPE_UNKNOWN = "UNKNOWN"


@dataclass
class Info:
    """api-table の 1 エントリ．C++ toppers::xml::info に対応．"""
    tfname: str = ""
    type: str = ""        # 文字列 ("INT", "+STRING", ... 元のままの形)
    type_enum: str = TYPE_UNKNOWN  # 上の TYPE_* の正規化値
    multimin: int = 0
    multimax: int = 1


@dataclass
class Parameter:
    def_name: str = ""    # 当初は full path /AUTOSAR/EcucDefs/...，rename 後は短い tfname
    value: str = ""
    type: str = TYPE_UNKNOWN
    file_name: str = ""
    line: int = 0
    parent: Optional["Object"] = None


@dataclass
class Object:
    def_name: str = ""
    obj_name: str = ""        # SHORT-NAME
    file_name: str = ""
    line: int = 0
    params: List[Parameter] = field(default_factory=list)
    subcontainers: List["Object"] = field(default_factory=list)
    parent: Optional["Object"] = None
    id: int = -1
    siblings: int = 0


# ----- ini-file パーサ -----

def parse_ini(path: str) -> Dict[str, str]:
    """`KEY=VALUE` 形式 (`;` 以降コメント) の ini を辞書化する．"""
    settings: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.split(";", 1)[0].strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            settings[k.strip()] = v.strip()
    return settings


# ----- api-table CSV パーサ -----

def parse_api_table(paths: List[str], container_path: str,
                    module_names: List[str]) -> Dict[str, Info]:
    """`--api-table` で渡された CSV から info_map を構築．

    container_path/module_names でフィルタする (C++ get_container_info_map 同等)．
    """
    info_map: Dict[str, Info] = {}
    for path in paths:
        for row in _read_csv(path):
            defref = row[0]
            # XML_ContainerPath/XML_ModuleName の組合せで in-scope 判定
            if not any(
                container_path + "/" + m in defref for m in module_names
            ):
                continue
            if len(row) < 2:
                raise SystemExit(f"too little fields in `{path}'")
            info = Info(tfname=row[1])
            if len(row) >= 3:
                info.type = row[2].strip()
                info.type_enum = _normalize_type(info.type)
            if len(row) >= 4 and row[3].strip():
                info.multimin = int(row[3])
                info.multimax = info.multimin
            if len(row) >= 5 and row[4].strip():
                if row[4].strip() == "*":
                    info.multimax = -1  # 無制限
                else:
                    info.multimax = int(row[4])
            info_map[defref] = info
    return info_map


def _read_csv(path: str) -> List[List[str]]:
    rows: List[List[str]] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            if not row or row[0].startswith("#"):
                continue
            rows.append(row)
    return rows


def _normalize_type(s: str) -> str:
    """`+STRING` `+INCLUDE` 等の `+` 接頭辞を取り除き，正規化された TYPE_* に変換．

    `+` 付きは parsed XML 由来の type を **上書き** する意味．
    """
    raw = s.lstrip("+").upper()
    return {
        "INT": TYPE_INT, "FLOAT": TYPE_FLOAT, "STRING": TYPE_STRING,
        "BOOLEAN": TYPE_BOOLEAN, "ENUM": TYPE_ENUM, "REF": TYPE_REF,
        "FUNCTION": TYPE_FUNCTION, "INCLUDE": TYPE_INCLUDE,
    }.get(raw, TYPE_UNKNOWN)


# ----- cfg1-def-table CSV パーサ -----

@dataclass
class Cfg1Def:
    name: str
    expression: str
    is_signed: bool = False
    value1: str = ""
    value2: str = ""


def parse_cfg1_def_table(paths: List[str]) -> List[Cfg1Def]:
    out: List[Cfg1Def] = []
    for path in paths:
        for row in _read_csv(path):
            if len(row) < 2:
                raise SystemExit(f"too little fields in `{path}'")
            d = Cfg1Def(name=row[0], expression=row[1])
            if len(row) >= 3:
                d.is_signed = row[2].strip() in ("s", "signed")
            if len(row) >= 4:
                d.value1 = row[3]
            if len(row) >= 5:
                d.value2 = row[4]
            out.append(d)
    return out


# ----- ARXML パース -----

def parse_arxml_files(paths: List[str], version: str = "4") -> List[Object]:
    """各 .arxml をパースし，ECUC-MODULE-CONFIGURATION-VALUES の一覧を返す．

    複数ファイル間のマージは呼び出し側で merge_containers() を行う想定．
    """
    ns = _ns(version)
    all_modules: List[Object] = []
    for path in paths:
        try:
            tree = ET.parse(path)
        except ET.ParseError as e:
            raise SystemExit(f"\nError during parsing: '{path}'\n{e}\n")
        root = tree.getroot()
        for module_el in root.iter(f"{{{ns}}}ECUC-MODULE-CONFIGURATION-VALUES"):
            mod_obj = _parse_module(module_el, ns, path)
            if mod_obj is not None:
                all_modules.append(mod_obj)
    return all_modules


def _parse_module(elem, ns: str, file_name: str) -> Optional[Object]:
    """ECUC-MODULE-CONFIGURATION-VALUES → 1 個の Object を作る．"""
    short_name = _findtext(elem, "SHORT-NAME", ns)
    def_ref = _findtext(elem, "DEFINITION-REF", ns)
    obj = Object(
        def_name=def_ref,
        obj_name=short_name,
        file_name=file_name,
        line=_lineno(elem),
        id=1,
    )
    obj.parent = obj  # C++ では root object の parent は self を指す
    cont_block = _find(elem, "CONTAINERS", ns)
    if cont_block is not None:
        for cv in _findall(cont_block, "ECUC-CONTAINER-VALUE", ns):
            child = _parse_container(cv, ns, file_name, parent=obj)
            obj.subcontainers.append(child)
    return obj


def _parse_container(elem, ns: str, file_name: str,
                     parent: Object) -> Object:
    short_name = _findtext(elem, "SHORT-NAME", ns)
    def_ref = _findtext(elem, "DEFINITION-REF", ns)
    obj = Object(
        def_name=def_ref,
        obj_name=short_name,
        file_name=file_name,
        line=_lineno(elem),
        parent=parent,
    )
    # PARAMETER-VALUES
    pv_block = _find(elem, "PARAMETER-VALUES", ns)
    if pv_block is not None:
        for child in pv_block:
            local = _local(child.tag)
            if local in (
                "ECUC-TEXTUAL-PARAM-VALUE",
                "ECUC-NUMERICAL-PARAM-VALUE",
                # R3.x 互換は省略
            ):
                p = _parse_param(child, ns, file_name, obj)
                if p is not None:
                    obj.params.append(p)
    # REFERENCE-VALUES
    rv_block = _find(elem, "REFERENCE-VALUES", ns)
    if rv_block is not None:
        for child in rv_block:
            local = _local(child.tag)
            if local == "ECUC-REFERENCE-VALUE":
                p = _parse_reference(child, ns, file_name, obj)
                if p is not None:
                    obj.params.append(p)
    # SUB-CONTAINERS (再帰)
    sub_block = _find(elem, "SUB-CONTAINERS", ns)
    if sub_block is not None:
        for cv in _findall(sub_block, "ECUC-CONTAINER-VALUE", ns):
            sub = _parse_container(cv, ns, file_name, parent=obj)
            obj.subcontainers.append(sub)
    return obj


def _parse_param(elem, ns: str, file_name: str,
                 parent: Object) -> Optional[Parameter]:
    """ECUC-{TEXTUAL,NUMERICAL}-PARAM-VALUE を Parameter にする．"""
    def_ref_el = _find(elem, "DEFINITION-REF", ns)
    if def_ref_el is None:
        return None
    def_ref = (def_ref_el.text or "").strip()
    dest = def_ref_el.get("DEST", "")
    value = _findtext(elem, "VALUE", ns)
    p = Parameter(
        def_name=def_ref,
        value=value,
        file_name=file_name,
        line=_lineno(elem),
        parent=parent,
    )
    # tag 名と DEST から仮の type を決める．api-table で上書きされ得る．
    local = _local(elem.tag)
    if local == "ECUC-TEXTUAL-PARAM-VALUE":
        p.type = TYPE_STRING
    elif local == "ECUC-NUMERICAL-PARAM-VALUE":
        p.type = TYPE_INT
    if dest in ("ECUC-INTEGER-PARAM-DEF",):
        p.type = TYPE_INT
    elif dest in ("ECUC-FLOAT-PARAM-DEF",):
        p.type = TYPE_FLOAT
    elif dest in ("ECUC-STRING-PARAM-DEF",):
        p.type = TYPE_STRING
    elif dest in ("ECUC-BOOLEAN-PARAM-DEF",):
        p.type = TYPE_BOOLEAN
    elif dest in ("ECUC-ENUMERATION-PARAM-DEF",):
        p.type = TYPE_ENUM
    elif dest in ("ECUC-FUNCTION-NAME-DEF",):
        p.type = TYPE_FUNCTION
    elif dest in ("ECUC-REFERENCE-DEF",):
        p.type = TYPE_REF
    return p


def _parse_reference(elem, ns: str, file_name: str,
                     parent: Object) -> Optional[Parameter]:
    def_ref_el = _find(elem, "DEFINITION-REF", ns)
    if def_ref_el is None:
        return None
    def_ref = (def_ref_el.text or "").strip()
    value = _findtext(elem, "VALUE-REF", ns)
    p = Parameter(
        def_name=def_ref,
        value=value,
        type=TYPE_REF,
        file_name=file_name,
        line=_lineno(elem),
        parent=parent,
    )
    return p


# ----- ElementTree ヘルパ -----

def _find(elem, local, ns):
    return elem.find(f"{{{ns}}}{local}")


def _findall(elem, local, ns):
    return elem.findall(f"{{{ns}}}{local}")


def _findtext(elem, local, ns, default=""):
    e = _find(elem, local, ns)
    return (e.text or default).strip() if e is not None else default


def _local(tag):
    return tag.split("}", 1)[1] if "}" in tag else tag


def _lineno(elem):
    # ElementTree は line 情報を持たないので 0 を返す．
    # (C++ では SAX の locator から取れるが今回不要)
    return getattr(elem, "_line", 0)


# ----- 複数 .arxml のマージ -----

def merge_modules(modules: List[Object]) -> List[Object]:
    """同じ DEFINITION-REF のモジュールどうしをマージする．

    モジュール (例: Os) のサブコンテナ群を，同名 (= shortname) の
    コンテナどうしを束ねつつ統合する．
    """
    merged: List[Object] = []
    for m in modules:
        existing = next(
            (x for x in merged if x.def_name == m.def_name), None,
        )
        if existing is None:
            merged.append(m)
            continue
        # 既存 module の subcontainers に m の subcontainers をマージ
        for sub in m.subcontainers:
            _merge_container(existing.subcontainers, sub, existing)
    return merged


def _merge_container(siblings: List[Object], new: Object,
                     parent: Object) -> None:
    """同じ defref + shortname のコンテナがあれば params/subs を取り込む．

    無ければ new をそのまま追加．
    """
    for s in siblings:
        if s.def_name == new.def_name and s.obj_name == new.obj_name:
            # 同一コンテナ: params を追加
            for p in new.params:
                p.parent = s
                s.params.append(p)
            # 子コンテナを再帰マージ
            for sub in new.subcontainers:
                _merge_container(s.subcontainers, sub, s)
            return
    # マージ対象なし: 新規追加
    new.parent = parent
    siblings.append(new)


# ----- モジュールフィルタ -----

def filter_modules(modules: List[Object], container_path: str,
                   module_names: List[str]) -> List[Object]:
    """XML_ContainerPath / XML_ModuleName と合致しないモジュールを除外する．"""
    keep = []
    targets = {f"{container_path}/{m}" for m in module_names}
    for m in modules:
        if any(t in m.def_name for t in targets):
            keep.append(m)
    return keep


# ----- リネーム (replase_xml_pathname の Python 版) -----

def replace_pathnames(modules: List[Object],
                      info_map: Dict[str, Info]) -> None:
    """module/container/parameter の def_name を api-table の tfname に置換．

    C++ cfg1_out::replase_xml_pathname (cfg1_out.cpp:1053-1075) と同等．
    対象が info_map に登録されていない場合は元のフルパスのまま．
    """
    for m in modules:
        # module 自身は OS / Os 等．通常 tfname は短いが api-table に
        # エントリがあれば置換．
        info = info_map.get(m.def_name)
        if info is not None and info.tfname:
            m.def_name = _replace_first(m.def_name, info.tfname, info.tfname)
        for sub in m.subcontainers:
            _replace_in_container(sub, info_map)


def _replace_in_container(obj: Object, info_map: Dict[str, Info]) -> None:
    info = info_map.get(obj.def_name)
    if info is not None and info.tfname:
        obj.def_name = info.tfname  # フルパスを丸ごと tfname に置換
    for p in obj.params:
        info_p = info_map.get(p.def_name)
        if info_p is not None and info_p.tfname:
            p.def_name = info_p.tfname
            # `+` 接頭辞付きの type は parsed XML を上書き
            if info_p.type.startswith("+") and info_p.type_enum != TYPE_UNKNOWN:
                p.type = info_p.type_enum
            elif info_p.type_enum != TYPE_UNKNOWN:
                # 通常: parsed XML の type と一致するはず (検証で確認)
                p.type = info_p.type_enum
    for sub in obj.subcontainers:
        _replace_in_container(sub, info_map)


def _replace_first(s: str, old: str, new: str) -> str:
    """C++ Replace の最小再現 (今回は完全一致時に置換するだけで足りる)．"""
    if s == old:
        return new
    return s


# ----- xml_obj_map: tfname → list[Object] のグループ化 -----

def build_xml_obj_map(modules: List[Object]) -> Dict[str, List[Object]]:
    """全モジュール / コンテナ / サブコンテナを tfname (= def_name) で
    グルーピングした辞書を作る．

    C++ cfg1_out::do_merge / do_sub_merge 相当．
    """
    out: Dict[str, List[Object]] = {}
    for m in modules:
        for top in m.subcontainers:
            out.setdefault(top.def_name, []).append(top)
            _add_subcontainers(top, out)
    return out


def _add_subcontainers(obj: Object, out: Dict[str, List[Object]]) -> None:
    for sub in obj.subcontainers:
        out.setdefault(sub.def_name, []).append(sub)
        _add_subcontainers(sub, out)


# ----- ID 振り分け -----

def assign_ids(xml_obj_map: Dict[str, List[Object]]) -> None:
    """tfname ごとに 1-origin の ID を振る．

    サブコンテナは親の ID を継承 (ID 未設定なら親の ID をコピー)．
    C++ assign_id (cfg1_out.cpp:100-125) + child_assign_id 相当．
    """
    for tfname, objs in xml_obj_map.items():
        serial = 1
        for obj in objs:
            obj.id = serial
            for sub in obj.subcontainers:
                _child_assign_id(sub, serial)
            serial += 1


def _child_assign_id(obj: Object, fixed_id: int) -> None:
    for sub in obj.subcontainers:
        _child_assign_id(sub, fixed_id)
    if obj.id < 0:
        obj.id = fixed_id


def assign_siblings(xml_obj_map: Dict[str, List[Object]]) -> None:
    """tfname グループの兄弟数 (siblings) を各 obj に付与する．

    C++ cfg1_out::do_sub_siblings 相当．
    """
    for tfname, objs in xml_obj_map.items():
        n = len(objs)
        for o in objs:
            o.siblings = n
            _do_sub_siblings(o)


def _do_sub_siblings(obj: Object) -> None:
    sn = len(obj.subcontainers)
    for sub in obj.subcontainers:
        sub.siblings = sn
        _do_sub_siblings(sub)


# ----- INCLUDE 抽出 -----

def search_includes(modules: List[Object],
                    info_map: Dict[str, Info]) -> List[str]:
    """INCLUDE タイプのパラメータ値を出現順 (深さ優先) に集める．

    info_map で INCLUDE に該当する defref を探す (rename 後は tfname 等
    なので元の info_map.values() を確認する形)．
    """
    include_tfnames = {info.tfname for info in info_map.values()
                       if info.type_enum == TYPE_INCLUDE}
    # rename 前のパスでも一致させる必要がある (rename 適用前に呼ばれる
    # ケースがあるため)．
    include_full = {k for k, v in info_map.items()
                    if v.type_enum == TYPE_INCLUDE}
    out: List[str] = []
    for m in modules:
        for sub in m.subcontainers:
            _walk_includes(sub, include_tfnames | include_full, out)
    return out


def _walk_includes(obj: Object, include_keys: set, out: List[str]) -> None:
    for p in obj.params:
        if p.def_name in include_keys:
            if p.value:
                out.append(p.value)
    for sub in obj.subcontainers:
        _walk_includes(sub, include_keys, out)


# ----- valueof_* マクロ生成 -----

def search_valueof_macros(modules: List[Object]) -> List[str]:
    """INT/FLOAT で値が数値リテラルでないパラメータを `TOPPERS_cfg_valueof_*`
    形式の C 行として返す．

    C++ cfg1_out::do_search_macro / do_out_macro_name (cfg1_out.cpp:295-372) 相当．
    """
    out: List[str] = []
    for m in modules:
        for sub in m.subcontainers:
            _walk_valueof(sub, out)
    return out


def _walk_valueof(obj: Object, out: List[str]) -> None:
    for sub in obj.subcontainers:
        _walk_valueof(sub, out)
    for p in obj.params:
        line = _maybe_valueof_line(p)
        if line:
            out.append(line)


_NUMERIC_INT_RE = re.compile(r'^-?(?:0[xX][0-9a-fA-F]+|0[0-7]*|[1-9][0-9]*)$')
_NUMERIC_FLOAT_RE = re.compile(
    r'^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$'
)


def _maybe_valueof_line(p: Parameter) -> Optional[str]:
    if p.type not in (TYPE_INT, TYPE_FLOAT):
        return None
    val = p.value
    if p.type == TYPE_INT and _NUMERIC_INT_RE.match(val):
        return None
    if p.type == TYPE_FLOAT and _NUMERIC_FLOAT_RE.match(val):
        return None
    container = p.parent
    if container is None:
        return None
    grand = container.parent
    grand_name = grand.obj_name if grand is not None else ""
    cdef = container.def_name.replace(".", "_")
    pdef = p.def_name.replace(".", "_")
    return (
        f"const unsigned_t TOPPERS_cfg_valueof_{cdef}_{pdef}_"
        f"{container.obj_name}_{grand_name} = ( {val} ); \n"
    )


# ----- パイプライン全体 -----

@dataclass
class XmlContext:
    """parse_arxml_files + 後処理を済ませた状態を保持するハンドル．"""
    modules: List[Object]
    info_map: Dict[str, Info]
    settings: Dict[str, str]
    container_path: str
    module_names: List[str]
    xml_obj_map: Dict[str, List[Object]] = field(default_factory=dict)
    includes: List[str] = field(default_factory=list)
    valueof_macros: List[str] = field(default_factory=list)


def build(arxml_paths: List[str],
          api_table_paths: List[str],
          ini_paths: List[str]) -> XmlContext:
    """pass1/2/3 の前処理を共通化したエントリ．

    1. ini-file 読込
    2. api-table 読込
    3. .arxml パース → モジュール一覧
    4. モジュールマージ
    5. モジュールフィルタ (XML_ModuleName)
    6. INCLUDE 抽出 (rename 前に: info_map のフルパスでも一致するため)
    7. valueof_* マクロ抽出
    8. tfname リネーム
    9. xml_obj_map 構築
    10. ID/siblings 振り分け
    """
    settings: Dict[str, str] = {}
    for ip in ini_paths:
        settings.update(parse_ini(ip))
    version = settings.get("AUTOSARVersion", "4")
    container_path = settings.get("ContainerPath", "/AUTOSAR/EcucDefs")
    module_names = [m.strip()
                    for m in settings.get("ModuleName", "Os").split(",")
                    if m.strip()]
    info_map = parse_api_table(api_table_paths, container_path, module_names)
    modules = parse_arxml_files(arxml_paths, version=version)
    modules = merge_modules(modules)
    modules = filter_modules(modules, container_path, module_names)
    includes = search_includes(modules, info_map)
    valueof = search_valueof_macros(modules)
    replace_pathnames(modules, info_map)
    xml_obj_map = build_xml_obj_map(modules)
    assign_ids(xml_obj_map)
    assign_siblings(xml_obj_map)
    return XmlContext(
        modules=modules,
        info_map=info_map,
        settings=settings,
        container_path=container_path,
        module_names=module_names,
        xml_obj_map=xml_obj_map,
        includes=includes,
        valueof_macros=valueof,
    )
