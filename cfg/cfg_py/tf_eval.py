# -*- coding: utf-8 -*-
#
#  TOPPERS .tf template engine (Python port) -- evaluator
#
#  C++ macro_processor.cpp の式評価 (line 508-1037) と
#  ディレクティブ実行 (line 1308-1679) を Python に移植する．
#
#  C++ では Boost.Spirit が parse tree を作りつつ「ノードに付与した
#  semantic action」で即時評価していたが，本 Python 実装では parser が
#  AST を生成し evaluator が後段で AST を辿る．意味論は同じ．
#

import sys
from typing import Dict, List, Optional, Any

from tf_ast import (
    Document, PlainText, EvalExpr, Assign,
    IfStmt, ForeachStmt, JoinEachStmt, WhileStmt, JoinWhileStmt,
    FunctionDef, ErrorDir, WarningDir, FileDir,
    IntLit, StrLit, Ident, IndexedIdent, UnaryOp, BinOp, Call, ListExpr,
)
from tf_value import (
    Element, Var, ExprError, DieTerminate,
    to_integer, to_string, make_int, make_str, empty_var, is_truthy,
)


# ============================================================
# 実行コンテキスト
# ============================================================

class Context:
    """C++ macro_processor::context に対応．

    var_map: 全変数 (per-id 変数も "NAME[1]" のようなキーで格納)
    func_map: ユーザ定義関数 (name → FunctionDef.body)
    builtins: ビルトイン関数の dispatch table
    output_files: 出力ファイル名 → 蓄積文字列
    current_file: 現在の出力先 (default: "")  ─ "" は標準出力扱い
    error_count: $ERROR$ や fatal の発生数
    """

    def __init__(self,
                 builtins: Optional[Dict[str, Any]] = None,
                 stderr=sys.stderr):
        self.var_map: Dict[str, Var] = {}
        self.func_map: Dict[str, FunctionDef] = {}
        self.builtins: Dict[str, Any] = builtins or {}
        self.output_files: Dict[str, List[str]] = {"": []}
        self.current_file: str = ""
        self.error_count: int = 0
        self.warning_count: int = 0
        self.stderr = stderr
        self.in_function: bool = False
        self.line: int = 0
        self.template_path: str = ""

    # ---- 変数アクセス ----

    def set_var(self, name: str, value: Var):
        self.var_map[name] = value

    def set_var_indexed(self, name: str, idx_str: str, value: Var):
        self.var_map[f"{name}[{idx_str}]"] = value

    def get_var(self, name: str, default: Optional[Var] = None) -> Var:
        return self.var_map.get(name, default if default is not None else [])

    # ---- 出力 ----

    def emit(self, text: str):
        if not text:
            return
        self.output_files.setdefault(self.current_file, []).append(text)

    def get_output(self, name: str = "") -> str:
        return "".join(self.output_files.get(name, []))

    def all_outputs(self) -> Dict[str, str]:
        return {k: "".join(v) for k, v in self.output_files.items()}

    def switch_file(self, name: str):
        # C++ macro_processor::file_ (line 1659-1660) と同じく，**現在の**
        # ファイルに `\n` を append してから新しいファイルへ切替える．
        # この動作のおかげで，連続する $FILE$ 切替で前ファイルに自然に
        # 末尾改行が付く．
        self.output_files.setdefault(self.current_file, []).append("\n")
        if name not in self.output_files:
            self.output_files[name] = []
        self.current_file = name


# ============================================================
# 式評価
# ============================================================

def _index_string(idx: Var) -> str:
    """$X[expr]$ の expr を文字列化してキーにする．

    C++ 実装 (macro_processor.cpp:1161-1166): 整数値があれば 10 進文字列，
    無ければ s をそのまま使う．
    """
    if not idx:
        raise ExprError("empty index")
    e = idx[0]
    if e.i is not None:
        return str(e.i)
    return e.s


