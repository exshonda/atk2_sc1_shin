# -*- coding: utf-8 -*-
#
#  TOPPERS .tf template engine (Python port) -- public API
#
#  Phase 4 の atk2_pass2 / atk2_pass3 から呼ばれるエントリポイント．
#  合成 context (dict) を受けて .tf を評価し，{file_name: text} を返す．
#

from typing import Dict, List, Optional, Any

from tf_lexer import preprocess, split_segments
from tf_parser import parse
from tf_eval import Context, exec_document
from tf_value import Element, Var, DieTerminate, make_str, make_int
from tf_builtin import BUILTINS


def _coerce_var(value: Any) -> Var:
    """合成 context から渡される値を Var (List[Element]) に正規化する．

    - 既に list[Element] ならそのまま
    - int → 1 要素 (i のみ)
    - str → 1 要素 (s のみ)
    - list of (int|str|Element|dict) → 各要素を Element に変換
    - dict {"i": ..., "s": ...} → 単一 Element
    """
    if isinstance(value, list):
        out = []
        for v in value:
            out.extend(_coerce_var(v))
        return out
    if isinstance(value, Element):
        return [value]
    if isinstance(value, int):
        return [Element(i=value, s=str(value))]
    if isinstance(value, str):
        return [Element(s=value)]
    if isinstance(value, dict):
        e = Element()
        if 'i' in value: e.i = int(value['i'])
        if 's' in value: e.s = str(value['s'])
        if 'v' in value: e.v = str(value['v'])
        return [e]
    if value is None:
        return []
    raise TypeError(f"cannot coerce to Var: {value!r}")


def _populate_context(ctx: Context, context: Dict[str, Any]):
    """合成 context dict を ctx.var_map に流し込む．

    キー形式:
      "NAME"            → ctx.var_map["NAME"] = Var
      "NAME[ID]"        → ctx.var_map["NAME[ID]"] = Var
      "NAME": dict[id, value]
                        → 各 id について ctx.var_map[f"NAME[{id}]"] を設定．
                          ID は int でも str でも可．
    """
    for k, v in context.items():
        if isinstance(v, dict) and not _looks_like_element_dict(v):
            # per-id バインディング
            for sub_id, sub_val in v.items():
                ctx.var_map[f"{k}[{sub_id}]"] = _coerce_var(sub_val)
        else:
            ctx.var_map[k] = _coerce_var(v)


def _looks_like_element_dict(d: dict) -> bool:
    return any(key in d for key in ('i', 's', 'v')) and \
        all(key in ('i', 's', 'v') for key in d.keys())


def run(template_paths: List[str],
        context: Optional[Dict[str, Any]] = None,
        include_dirs: Optional[List[str]] = None,
        builtins: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, str]:
    """指定された .tf テンプレート群を評価する．

    template_paths: 入力テンプレートファイル (順次読まれ連結評価される)
    context: 変数 binding (キー: 変数名 / "NAME[id]" / "NAME" + per-id dict)
    include_dirs: $INCLUDE 検索ディレクトリ
    builtins: ビルトイン関数の差し替え (省略時は tf_builtin.BUILTINS)

    戻り値: {file_name: text}．`""` キーは default 出力 (= $FILE 切替前)．
    """
    ctx = Context(builtins=builtins if builtins is not None else BUILTINS)
    if context:
        _populate_context(ctx, context)
    inc_dirs = list(include_dirs or [])
    # template が複数ある場合，順次評価する (出力バッファは共有)．
    for tpath in template_paths:
        ctx.template_path = tpath
        with open(tpath, 'r', encoding='utf-8') as f:
            src = f.read()
        # current file が含まれるディレクトリも include 検索パスに足す
        own_dir = _dirname_or_dot(tpath)
        eff_dirs = [own_dir] + inc_dirs
        try:
            preproc = preprocess(src, eff_dirs, current_file=tpath)
            segments = split_segments(preproc)
            doc = parse(segments)
            exec_document(doc, ctx)
        except DieTerminate as e:
            print(f"[tf_engine] DIE: {e}", file=ctx.stderr)
            break
    return ctx.all_outputs()


def _dirname_or_dot(path: str) -> str:
    import os
    d = os.path.dirname(path)
    return d if d else "."


def run_string(source: str,
               context: Optional[Dict[str, Any]] = None,
               include_dirs: Optional[List[str]] = None,
               builtins: Optional[Dict[str, Any]] = None,
               ) -> Dict[str, str]:
    """ソース文字列を直接評価する (主にテスト用)．"""
    ctx = Context(builtins=builtins if builtins is not None else BUILTINS)
    if context:
        _populate_context(ctx, context)
    inc_dirs = list(include_dirs or [])
    preproc = preprocess(source, inc_dirs)
    segments = split_segments(preproc)
    doc = parse(segments)
    try:
        exec_document(doc, ctx)
    except DieTerminate as e:
        print(f"[tf_engine] DIE: {e}", file=ctx.stderr)
    return ctx.all_outputs()
