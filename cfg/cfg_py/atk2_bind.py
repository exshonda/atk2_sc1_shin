# -*- coding: utf-8 -*-
#
#  TOPPERS ATK2 cfg (Python port) -- macro_processor binding
#
#  C++ factory.cpp の set_object_vars (line 315-651) と
#  set_platform_vars (line 656-735) を Python に移植する．
#  XML 木 (atk2_xml.XmlContext) と cfg1_def_table と srec/syms から
#  tf_engine 用の context (dict) を構築する．
#

import os
from typing import Any, Dict, List, Optional, Tuple

from atk2_xml import (
    Cfg1Def, Object, Parameter, XmlContext,
    TYPE_INT, TYPE_FLOAT, TYPE_BOOLEAN, TYPE_REF, TYPE_UNKNOWN,
)


# ----- 補助 -----

def _elem_int(value: int, s: Optional[str] = None) -> Dict[str, Any]:
    return {"i": int(value), "s": s if s is not None else str(value)}


def _elem_str(s: str) -> Dict[str, Any]:
    return {"s": s}


def _elem_both(i: int, s: str) -> Dict[str, Any]:
    return {"i": int(i), "s": s}


# ----- 参照解決 -----

def _find_object_by_short_name(xml_obj_map: Dict[str, List[Object]],
                                value_ref: str) -> Optional[Object]:
    """VALUE-REF の末尾の SHORT-NAME に一致する Object を全グループから探す．

    C++ find_object (factory.cpp:85-118) の主たる動作 (= 末尾名一致) を再現．
    """
    if not value_ref:
        return None
    last = value_ref.rsplit("/", 1)[-1]
    found = None
    for objs in xml_obj_map.values():
        for o in objs:
            if o.obj_name == last:
                found = o
    return found


# ----- numeric param 値の評価 -----

def _try_int(s: str) -> Optional[int]:
    s = s.strip()
    try:
        if s.startswith(("0x", "0X")):
            return int(s, 16)
        if s.startswith("0") and len(s) > 1 and all(c in "01234567" for c in s[1:]):
            return int(s, 8)
        return int(s, 10)
    except (ValueError, TypeError):
        return None


def _try_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


# ----- 平台 (cfg1_def_table) 由来の binding -----

def bind_platform_vars(ctx: Dict[str, Any],
                        cfg1_def_table: List[Cfg1Def],
                        srec, syms: Optional[Dict[str, int]],
                        ) -> Tuple[bool, int, int]:
    """C++ set_platform_vars の Python 移植．

    戻り値: (little_endian, sizeof_signed_t, sizeof_pointer)．
    syms/srec が None の場合は 4 (sizeof_signed_t) と 4 (sizeof_pointer) を仮値で
    使う ─ omit-symbol モード相当．platform 値はバインドしない．
    """
    little_endian = True
    sizeof_signed_t = 4
    sizeof_pointer = 4
    if srec is not None and syms is not None:
        # マジックナンバーから endianness 確定
        magic_addr = syms.get("TOPPERS_cfg_magic_number")
        if magic_addr is not None:
            magic_bytes = [srec.get_value(magic_addr + i, 1, False)
                           for i in range(4)]
            be_value = (magic_bytes[0] << 24) | (magic_bytes[1] << 16) \
                | (magic_bytes[2] << 8) | magic_bytes[3]
            if be_value == 0x12345678:
                little_endian = False
            elif be_value == 0x78563412:
                little_endian = True
        srec.endian_little = little_endian
        # sizeof_signed_t / sizeof_pointer
        addr = syms.get("TOPPERS_cfg_sizeof_signed_t")
        if addr is not None:
            sizeof_signed_t = int(srec.get_value(addr, 4, False))
        addr = syms.get("TOPPERS_cfg_sizeof_pointer")
        if addr is not None:
            sizeof_pointer = int(srec.get_value(addr, 4, False))
        # 各 cfg1_def_table エントリを ROM から読む
        for d in cfg1_def_table:
            sym = "TOPPERS_cfg_" + d.name
            addr = syms.get(sym)
            if addr is None:
                continue
            if d.expression.startswith("@"):
                # ポインタ: アドレス → 間接参照
                value = int(srec.get_value(addr, sizeof_pointer,
                                           d.is_signed))
                # 間接参照 (8 バイト固定)
                try:
                    value = int(srec.get_value(value, 8, d.is_signed))
                except Exception:
                    pass
                expr_text = d.expression[1:]
            else:
                value = int(srec.get_value(addr, sizeof_signed_t, d.is_signed))
                expr_text = d.expression
            ctx[d.name] = _elem_both(value, expr_text)
    # endian の binding
    ctx["LITTLE_ENDIAN"] = _elem_int(1 if little_endian else 0)
    ctx["BIG_ENDIAN"] = _elem_int(0 if little_endian else 1)
    return little_endian, sizeof_signed_t, sizeof_pointer


# ----- XML 由来の binding -----

