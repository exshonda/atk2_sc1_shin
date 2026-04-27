# -*- coding: utf-8 -*-
#
#  TOPPERS .tf template engine (Python port) -- preprocessor + tokenizer
#
#  3 段階処理:
#    1. preprocess(text)   ← コメント除去 + $INCLUDE 展開
#    2. split_segments     ← 平文 / $...$ ディレクティブの 2 分割ストリーム
#    3. tokenize_directive ← $...$ 内部のトークン化 (識別子, 整数, 文字列, ...)
#
#  C++ macro_processor.cpp の preprocess (line 2086-2089), remove_comment
#  (line 1981-2007), expand_include (line 2010-2050) と
#  Boost.Spirit 文法 (line 240-405) に対応．
#

import os
import re
from dataclasses import dataclass
from typing import Iterator, List, Optional


# ============================================================
# 1. プリプロセッサ
# ============================================================

# 行頭が `$ ` または `$<TAB>` または `$` のみで終わる行はコメント．
# 中行の `$#` 以降もコメント．
_LINE_COMMENT_FULL = re.compile(r'^[ \t]*\$([ \t#].*)?$')
_INLINE_COMMENT = re.compile(r'\$#.*$')

# `$INCLUDE "filename"$` (前後に余計な空白・タブを許容)
# 行ごとにヒットさせて行単位で置換する．
_INCLUDE_DIRECTIVE = re.compile(
    r'\$INCLUDE[ \t\r\n]+"([^"]+)"[ \t\r\n]*\$'
)


def remove_comment(src: str) -> str:
    """C++ macro_processor::remove_comment(line 1981-2007) と同等．

    3 ケースを区別する:
      1. `$` のみ または `$<空白>...EOL`  → 出力は `\n` のみ (本文は捨てる)
      2. 中行に `$#` を含む                → `$#` 以前を出力 (改行は付けない)
      3. それ以外                          → 行頭の空白を除去して `行 + \n` 出力
    """
    out: List[str] = []
    n = len(src)
    i = 0
    while i < n:
        # 1 行を切り出す (改行を含めない)
        j = src.find('\n', i)
        if j == -1:
            line = src[i:]
            i = n
            has_eol = False
        else:
            line = src[i:j]
            i = j + 1
            has_eol = True
        # 末尾 CR を判定用に剥がす
        had_cr = line.endswith('\r')
        bare = line[:-1] if had_cr else line

        if (len(bare) >= 2 and bare[0] == '$' and bare[1] in (' ', '\t', '\r')) \
                or (len(bare) == 1 and bare[0] == '$'):
            # case 1: コメント行 → \n のみ出力
            if has_eol:
                out.append('\n')
            continue
        # case 2: $# 以降をカット (改行は付与しない)
        idx = bare.find('$#')
        if idx >= 0:
            out.append(bare[:idx])
            # has_eol を消費するが，C++ コードは \n を付与しない
            continue
        # case 3: 行頭の空白を除去
        stripped = bare.lstrip(' \t\r')
        out.append(stripped)
        if has_eol:
            out.append('\n')
    return ''.join(out)


def expand_include(src: str, include_dirs: List[str],
                   seen: Optional[set] = None,
                   current_file: Optional[str] = None) -> str:
    """`$INCLUDE "filename"$` を再帰的に展開する．

    - filename は include_dirs から検索される．
    - 含めた先のファイルにも remove_comment + expand_include を適用．
    - 同じファイルを 2 回以上含めてもループしないよう seen で抑止．
    """
    if seen is None:
        seen = set()

    def _replace(match):
        fname = match.group(1)
        path = _find_include(fname, include_dirs)
        if path is None:
            raise FileNotFoundError(
                f"$INCLUDE not found: '{fname}'"
                + (f" (referenced from {current_file})" if current_file else "")
            )
        abspath = os.path.normcase(os.path.abspath(path))
        if abspath in seen:
            # 二重インクルードはノーオペにする (kernel.tf 等で fallthrough する)
            return ''
        seen.add(abspath)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 再帰: コメント除去 → 自身の INCLUDE 展開
        content = remove_comment(content)
        content = expand_include(content, include_dirs, seen, current_file=path)
        return content

    # 最大 64 回まで substitution を回す (再帰インクルードの確実な吸収)．
    for _ in range(64):
        new_src, n = _INCLUDE_DIRECTIVE.subn(_replace, src)
        if n == 0:
            return new_src
        src = new_src
    return src  # まだ残っていても諦め (Diagnose: 循環の可能性)


