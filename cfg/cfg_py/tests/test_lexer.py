# -*- coding: utf-8 -*-
import os
import textwrap

from tf_lexer import (
    remove_comment, expand_include, preprocess,
    split_segments, tokenize_directive,
)


def test_remove_comment_full_dollar_lines_become_blank():
    src = "$ comment 1\n$    comment 2\nreal\n"
    out = remove_comment(src)
    # C++ remove_comment: コメント行は \n のみ出力 (本文は捨てる)
    assert out == "\n\nreal\n"


def test_remove_comment_strips_leading_whitespace():
    # 非コメント行は行頭の空白を除去する (C++ 動作)
    src = "    indented\n\tline\n"
    out = remove_comment(src)
    assert out == "indented\nline\n"


def test_remove_comment_inline_dollar_hash():
    # 中行 $# 以降を削除する．C++ 仕様では改行も付けない
    src = "real $# comment\nx = 1 $#also\n"
    out = remove_comment(src)
    assert out == "real x = 1 "


def test_remove_comment_keeps_dollar_directive():
    src = "$INCLUDE \"foo.tf\"$\n$X = 1$\n"
    out = remove_comment(src)
    assert out == src


def test_split_segments_plain_only():
    out = split_segments("hello world\n")
    assert len(out) == 1
    assert out[0].kind == 'PLAIN'
    assert out[0].text == "hello world\n"


def test_split_segments_dollar_dollar_escape():
    out = split_segments("a$$b$$c")
    assert len(out) == 1
    assert out[0].kind == 'PLAIN'
    assert out[0].text == "a$b$c"


def test_split_segments_directive():
    out = split_segments("hello $X$ world")
    assert [s.kind for s in out] == ['PLAIN', 'DIR', 'PLAIN']
    assert out[0].text == "hello "
    assert out[1].text == "X"
    assert out[2].text == " world"


def test_split_segments_string_with_dollar_inside():
    # $...$ の中の "..." 内の `$` は終端と見なさない
    out = split_segments('$X = "ab$cd" + "ef"$')
    assert len(out) == 1
    assert out[0].kind == 'DIR'
    assert out[0].text == 'X = "ab$cd" + "ef"'


def test_tokenize_directive_basic():
    toks = tokenize_directive('IF X >= 10', base_line=1)
    kinds = [t.kind for t in toks]
    vals = [t.value for t in toks]
    assert kinds == ['IDENT', 'IDENT', 'OP', 'NUM']
    assert vals == ['IF', 'X', '>=', 10]


def test_tokenize_directive_string_escape():
    toks = tokenize_directive(r'TRACE("a\nb")', base_line=1)
    assert toks[0].kind == 'IDENT' and toks[0].value == 'TRACE'
    assert toks[1].kind == 'OP' and toks[1].value == '('
    assert toks[2].kind == 'STR' and toks[2].value == "a\nb"
    assert toks[3].kind == 'OP' and toks[3].value == ')'


def test_tokenize_directive_hex_oct():
    toks = tokenize_directive('A = 0x10 + 010 + 8', base_line=1)
    nums = [t.value for t in toks if t.kind == 'NUM']
    assert nums == [16, 8, 8]


def test_expand_include(tmp_path):
    inc = tmp_path / "inc.tf"
    inc.write_text('inner-content\n', encoding='utf-8')
    src = '$INCLUDE "inc.tf"$\nouter\n'
    out = expand_include(src, [str(tmp_path)])
    assert out == 'inner-content\n\nouter\n'


def test_preprocess_combines(tmp_path):
    inc = tmp_path / "inc.tf"
    inc.write_text("$ comment in include\nINNER\n", encoding='utf-8')
    src = '$ outer comment\n$INCLUDE "inc.tf"$\nOUTER\n'
    out = preprocess(src, [str(tmp_path)])
    # outer comment 除去 → INCLUDE 展開時に inc.tf も remove_comment される
    assert "comment" not in out
    assert "INNER" in out
    assert "OUTER" in out
