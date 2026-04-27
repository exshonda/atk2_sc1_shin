# -*- coding: utf-8 -*-
#
#  TOPPERS .tf template engine (Python port) -- value model
#
#  C++ macro_processor.hpp の element / var_t を Python の dataclass に
#  そのまま移植する．数値情報は int (64bit 相当) で保持する．
#

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Element:
    """C++ macro_processor::element の対応物．

    i: 数値情報 (None なら未設定)
    s: 文字列情報
    v: 中間値 (現状ほぼ未使用だが C++ 側にあるので残す)
    """
    i: Optional[int] = None
    s: str = ""
    v: str = ""


# Var は単に list[Element]．C++ の var_t (= std::vector<element>) を Python list で表現．
Var = List[Element]


class ExprError(Exception):
    """式評価中の型エラー (C++ macro_processor の expr_error 相当)．"""


class DieTerminate(Exception):
    """`$DIE()$` などで処理を即時打ち切るための例外．

    C++ macro_processor::die_terminate に対応．
    """


def to_integer(var: Var, where: str = "") -> int:
    """var_t → int64．先頭要素の i を返す．

    要素が無い，または数値情報が無い場合は ExprError．
    where はエラーメッセージ用の場所表記 (任意)．
    """
    if not var:
        raise ExprError(f"non-value is referred ({where})" if where
                        else "non-value is referred")
    e = var[0]
    if e.i is None:
        # 文字列だけが入っている場合: 数値解釈は出来ないのでエラー
        raise ExprError(
            f"`{e.s}' cannot be converted to integer" if not where
            else f"`{e.s}' cannot be converted to integer ({where})"
        )
    return int(e.i)


def to_string(var: Var, where: str = "") -> str:
    """var_t → string．

    C++ macro_processor::to_string の挙動に合わせる:
      - 空 var → ""
      - 各要素について s が非空なら s，さもなくば i を 10 進文字列化
      - 複数要素はカンマで連結
    """
    if not var:
        return ""
    parts = []
    for e in var:
        if e.s != "":
            parts.append(e.s)
        elif e.i is not None:
            parts.append(str(e.i))
        else:
            parts.append("")
    return ",".join(parts)


def make_int(value: int, s: Optional[str] = None) -> Var:
    """int から 1 要素 Var を作るヘルパ．"""
    return [Element(i=int(value), s=s if s is not None else str(value))]


def make_str(value: str) -> Var:
    """文字列から 1 要素 Var を作るヘルパ．"""
    return [Element(s=value)]


def empty_var() -> Var:
    return []


def is_truthy(var: Var) -> bool:
    """`$IF expr$` などで真偽判定するときの基準．

    C++ では `get_i(var) != 0` で判定．数値情報が無ければエラー．
    """
    return to_integer(var) != 0