def eval_expr(node, ctx: Context) -> Var:
    if isinstance(node, IntLit):
        return [Element(i=node.value, s=node.text)]
    if isinstance(node, StrLit):
        return [Element(s=node.value)]
    if isinstance(node, Ident):
        v = ctx.var_map.get(node.name)
        if v is None:
            # C++ では "non-value" エラーになるが，IF 文の存在チェック等で
            # 空変数を許容する場面が多い．未定義変数は空 var として返す．
            return []
        return v
    if isinstance(node, IndexedIdent):
        idx = eval_expr(node.index, ctx)
        key = f"{node.name}[{_index_string(idx)}]"
        return ctx.var_map.get(key, [])
    if isinstance(node, UnaryOp):
        return _eval_unary(node, ctx)
    if isinstance(node, BinOp):
        return _eval_binop(node, ctx)
    if isinstance(node, Call):
        return _eval_call(node, ctx)
    if isinstance(node, ListExpr):
        return _eval_list(node, ctx)
    raise ExprError(f"unsupported expression node: {type(node).__name__}")


def _eval_unary(node: UnaryOp, ctx: Context) -> Var:
    v = eval_expr(node.operand, ctx)
    if node.op == '+':
        # 整数化のみ実施 (NumStr の精錬)
        n = to_integer(v)
        return make_int(n)
    if node.op == '-':
        n = to_integer(v)
        return make_int(-n)
    if node.op == '~':
        n = to_integer(v)
        return make_int(~n & 0xFFFFFFFFFFFFFFFF if n >= 0 else ~n)
    if node.op == '!':
        n = to_integer(v)
        return make_int(0 if n else 1)
    if node.op == '@':
        # 数値→文字列化．C++ では get_i して to_string したものを s に入れる．
        n = to_integer(v)
        return [Element(i=n, s=str(n))]
    raise ExprError(f"unknown unary op: {node.op}")


def _eval_binop(node: BinOp, ctx: Context) -> Var:
    op = node.op
    # 短絡評価
    if op == '&&':
        l = eval_expr(node.left, ctx)
        if not is_truthy(l):
            return make_int(0)
        r = eval_expr(node.right, ctx)
        return make_int(1 if is_truthy(r) else 0)
    if op == '||':
        l = eval_expr(node.left, ctx)
        if is_truthy(l):
            return make_int(1)
        r = eval_expr(node.right, ctx)
        return make_int(1 if is_truthy(r) else 0)
    # 残りは両辺評価
    l = eval_expr(node.left, ctx)
    r = eval_expr(node.right, ctx)
    if op == '==':
        return make_int(1 if to_integer(l) == to_integer(r) else 0)
    if op == '!=':
        return make_int(1 if to_integer(l) != to_integer(r) else 0)
    li = to_integer(l)
    ri = to_integer(r)
    if op == '+': return make_int(li + ri)
    if op == '-': return make_int(li - ri)
    if op == '*': return make_int(li * ri)
    if op == '/':
        if ri == 0:
            raise ExprError("division by zero")
        # C++ は signed なので truncate toward zero
        q = abs(li) // abs(ri)
        if (li < 0) ^ (ri < 0):
            q = -q
        return make_int(q)
    if op == '%':
        if ri == 0:
            raise ExprError("modulo by zero")
        # C++ truncate toward zero remainder と同じ符号則を再現
        q = abs(li) // abs(ri)
        if (li < 0) ^ (ri < 0):
            q = -q
        return make_int(li - q * ri)
    if op == '<':  return make_int(1 if li <  ri else 0)
    if op == '>':  return make_int(1 if li >  ri else 0)
    if op == '<=': return make_int(1 if li <= ri else 0)
    if op == '>=': return make_int(1 if li >= ri else 0)
    if op == '&':  return make_int(li & ri)
    if op == '|':  return make_int(li | ri)
    if op == '^':  return make_int(li ^ ri)
    if op == '<<':
        if ri < 0:
            raise ExprError("negative shift count")
        return make_int(li << ri)
    if op == '>>':
        if ri < 0:
            raise ExprError("negative shift count")
        return make_int(li >> ri)
    raise ExprError(f"unknown binary op: {op}")