def bind_object_vars(ctx: Dict[str, Any], xml_obj_map: Dict[str, List[Object]],
                      srec=None, syms: Optional[Dict[str, int]] = None,
                      sizeof_signed_t: int = 4) -> None:
    """C++ set_object_vars の Python 移植．"""
    little = (srec is None) or srec.endian_little
    order_list_map: Dict[str, List[Dict[str, Any]]] = {}
    for tfname, objs in xml_obj_map.items():
        for obj in objs:
            obj_id = obj.id
            obj_elem = _elem_both(obj_id, obj.obj_name)
            order_list_map.setdefault(tfname, []).append(obj_elem)
            # OBJ[id] = {i: id, s: shortname}
            ctx[f"{tfname}[{obj_id}]"] = [obj_elem]
            # OBJ.PARENT[id]
            if obj.parent is not None and obj.parent is not obj:
                pe = _elem_both(obj.parent.id if obj.parent.id > 0 else 0,
                                obj.parent.obj_name)
                ctx[f"{tfname}.PARENT[{obj_id}]"] = [pe]
            # 各 param を蓄積
            obj_param: Dict[str, List[Dict[str, Any]]] = {}
            for p in obj.params:
                if p.value == "" or "/" in p.def_name:
                    # rename されなかったパラメータはスキップ
                    continue
                pname = f"{tfname}.{p.def_name}"
                e: Dict[str, Any] = {"s": p.value}
                if p.type in (TYPE_INT, TYPE_FLOAT):
                    iv = _try_int(p.value) if p.type == TYPE_INT \
                        else _try_float(p.value)
                    if iv is not None and isinstance(iv, int):
                        e["i"] = iv
                    elif iv is not None and isinstance(iv, float):
                        # FLOAT の場合: e.i = int(value)，e.s は %f 既定精度
                        # でフォーマットし直す (C++ 互換: "1.0e-06" → "0.000001")．
                        e["i"] = int(iv)
                        e["s"] = format(iv, "f")
                    else:
                        # symbol lookup: TOPPERS_cfg_valueof_<C>_<P>_<O>_<G>
                        cdef = (p.parent.def_name if p.parent else "").replace(".", "_")
                        pdef = p.def_name.replace(".", "_")
                        gname = (p.parent.parent.obj_name
                                 if (p.parent and p.parent.parent) else "")
                        sym = (f"TOPPERS_cfg_valueof_{cdef}_{pdef}_"
                               f"{p.parent.obj_name if p.parent else ''}_{gname}")
                        addr = syms.get(sym) if syms else None
                        if addr is not None and srec is not None:
                            e["i"] = int(srec.get_value(
                                addr, sizeof_signed_t, False))
                        else:
                            e["i"] = 0
                elif p.type == TYPE_REF:
                    target = _find_object_by_short_name(xml_obj_map, p.value)
                    if target is not None:
                        e["i"] = target.id
                        # shortname だけにする
                        e["s"] = target.obj_name
                    else:
                        e["i"] = 0
                elif p.type == TYPE_BOOLEAN:
                    v = p.value.lower()
                    e["i"] = 1 if v in ("1", "true", "on", "enable") else 0
                else:
                    e["i"] = 0
                if p.type != TYPE_UNKNOWN:
                    obj_param.setdefault(pname, []).append(e)
                    # *.TEXT_LINE[obj_id]
                    ctx[f"{pname}.TEXT_LINE[{obj_id}]"] = [
                        _elem_both(p.line + 1, p.file_name)
                    ]
            for pname, vlist in obj_param.items():
                ctx[f"{pname}[{obj_id}]"] = vlist
            # OBJ.TEXT_LINE[id]
            ctx[f"{tfname}.TEXT_LINE[{obj_id}]"] = [
                _elem_both(obj.line + 1, obj.file_name)
            ]
    # ORDER_LIST / RORDER_LIST / ID_LIST
    for tfname, elist in order_list_map.items():
        ctx[f"{tfname}.ORDER_LIST"] = list(elist)
        ctx[f"{tfname}.RORDER_LIST"] = list(reversed(elist))
        # ID_LIST: id でソート
        ctx[f"{tfname}.ID_LIST"] = sorted(elist, key=lambda e: e["i"])


# ----- 上位 API -----

def build_context(xc: XmlContext, cfg1_def_table: List[Cfg1Def],
                   srec=None, syms: Optional[Dict[str, int]] = None,
                   pass_num: int = 2,
                   includes_text: str = "",
                   external_id: bool = False,
                   timestamp: int = 0,
                   version: str = "1.7.0") -> Dict[str, Any]:
    """tf_engine.run() に渡す context dict を組み立てる．"""
    ctx: Dict[str, Any] = {}
    # 標準特殊変数
    ctx["SPC"] = " "
    ctx["TAB"] = "\t"
    ctx["NL"] = "\n"
    ctx["CFG_VERSION"] = _elem_both(timestamp, version)
    ctx["CFG_PASS"] = _elem_int(pass_num)
    ctx["CFG_XML"] = _elem_int(1)
    ctx["INCLUDES"] = _elem_str(includes_text)
    ctx["USE_EXTERNAL_ID"] = _elem_int(1 if external_id else 0)
    # 平台 (cfg1_def_table)
    little_endian, sizeof_signed_t, sizeof_pointer = bind_platform_vars(
        ctx, cfg1_def_table, srec, syms,
    )
    # XML 由来
    bind_object_vars(ctx, xc.xml_obj_map, srec=srec, syms=syms,
                      sizeof_signed_t=sizeof_signed_t)
    return ctx


def read_symbol_file(path: str) -> Dict[str, int]:
    """nm 形式 (`<addr> <type> <name>`) の symbol テーブルを dict に．

    cfg.py 既存の read_symbol_file を流用する形で再実装．
    """
    out: Dict[str, int] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 3:
                try:
                    out[parts[2]] = int(parts[0], 16)
                except ValueError:
                    pass
    return out