def _find_include(fname: str, include_dirs: List[str]) -> Optional[str]:
    """include_dirs から fname を探す．存在しなければ None．"""
    if os.path.isabs(fname) and os.path.exists(fname):
        return fname
    for d in include_dirs:
        cand = os.path.join(d, fname)
        if os.path.exists(cand):
            return cand
    # 最後にカレントを試す
    if os.path.exists(fname):
        return fname
    return None


def preprocess(src: str, include_dirs: List[str],
               current_file: Optional[str] = None) -> str:
    """C++ macro_processor::preprocess に対応．

    順序: remove_comment → expand_include．
    """
    seen = set()
    if current_file:
        seen.add(os.path.normcase(os.path.abspath(current_file)))
    src = remove_comment(src)
    src = expand_include(src, include_dirs, seen, current_file=current_file)
    return src


# ============================================================
# 2. 平文 / ディレクティブ の分離
# ============================================================

@dataclass
class Segment:
    """ソース上の 1 セグメント．

    kind == 'PLAIN'  : text は平文 (生のまま)
    kind == 'DIR'    : text は $...$ の中身 (両端の $ を含まない)
    """
    kind: str
    text: str
    line: int  # 開始行 (1-origin)


def split_segments(src: str) -> List[Segment]:
    """src を Segment のリストに分解する．

    平文中の `$$` は `$` リテラルに復元して PLAIN に含める．
    `$...$` の中身は 1 つの DIR セグメントとして取り出す．
    DIR の中の文字列リテラル `"..."` 内の `$` は終端と扱わない．
    """
    segments: List[Segment] = []
    i = 0
    n = len(src)
    line = 1
    plain_buf: List[str] = []
    plain_start_line = 1

    def _flush_plain(end_line: int):
        if plain_buf:
            segments.append(Segment('PLAIN', ''.join(plain_buf), plain_start_line))
            plain_buf.clear()

    while i < n:
        ch = src[i]
        if ch == '\n':
            plain_buf.append(ch)
            line += 1
            i += 1
            continue
        if ch != '$':
            plain_buf.append(ch)
            i += 1
            continue
        # `$` を見た．次が `$` なら escape．それ以外なら DIR 開始．
        if i + 1 < n and src[i + 1] == '$':
            plain_buf.append('$')
            i += 2
            continue
        # DIR 開始
        _flush_plain(line)
        plain_start_line = line  # 次の PLAIN の起点を仮確定
        dir_start_line = line
        i += 1  # opening `$` を消費
        # 中身を読む．`"..."` 内の `$` は通過させる．
        buf: List[str] = []
        in_string = False
        while i < n:
            c = src[i]
            if in_string:
                if c == '\\' and i + 1 < n:
                    # エスケープ: \X はそのまま 2 文字残す
                    buf.append(c)
                    buf.append(src[i + 1])
                    if src[i + 1] == '\n':
                        line += 1
                    i += 2
                    continue
                if c == '"':
                    in_string = False
                    buf.append(c)
                    i += 1
                    continue
                if c == '\n':
                    line += 1
                buf.append(c)
                i += 1
                continue
            # in_string == False
            if c == '"':
                in_string = True
                buf.append(c)
                i += 1
                continue
            if c == '$':
                # 閉じ
                segments.append(Segment('DIR', ''.join(buf), dir_start_line))
                i += 1
                plain_start_line = line
                break
            if c == '\n':
                line += 1
            buf.append(c)
            i += 1
        else:
            # ソース末端まで来てしまった (閉じ `$` が無い)
            raise SyntaxError(
                f"unterminated $...$ directive starting at line {dir_start_line}"
            )
    _flush_plain(line)
    return segments


# ============================================================
# 3. ディレクティブ内部のトークン化
# ============================================================
#
# 型: ('NAME', value, col) のタプル．value は文字列 (NUM は int, STR は
# unescape 後の文字列)．col はディレクティブ先頭からのバイト位置．


