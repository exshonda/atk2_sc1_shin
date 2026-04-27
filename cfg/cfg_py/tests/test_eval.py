# -*- coding: utf-8 -*-
import pytest

from tf_engine import run_string


def out(text, ctx=None):
    """run_string で評価して default 出力を返すヘルパ．"""
    return run_string(text, context=ctx).get("", "")


# ----- 平文 / $$ -----

def test_plain_passthrough():
    # C++ macro_processor::plain は plain text 中の `\r` `\n` を捨てるため，
    # 出力には改行は含まれない (改行は $NL$ ディレクティブで生成する)．
    assert out("hello world\n") == "hello world"


def test_dollar_dollar_escape():
    assert out("$$ a $$ b\n") == "$ a $ b"


# ----- 式評価 -----

def test_eval_int_literal():
    assert out("$1 + 2$") == "3"


def test_eval_hex_oct():
    assert out("$0x10 + 010$") == "24"  # 16 + 8


def test_eval_string_literal():
    assert out(r'$"foo bar"$') == "foo bar"


def test_eval_unary_at_int_to_str():
    # @ は数値を文字列化する単項
    assert out("$@(1+2)$") == "3"


def test_eval_var_lookup():
    assert out("$X$", ctx={"X": 42}) == "42"
    assert out("$X$", ctx={"X": "hello"}) == "hello"


def test_eval_indexed_var():
    # NAME[1] → "TskA"
    assert out("$TSK[1]$", ctx={"TSK[1]": "TskA"}) == "TskA"


def test_eval_per_id_via_dict_form():
    # context に dict を渡すと per-id バインディングになる
    ctx = {"TSK": {1: "TskA", 2: "TskB"}}
    assert out("$TSK[1]$/$TSK[2]$", ctx=ctx) == "TskA/TskB"


# ----- 算術 -----

@pytest.mark.parametrize("expr,want", [
    ("$1 + 2 * 3$", "7"),
    ("$(1+2) * 3$", "9"),
    ("$10 / 3$", "3"),
    ("$10 % 3$", "1"),
    ("$-5 / 2$", "-2"),
    ("$-5 % 2$", "-1"),
    ("$1 << 4$", "16"),
    ("$0xFF >> 4$", "15"),
    ("$5 & 3$", "1"),
    ("$5 | 3$", "7"),
    ("$5 ^ 3$", "6"),
])
def test_arith_ops(expr, want):
    assert out(expr) == want


@pytest.mark.parametrize("expr,want", [
    ("$1 < 2$", "1"),
    ("$2 < 1$", "0"),
    ("$2 == 2$", "1"),
    ("$2 != 2$", "0"),
    ("$1 && 1$", "1"),
    ("$1 && 0$", "0"),
    ("$0 || 1$", "1"),
    ("$!0$", "1"),
    ("$!1$", "0"),
])
def test_relational_logical(expr, want):
    assert out(expr) == want


# ----- 代入 -----

def test_assign_simple():
    src = "$X = 5$$X$"
    assert out(src) == "5"


def test_assign_indexed():
    src = "$T[1] = 100$$T[1]$"
    assert out(src) == "100"


# ----- IF -----

def test_if_then():
    src = "$IF 1$YES$END$"
    assert out(src) == "YES"


def test_if_else():
    src = "$IF 0$YES$ELSE$NO$END$"
    assert out(src) == "NO"


def test_if_elif_chain():
    src = "$IF 0$A$ELIF 1$B$ELIF 1$C$ELSE$D$END$"
    assert out(src) == "B"


def test_if_with_var():
    src = "$IF X == 1$ONE$ELSE$NOT$END$"
    assert out(src, ctx={"X": 1}) == "ONE"
    assert out(src, ctx={"X": 2}) == "NOT"


# ----- FOREACH / JOINEACH -----

def test_foreach_list_literal():
    src = "$FOREACH x {1, 2, 3}$$x$,$END$"
    assert out(src) == "1,2,3,"


def test_foreach_var():
    src = "$FOREACH x L$$x$;$END$"
    assert out(src, ctx={"L": [1, 2, 3]}) == "1;2;3;"


def test_joineach():
    src = "$JOINEACH x {1, 2, 3} \"-\"$$x$$END$"
    assert out(src) == "1-2-3"


def test_foreach_range_via_builtin():
    src = "$FOREACH i RANGE(1, 4)$$i$$END$"
    assert out(src) == "1234"


# ----- WHILE -----

def test_while_loop():
    src = "$i = 0$$WHILE i < 3$$i$,$i = i + 1$$END$"
    assert out(src) == "0,1,2,"


# ----- ユーザ関数 -----

def test_user_function_simple():
    src = (
        "$FUNCTION ADD$\n"
        "  $RESULT = ARGV[1] + ARGV[2]$\n"
        "$END$\n"
        "$ADD(3, 4)$"
    )
    assert "7" in out(src)


def test_user_function_recursive_arg_isolation():
    src = (
        "$FUNCTION INC$\n"
        "  $RESULT = ARGV[1] + 1$\n"
        "$END$\n"
        "$INC(INC(5))$"
    )
    assert "7" in out(src)


# ----- ビルトイン -----

def test_builtin_eq():
    assert out("$EQ(\"a\",\"a\")$") == "1"
    assert out("$EQ(\"a\",\"b\")$") == "0"


def test_builtin_alt():
    assert out("$ALT(X, \"def\")$", ctx={"X": ""}) == "def" or \
           out("$ALT(X, \"def\")$", ctx={"X": ""}) == ""  # X="" のとき空 var なら def
    assert out("$ALT(X, \"def\")$", ctx={"X": "set"}) == "set"


def test_builtin_length():
    assert out("$LENGTH({1,2,3})$") == "3"
    assert out("$LENGTH({})$") == "0"


def test_builtin_at():
    assert out("$AT({10,20,30}, 1)$") == "20"


def test_builtin_format_position():
    assert out('$FORMAT("%1%/%2%", 3, "x")$') == "3/x"


def test_builtin_format_printf():
    assert out('$FORMAT("0x%x", 255)$') == "0xff"
    assert out('$FORMAT("%d", -7)$') == "-7"
    assert out('$FORMAT("%05d", 42)$') == "00042"


def test_builtin_concat():
    assert out('$CONCAT("a", "b")$') == "ab"


def test_builtin_value():
    # VALUE("name", 5) → Element(s="name", i=5) ; default to_string は s 優先
    assert out('$VALUE("foo", 5)$') == "foo"
    assert out('$+VALUE("foo", 5)$') == "5"  # +X で int 取り出し


def test_builtin_range():
    assert out("$LENGTH(RANGE(0,4))$") == "5"


def test_builtin_isfunction():
    # $FUNCTION$ ディレクティブの末尾改行は出力に残る (C++ も同様の挙動).
    src = (
        "$FUNCTION FOO$\n  $RESULT = 1$\n$END$"
        "$ISFUNCTION(\"FOO\")$/$ISFUNCTION(\"BAR\")$"
    )
    assert out(src) == "1/0"


# ----- $FILE 切替 -----

def test_file_switch():
    # C++ macro_processor::file_ (line 1659) は切替時に旧ファイルへ \n を
    # append する仕様．本実装も同じ動作にしている．
    src = "default$FILE \"a.txt\"$ABC$FILE \"b.txt\"$XYZ"
    res = run_string(src)
    assert res.get("") == "default\n"
    assert res.get("a.txt") == "ABC\n"
    assert res.get("b.txt") == "XYZ"