def _eval_call(node: Call, ctx: Context) -> Var:
    # 引数を左から右に評価
    arg_vals: List[Var] = [eval_expr(a, ctx) for a in node.args]
    # ビルトイン優先
    bi = ctx.builtins.get(node.name)
    if bi is not None:
        line_info = (ctx.template_path, node.line)
        return bi(line_info, arg_vals, ctx)
    # ユーザ関数
    fn = ctx.func_map.get(node.name)
    if fn is None:
        raise ExprError(f"undefined function: {node.name}")
    return _call_user_function(node.name, fn, arg_vals, ctx, node.line)


def _eval_list(node: ListExpr, ctx: Context) -> Var:
    if node.sequence and node.start is not None:
        a = to_integer(eval_expr(node.start, ctx))
        b = to_integer(eval_expr(node.second, ctx))
        c = to_integer(eval_expr(node.end, ctx))
        d = b - a
        if d == 0:
            raise ExprError("ordered_sequence step is zero")
        out: Var = []
        v = a
        if d > 0:
            while v <= c:
                out.append(Element(i=v, s=str(v)))
                v += d
        else:
            while v >= c:
                out.append(Element(i=v, s=str(v)))
                v += d
        return out
    # 通常の {a, b, c}: 各要素を評価して連結
    out: Var = []
    for e in node.items:
        v = eval_expr(e, ctx)
        out.extend(v)
    return out


# ============================================================
# ユーザ関数呼び出し
# ============================================================

def _call_user_function(name: str, fn: FunctionDef,
                         arg_vals: List[Var], ctx: Context, line: int) -> Var:
    # ARGV/ARGC のバインド (C++ macro_processor.cpp:1078-1096)
    saved_argv: Dict[str, Var] = {}
    saved_argc = ctx.var_map.get('ARGC')
    saved_result = ctx.var_map.get('RESULT')
    saved_in_function = ctx.in_function
    try:
        ctx.in_function = True
        # ARGV[0] = 関数名, ARGV[1..N] = 引数, ARGV[N+1] = 空 sentinel
        argv_keys = []
        ctx.set_var_indexed('ARGV', '0', make_str(name))
        argv_keys.append('ARGV[0]')
        for i, a in enumerate(arg_vals, start=1):
            ctx.set_var_indexed('ARGV', str(i), a)
            argv_keys.append(f'ARGV[{i}]')
        ctx.set_var_indexed('ARGV', str(len(arg_vals) + 1), [])
        argv_keys.append(f'ARGV[{len(arg_vals)+1}]')
        ctx.set_var('ARGC', make_int(len(arg_vals) + 1))
        ctx.set_var('RESULT', [])
        # 本体実行
        exec_document(fn.body, ctx)
        result = ctx.var_map.get('RESULT', [])
        return result
    finally:
        # 後片付け
        for k in argv_keys:
            ctx.var_map.pop(k, None)
        if saved_argc is None:
            ctx.var_map.pop('ARGC', None)
        else:
            ctx.var_map['ARGC'] = saved_argc
        if saved_result is None:
            ctx.var_map.pop('RESULT', None)
        else:
            ctx.var_map['RESULT'] = saved_result
        ctx.in_function = saved_in_function


# ============================================================
# 文 (statement) の実行
# ============================================================

def exec_document(doc: Document, ctx: Context):
    for stmt in doc.children:
        exec_stmt(stmt, ctx)


