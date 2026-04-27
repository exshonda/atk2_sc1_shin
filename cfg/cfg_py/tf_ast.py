# -*- coding: utf-8 -*-
#
#  TOPPERS .tf template engine (Python port) -- AST nodes
#
#  C++ macro_processor.cpp:174-447 の Boost.Spirit 文法に直結する形で
#  AST ノードを dataclass で定義する．
#

from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple


# ----- 式 (Expr) -----

@dataclass
class IntLit:
    value: int
    text: str  # 元ソースの表記 (例: "0x10")
    line: int = 0


@dataclass
class StrLit:
    value: str  # エスケープ展開済み
    line: int = 0


@dataclass
class Ident:
    name: str
    line: int = 0


@dataclass
class IndexedIdent:
    name: str
    index: Any  # Expr
    line: int = 0


@dataclass
class UnaryOp:
    op: str  # '-' '+' '~' '!' '@'
    operand: Any  # Expr
    line: int = 0


@dataclass
class BinOp:
    op: str  # '+' '-' '*' '/' '%' '<' '>' ... '&&' '||'
    left: Any  # Expr
    right: Any  # Expr
    line: int = 0


@dataclass
class Call:
    name: str
    args: List[Any]  # list[Expr]
    line: int = 0


@dataclass
class ListExpr:
    """`{a, b, c}` の通常形式と，`{a, b, ..., c}` の等差数列形式を兼ねる．

    sequence=True なら start/second/end が埋まる．それ以外は items のみ．
    `;` で区切られた複数のグループも items にぶら下げる (フラット化)．
    """
    items: List[Any]  # list[Expr]
    sequence: bool = False
    start: Optional[Any] = None
    second: Optional[Any] = None
    end: Optional[Any] = None
    line: int = 0


@dataclass
class Assign:
    """`$X = e$` または `$X[i] = e$` の代入式．

    Boost.Spirit 文法では assignment_expr は expr と同じ位置に出てくるが，
    ここでは Stmt として扱う．`$X = e$` の評価値は代入された var_t そのもの
    だが，statement 形式で使われる際は出力に反映しない．
    """
    target_name: str
    target_index: Optional[Any]  # Expr or None (None なら普通の代入)
    value: Any  # Expr
    line: int = 0


# ----- 文 (Stmt) -----
#
# Stmt = PlainText | EvalExpr | Assign (上で定義)
#      | If | Foreach | JoinEach | While | JoinWhile
#      | FunctionDef | ErrorDir | WarningDir | FileDir
# Document は Stmt のリスト

@dataclass
class PlainText:
    text: str
    line: int = 0


@dataclass
class EvalExpr:
    """`$expr$` 評価結果を出力に追加する文．"""
    expr: Any  # Expr
    line: int = 0


@dataclass
class IfStmt:
    """`$IF e$ ... ($ELIF e$ ...)* ($ELSE$ ...)? $END$`"""
    cases: List[Tuple[Any, "Document"]]  # (cond_expr, body)
    else_body: Optional["Document"] = None
    line: int = 0


@dataclass
class ForeachStmt:
    var_name: str
    list_expr: Any  # Expr
    body: "Document"
    line: int = 0


@dataclass
class JoinEachStmt:
    var_name: str
    list_expr: Any  # Expr
    delim_expr: Any  # Expr
    body: "Document"
    line: int = 0


@dataclass
class WhileStmt:
    cond: Any  # Expr
    body: "Document"
    line: int = 0


@dataclass
class JoinWhileStmt:
    cond: Any  # Expr
    delim_expr: Any  # Expr
    body: "Document"
    line: int = 0


@dataclass
class FunctionDef:
    name: str
    body: "Document"
    line: int = 0


@dataclass
class ErrorDir:
    """`$ERROR$ ... $END$` または `$ERROR e$ ... $END$`"""
    arg: Optional[Any]  # Expr (場所表記用) or None
    body: "Document"
    line: int = 0


@dataclass
class WarningDir:
    arg: Optional[Any]  # Expr or None
    body: "Document"
    line: int = 0


@dataclass
class FileDir:
    """`$FILE "path"$`"""
    path: str  # string_literal はパース時に文字列確定
    line: int = 0


@dataclass
class Document:
    children: List[Any] = field(default_factory=list)


# 区切り用センチネル．パーサが top を「次の閉じタグまで」消費するときに
# 期待する閉じトークンを表す内部値．
END_KEYWORDS = ("END", "ELIF", "ELSEIF", "ELSE")