# 識別子: [A-Za-z_][A-Za-z_0-9.]*
_RE_IDENT = re.compile(r'[A-Za-z_][A-Za-z_0-9\.]*')
# 整数: 0x... / 0... (8進) / 10進
_RE_NUM_HEX = re.compile(r'0[xX][0-9a-fA-F]+')
_RE_NUM_OCT = re.compile(r'0[0-7]+')
_RE_NUM_DEC = re.compile(r'[0-9]+')
# 演算子 (長いものから優先)
_OPS = (
    "<<", ">>", "<=", ">=", "==", "!=", "&&", "||",
    "...",
    "(", ")", "[", "]", "{", "}",
    ",", ";", "=",
    "+", "-", "*", "/", "%",
    "<", ">", "&", "|", "^", "~", "!", "@",
)


@dataclass
class Tok:
    kind: str  # 'IDENT' 'NUM' 'STR' 'OP'
    value: object  # str / int / str
    line: int  # ソース上の行 (segment.line に相対加算済)


def _unescape_c_string(raw: str) -> str:
    """C 風エスケープ展開．`\\n` `\\t` `\\"` `\\\\` `\\xHH` `\\NNN` をサポート．"""
    out: List[str] = []
    i = 0
    n = len(raw)
    while i < n:
        c = raw[i]
        if c == '\\' and i + 1 < n:
            nxt = raw[i + 1]
            if nxt in ('n', 'N'): out.append('\n'); i += 2
            elif nxt in ('t', 'T'): out.append('\t'); i += 2
            elif nxt in ('r', 'R'): out.append('\r'); i += 2
            elif nxt in ('a', 'A'): out.append('\a'); i += 2
            elif nxt in ('b', 'B'): out.append('\b'); i += 2
            elif nxt in ('f', 'F'): out.append('\f'); i += 2
            elif nxt in ('v', 'V'): out.append('\v'); i += 2
            elif nxt == '0': out.append('\0'); i += 2
            elif nxt == '\\': out.append('\\'); i += 2
            elif nxt == '"': out.append('"'); i += 2
            elif nxt == "'": out.append("'"); i += 2
            elif nxt in ('x', 'X'):
                m = re.match(r'[0-9a-fA-F]{1,2}', raw[i + 2:])
                if m:
                    out.append(chr(int(m.group(), 16)))
                    i += 2 + len(m.group())
                else:
                    out.append(nxt); i += 2
            else:
                out.append(nxt); i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def tokenize_directive(text: str, base_line: int = 1) -> List[Tok]:
    """`$...$` の中身を Tok のリストに分解する．"""
    toks: List[Tok] = []
    i = 0
    n = len(text)
    line = base_line
    while i < n:
        c = text[i]
        # 空白／改行スキップ
        if c == '\n':
            line += 1
            i += 1
            continue
        if c in ' \t\r':
            i += 1
            continue
        # 文字列リテラル
        if c == '"':
            j = i + 1
            while j < n:
                cj = text[j]
                if cj == '\\' and j + 1 < n:
                    if text[j + 1] == '\n':
                        line += 1
                    j += 2
                    continue
                if cj == '"':
                    break
                if cj == '\n':
                    line += 1
                j += 1
            else:
                raise SyntaxError(
                    f"unterminated string literal at line {line}"
                )
            raw = text[i + 1:j]
            toks.append(Tok('STR', _unescape_c_string(raw), line))
            i = j + 1
            continue
        # 数値
        if c.isdigit():
            m = _RE_NUM_HEX.match(text, i) \
                or _RE_NUM_OCT.match(text, i) \
                or _RE_NUM_DEC.match(text, i)
            if m:
                lit = m.group()
                if lit.startswith(('0x', '0X')):
                    val = int(lit, 16)
                elif lit.startswith('0') and len(lit) > 1 and all(ch in '01234567' for ch in lit[1:]):
                    val = int(lit, 8)
                else:
                    val = int(lit, 10)
                toks.append(Tok('NUM', val, line))
                i = m.end()
                continue
        # 識別子
        if c.isalpha() or c == '_':
            m = _RE_IDENT.match(text, i)
            if m:
                toks.append(Tok('IDENT', m.group(), line))
                i = m.end()
                continue
        # 演算子
        matched = False
        for op in _OPS:
            if text.startswith(op, i):
                toks.append(Tok('OP', op, line))
                i += len(op)
                matched = True
                break
        if matched:
            continue
        raise SyntaxError(
            f"unexpected character {c!r} at line {line}"
        )
    return toks