def exec_stmt(stmt, ctx: Context):
    if isinstance(stmt, PlainText):
        # C++ macro_processor::plain (line 1682-1709) の挙動を再現:
        #  - 本文の \r / \n は出力に含めない (改行は $NL$ ディレクティブで生成)
        #  - `$$` は split_segments で既に `$` 1 文字に正規化されている
        # 注: 「先頭が空白なら 1 文字スキップ」(line 1688-1689) は
        #     Boost.Spirit の skip parser が既に消費した残りに対する
        #     防御コードのため，本実装では適用しない (空白を二重に消すと
        #     `$EVT.ATR$ & CALLBACK` 周りで意味が変わる)．
        text = stmt.text
        if text:
            text = text.replace('\r', '').replace('\n', '')
            ctx.emit(text)
        return
    ctx.line = getattr(stmt, 'line', ctx.line)
    if isinstance(stmt, EvalExpr):
        v = eval_expr(stmt.expr, ctx)
        ctx.emit(to_string(v))
        return
    if isinstance(stmt, Assign):
        v = eval_expr(stmt.value, ctx)
        if stmt.target_index is None:
            ctx.set_var(stmt.target_name, v)
        else:
            idx = eval_expr(stmt.target_index, ctx)
            ctx.set_var_indexed(stmt.target_name, _index_string(idx), v)
        return
    if isinstance(stmt, IfStmt):
        for cond, body in stmt.cases:
            cv = eval_expr(cond, ctx)
            if is_truthy(cv):
                exec_document(body, ctx)
                return
        if stmt.else_body is not None:
            exec_document(stmt.else_body, ctx)
        return
    if isinstance(stmt, ForeachStmt):
        lst = eval_expr(stmt.list_expr, ctx)
        for el in lst:
            ctx.set_var(stmt.var_name, [el])
            exec_document(stmt.body, ctx)
        return
    if isinstance(stmt, JoinEachStmt):
        lst = eval_expr(stmt.list_expr, ctx)
        delim = to_string(eval_expr(stmt.delim_expr, ctx))
        first = True
        for el in lst:
            if not first:
                ctx.emit(delim)
            first = False
            ctx.set_var(stmt.var_name, [el])
            exec_document(stmt.body, ctx)
        return
    if isinstance(stmt, WhileStmt):
        # 暴走防止: 1e7 回でアサート
        budget = 10_000_000
        while is_truthy(eval_expr(stmt.cond, ctx)):
            exec_document(stmt.body, ctx)
            budget -= 1
            if budget <= 0:
                raise ExprError("$WHILE budget exceeded (possible infinite loop)")
        return
    if isinstance(stmt, JoinWhileStmt):
        budget = 10_000_000
        first = True
        while is_truthy(eval_expr(stmt.cond, ctx)):
            if not first:
                ctx.emit(to_string(eval_expr(stmt.delim_expr, ctx)))
            first = False
            exec_document(stmt.body, ctx)
            budget -= 1
            if budget <= 0:
                raise ExprError("$JOINWHILE budget exceeded")
        return
    if isinstance(stmt, FunctionDef):
        if ctx.in_function:
            raise ExprError(f"$FUNCTION cannot be nested (line {stmt.line})")
        ctx.func_map[stmt.name] = stmt
        return
    if isinstance(stmt, ErrorDir):
        _emit_diag(stmt, ctx, is_error=True)
        return
    if isinstance(stmt, WarningDir):
        _emit_diag(stmt, ctx, is_error=False)
        return
    if isinstance(stmt, FileDir):
        ctx.switch_file(stmt.path)
        return
    raise ExprError(f"unsupported stmt node: {type(stmt).__name__}")


def _emit_diag(stmt, ctx: Context, *, is_error: bool):
    # C++ 仕様: target_file を一時的に stderr へ振り替えて body を実行する．
    # arg があればそれを場所表記として先頭に出す (例: line=1 → "1: ...")．
    saved_file = ctx.current_file
    DIAG_FILE = "<stderr>"
    if DIAG_FILE not in ctx.output_files:
        ctx.output_files[DIAG_FILE] = []
    ctx.current_file = DIAG_FILE
    try:
        prefix = "error: " if is_error else "warning: "
        ctx.emit(prefix)
        if stmt.arg is not None:
            arg_v = eval_expr(stmt.arg, ctx)
            ctx.emit(f"line {to_string(arg_v)}: ")
        exec_document(stmt.body, ctx)
        ctx.emit("\n")
    finally:
        ctx.current_file = saved_file
    # stderr バッファに溜めた分を実際の stderr へも吐く
    msg = "".join(ctx.output_files[DIAG_FILE])
    if msg:
        print(msg, end="", file=ctx.stderr)
        ctx.output_files[DIAG_FILE] = []
    if is_error:
        ctx.error_count += 1
    else:
        ctx.warning_count += 1
