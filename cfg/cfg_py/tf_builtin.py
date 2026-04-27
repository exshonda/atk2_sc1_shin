# -*- coding: utf-8 -*-
#
#  TOPPERS .tf template engine (Python port) -- builtin functions
#
#  C++ builtin_function.cpp の Python ポート．
#  ATK2 で実使用される頻度順に: FORMAT > TRACE > LENGTH > DIE > EQ > ALT > VALUE
#  追加で APPEND / AT / CONCAT / FIND / ATOI / RANGE / ENVIRON /
#  LSORT / ESCSTR / ISFUNCTION / CALL / NOOP / GETTEXT / _ も実装．
#

import os
import re
import sys
from typing import Callable, Dict, List

from tf_value import (
    Element, Var, ExprError, DieTerminate,
    to_integer, to_string, make_int, make_str, empty_var,
)


# ----- ヘルパ -----

def _check_arity(line_info, name, expected, got):
    if got != expected:
        raise ExprError(
            f"`{name}' expects {expected} args, got {got}"
            f" at {line_info[0]}:{line_info[1]}"
        )


def _check_arity_min(line_info, name, minimum, got):
    if got < minimum:
        raise ExprError(
            f"`{name}' expects at least {minimum} args, got {got}"
            f" at {line_info[0]}:{line_info[1]}"
        )


# ============================================================
# 比較系
# ============================================================

def _bi_eq(line_info, args, ctx) -> Var:
    """EQ(a, b) → 1 if to_string(a) == to_string(b) else 0."""
    _check_arity(line_info, 'EQ', 2, len(args))
    return make_int(1 if to_string(args[0]) == to_string(args[1]) else 0)


def _bi_alt(line_info, args, ctx) -> Var:
    """ALT(a, b) → a if a is non-empty else b."""
    _check_arity(line_info, 'ALT', 2, len(args))
    return args[0] if args[0] else args[1]


# ============================================================
# 算術 / 数値
# ============================================================

def _bi_atoi(line_info, args, ctx) -> Var:
    """ATOI(string [, radix]) → int (radix 既定 10, 0 なら自動判定)．"""
    if len(args) not in (1, 2):
        raise ExprError(f"`ATOI' expects 1 or 2 args at {line_info[0]}:{line_info[1]}")
    s = to_string(args[0]).strip()
    radix = 10
    if len(args) == 2:
        radix = to_integer(args[1])
    if radix == 0:
        # 0x..., 0..., 10進 を自動
        if s.lower().startswith('0x'):
            return make_int(int(s, 16))
        if s.startswith('0') and len(s) > 1 and all(c in '01234567' for c in s[1:]):
            return make_int(int(s, 8))
        return make_int(int(s, 10))
    return make_int(int(s, radix))


def _bi_range(line_info, args, ctx) -> Var:
    """RANGE(min, max) → {min, min+1, ..., max} (inclusive)．"""
    _check_arity(line_info, 'RANGE', 2, len(args))
    a = to_integer(args[0])
    b = to_integer(args[1])
    out: Var = []
    if a <= b:
        for i in range(a, b + 1):
            out.append(Element(i=i, s=str(i)))
    else:
        for i in range(a, b - 1, -1):
            out.append(Element(i=i, s=str(i)))
    return out


# ============================================================
# 文字列
# ============================================================

# boost::format ("%1%, %2%") → Python (%s, %s) に変換．
# %1% などの位置指定をキャプチャし，対応する引数を文字列化して埋め込む．
_FORMAT_PLACEHOLDER = re.compile(r'%([0-9]+)([a-zA-Z]?)')
# 例: "%1%", "%1$d", "%2%"
_FORMAT_PRINTF = re.compile(r'%(?:(?P<idx>\d+)\$)?(?P<flags>[-+ 0#]*)(?P<width>\d*)(?:\.(?P<prec>\d+))?(?P<conv>[diouxXeEfFgGsc%])')


def _format_arg(var: Var, conv: str) -> str:
    """単一引数を conv 指定子に従って文字列化．"""
    if conv in ('d', 'i'):
        return str(to_integer(var))
    if conv == 'u':
        n = to_integer(var)
        if n < 0:
            n = n & 0xFFFFFFFFFFFFFFFF
        return str(n)
    if conv == 'o':
        return format(to_integer(var) & 0xFFFFFFFFFFFFFFFF, 'o')
    if conv == 'x':
        return format(to_integer(var) & 0xFFFFFFFFFFFFFFFF, 'x')
    if conv == 'X':
        return format(to_integer(var) & 0xFFFFFFFFFFFFFFFF, 'X')
    if conv in ('e', 'E', 'f', 'F', 'g', 'G'):
        # FLOAT は Element.i しか持たないので integer から作る
        return format(float(to_integer(var)), conv)
    if conv == 'c':
        n = to_integer(var)
        return chr(n & 0xFF)
    # %s と既定値: 文字列化
    return to_string(var)


def _format_with_spec(spec_match, var: Var) -> str:
    """%[flags][width][.prec]conv の単発 specifier を Python format に翻訳．"""
    flags = spec_match.group('flags') or ''
    width = spec_match.group('width') or ''
    prec = spec_match.group('prec')
    conv = spec_match.group('conv')
    if conv == '%':
        return '%'
    raw = _format_arg(var, conv)
    # width / flags 適用
    if width:
        w = int(width)
        if '-' in flags:
            raw = raw.ljust(w)
        elif '0' in flags and conv in 'diouxX':
            # 符号があれば符号の後に 0 詰め
            sign = ''
            r = raw
            if r.startswith('-') or r.startswith('+'):
                sign = r[0]; r = r[1:]
            elif '+' in flags and conv in 'di':
                sign = '+'
            r = r.rjust(w - len(sign), '0')
            raw = sign + r
        else:
            raw = raw.rjust(w)
    if prec is not None and conv == 's':
        raw = raw[:int(prec)]
    return raw


def _bi_format(line_info, args, ctx) -> Var:
    """FORMAT(fmt, args...) → string．

    boost::format は `%1%`/`%2%` の位置指定，および printf 風 (`%d`, `%x` ...)
    の両方をサポートしている．ATK2 の .tf では両方が使われる．
    """
    _check_arity_min(line_info, 'FORMAT', 1, len(args))
    fmt = to_string(args[0])
    rest = args[1:]
    out = []
    i = 0
    n = len(fmt)
    arg_pos = 0  # 位置引数の 0-origin index
    while i < n:
        ch = fmt[i]
        if ch != '%':
            out.append(ch)
            i += 1
            continue
        # boost-style %1% を試す
        m = _FORMAT_PLACEHOLDER.match(fmt, i)
        if m and m.group(2) == '':
            idx = int(m.group(1)) - 1
            # 末尾の '%' をスキップ確認
            after = m.end()
            if after < n and fmt[after] == '%':
                if 0 <= idx < len(rest):
                    out.append(to_string(rest[idx]))
                else:
                    out.append('')
                i = after + 1
                continue
        # printf-style
        m = _FORMAT_PRINTF.match(fmt, i)
        if m:
            if m.group('conv') == '%':
                out.append('%')
                i = m.end()
                continue
            idx = m.group('idx')
            if idx is not None:
                a_idx = int(idx) - 1
            else:
                a_idx = arg_pos
                arg_pos += 1
            if 0 <= a_idx < len(rest):
                out.append(_format_with_spec(m, rest[a_idx]))
            else:
                out.append('')
            i = m.end()
            continue
        # マッチしない `%` はそのまま
        out.append(ch)
        i += 1
    return make_str(''.join(out))


def _bi_concat(line_info, args, ctx) -> Var:
    """CONCAT(a, b) → string concatenation．"""
    _check_arity(line_info, 'CONCAT', 2, len(args))
    return make_str(to_string(args[0]) + to_string(args[1]))


def _bi_toupper(line_info, args, ctx) -> Var:
    _check_arity(line_info, 'TOUPPER', 1, len(args))
    return make_str(to_string(args[0]).upper())


def _bi_tolower(line_info, args, ctx) -> Var:
    _check_arity(line_info, 'TOLOWER', 1, len(args))
    return make_str(to_string(args[0]).lower())


def _bi_escstr(line_info, args, ctx) -> Var:
    """ESCSTR(s) → C 風エスケープ済文字列 (両端の `"` 付き) を返す．"""
    _check_arity(line_info, 'ESCSTR', 1, len(args))
    s = to_string(args[0])
    out = ['"']
    for c in s:
        if c == '"': out.append('\\"')
        elif c == '\\': out.append('\\\\')
        elif c == '\n': out.append('\\n')
        elif c == '\t': out.append('\\t')
        elif c == '\r': out.append('\\r')
        elif c == '\0': out.append('\\0')
        elif ord(c) < 0x20: out.append(f'\\x{ord(c):02x}')
        else: out.append(c)
    out.append('"')
    return make_str(''.join(out))


def _bi_unescstr(line_info, args, ctx) -> Var:
    _check_arity(line_info, 'UNESCSTR', 1, len(args))
    s = to_string(args[0])
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    # 単純 unescape
    return make_str(bytes(s, 'utf-8').decode('unicode_escape'))


def _bi_split(line_info, args, ctx) -> Var:
    """SPLIT(s, sep) → list of substrings (Element.s)．"""
    _check_arity(line_info, 'SPLIT', 2, len(args))
    s = to_string(args[0])
    sep = to_string(args[1])
    parts = s.split(sep) if sep else list(s)
    return [Element(s=p) for p in parts]


def _bi_regex_replace(line_info, args, ctx) -> Var:
    """REGEX_REPLACE(s, pattern, replacement)．

    Boost.Regex は ECMAScript 互換で `$1` `$&` 等のバックリファレンスを
    使うが Python re は `\\1` `\\g<0>` を使う．
    boost 風 → Python 風 へ変換してから re.sub に渡す．
    """
    _check_arity(line_info, 'REGEX_REPLACE', 3, len(args))
    s = to_string(args[0])
    pat = to_string(args[1])
    repl = to_string(args[2])
    repl_py = _boost_to_py_replacement(repl)
    return make_str(re.sub(pat, repl_py, s))


_BOOST_REPL_BACKREF = re.compile(r'\$(\d+|\&)')


def _boost_to_py_replacement(repl: str) -> str:
    """`$1` `$2` ... `$&` を Python の `\\1` `\\2` `\\g<0>` に変換．

    `\\` 自体は Python 側の特殊扱いを避けるため `\\\\` にエスケープ．
    """
    out = []
    i = 0
    while i < len(repl):
        c = repl[i]
        if c == '\\':
            # 既存のバックスラッシュは 2 重化して Python re にリテラル渡し
            out.append('\\\\')
            i += 1
            continue
        if c == '$':
            m = _BOOST_REPL_BACKREF.match(repl, i)
            if m:
                ref = m.group(1)
                if ref == '&':
                    out.append('\\g<0>')
                else:
                    out.append('\\g<' + ref + '>')
                i = m.end()
                continue
        out.append(c)
        i += 1
    return ''.join(out)


# ============================================================
# リスト / コレクション
# ============================================================

def _bi_length(line_info, args, ctx) -> Var:
    _check_arity(line_info, 'LENGTH', 1, len(args))
    return make_int(len(args[0]))


def _bi_at(line_info, args, ctx) -> Var:
    """AT(list, index) → list[index]，範囲外なら空 Element．"""
    _check_arity(line_info, 'AT', 2, len(args))
    lst = args[0]
    idx = to_integer(args[1])
    if 0 <= idx < len(lst):
        return [lst[idx]]
    return []


def _bi_find(line_info, args, ctx) -> Var:
    """FIND(list, value) → 0-origin index or 空．"""
    _check_arity(line_info, 'FIND', 2, len(args))
    lst = args[0]
    target = args[1]
    if not target:
        return []
    # 数値なら数値で，それ以外は文字列で照合
    if target[0].i is not None:
        v = target[0].i
        for i, e in enumerate(lst):
            if e.i is not None and e.i == v:
                return make_int(i)
    else:
        v = target[0].s
        for i, e in enumerate(lst):
            if e.s == v:
                return make_int(i)
    return []


def _bi_append(line_info, args, ctx) -> Var:
    """APPEND(list1, list2 [, list3 ...]) → 連結リスト．"""
    _check_arity_min(line_info, 'APPEND', 2, len(args))
    out: Var = []
    for a in args:
        out.extend(a)
    return out


def _bi_reverse(line_info, args, ctx) -> Var:
    _check_arity(line_info, 'REVERSE', 1, len(args))
    return list(reversed(args[0]))


def _bi_sort(line_info, args, ctx) -> Var:
    """SORT(list, fieldName) → list を field 値でソートした結果．

    list の各要素は ID．field[ID] を見て並べ替える．
    """
    _check_arity(line_info, 'SORT', 2, len(args))
    lst = args[0]
    field = to_string(args[1])
    def key(elem: Element):
        idx = str(elem.i) if elem.i is not None else elem.s
        v = ctx.var_map.get(f"{field}[{idx}]", [])
        if v and v[0].i is not None:
            return (0, v[0].i)
        return (1, v[0].s if v else "")
    return sorted(lst, key=key)


def _bi_lsort(line_info, args, ctx) -> Var:
    """LSORT(list, comparator_func_name) → ユーザ関数を比較器に使ってソート．

    比較器は ARGV[1], ARGV[2] を受け，負/0/正の整数を返す．
    """
    _check_arity(line_info, 'LSORT', 2, len(args))
    from tf_eval import _call_user_function  # 循環回避
    lst = args[0]
    fname = to_string(args[1])
    fn = ctx.func_map.get(fname)
    if fn is None:
        raise ExprError(f"`LSORT' comparator `{fname}' not defined")
    import functools

    def cmp(a: Element, b: Element):
        r = _call_user_function(fname, fn, [[a], [b]], ctx, line_info[1])
        return to_integer(r) if r else 0
    return sorted(lst, key=functools.cmp_to_key(cmp))


# ============================================================
# 値構築 / 環境
# ============================================================

def _bi_value(line_info, args, ctx) -> Var:
    """VALUE([str], [int]) → 1 要素 Element を作る．

    引数 0/1/2 個のいずれも許容．
    """
    e = Element()
    if len(args) >= 1:
        e.s = to_string(args[0])
    if len(args) >= 2:
        e.i = to_integer(args[1])
    return [e]


def _bi_environ(line_info, args, ctx) -> Var:
    _check_arity(line_info, 'ENVIRON', 1, len(args))
    name = to_string(args[0])
    val = os.environ.get(name, "")
    e = Element(s=val)
    try:
        e.i = int(val, 0)
    except (ValueError, TypeError):
        pass
    return [e]


def _bi_clean(line_info, args, ctx) -> Var:
    _check_arity(line_info, 'CLEAN', 1, len(args))
    base = to_string(args[0])
    pref = base + "["
    keys = [k for k in ctx.var_map if k.startswith(pref)]
    for k in keys:
        del ctx.var_map[k]
    return []


# ============================================================
# 制御 / メタ
# ============================================================

def _bi_die(line_info, args, ctx) -> Var:
    raise DieTerminate(f"$DIE() called at {line_info[0]}:{line_info[1]}")


def _bi_isfunction(line_info, args, ctx) -> Var:
    _check_arity(line_info, 'ISFUNCTION', 1, len(args))
    name = to_string(args[0])
    return make_int(1 if name in ctx.func_map else 0)


def _bi_call(line_info, args, ctx) -> Var:
    """CALL(name, args...) → 名前指定でユーザ関数を起動．"""
    _check_arity_min(line_info, 'CALL', 1, len(args))
    from tf_eval import _call_user_function
    fname = to_string(args[0])
    fn = ctx.func_map.get(fname)
    if fn is None:
        raise ExprError(f"`CALL' target `{fname}' not defined")
    return _call_user_function(fname, fn, list(args[1:]), ctx, line_info[1])


def _bi_noop(line_info, args, ctx) -> Var:
    return []


def _bi_gettext(line_info, args, ctx) -> Var:
    """GETTEXT(s) / _(s) → s をそのまま返す (i18n 不要)．"""
    _check_arity(line_info, 'GETTEXT', 1, len(args))
    return args[0]


# ============================================================
# デバッグ / 出力
# ============================================================

def _format_var_for_trace(var: Var) -> str:
    parts = []
    for e in var:
        if e.i is not None and e.s:
            parts.append(f"[{e.i}({e.s})]")
        elif e.i is not None:
            parts.append(f"[{e.i}]")
        else:
            parts.append(f"[{e.s}]")
    return "(" + ",".join(parts) + ")"


def _bi_trace(line_info, args, ctx) -> Var:
    """TRACE(var [, file]) → 変数の中身を stderr に表示 (デバッグ用)．"""
    if len(args) not in (1, 2):
        raise ExprError(f"`TRACE' expects 1-2 args at {line_info[0]}:{line_info[1]}")
    body = _format_var_for_trace(args[0])
    msg = f"TRACE: {body}\n"
    if len(args) == 2:
        # ファイル名指定 (簡易: 末尾追加書き込み)
        path = to_string(args[1])
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(msg)
        except OSError:
            pass
    else:
        print(msg, end='', file=ctx.stderr)
    return []


def _bi_dump(line_info, args, ctx) -> Var:
    """DUMP([file]) → 全変数を表示 (デバッグ用)．"""
    out_lines = []
    for k in sorted(ctx.var_map.keys()):
        out_lines.append(f"{k} = {_format_var_for_trace(ctx.var_map[k])}\n")
    msg = "".join(out_lines)
    if args:
        path = to_string(args[0])
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(msg)
        except OSError:
            pass
    else:
        print(msg, end='', file=ctx.stderr)
    return []


# ============================================================
# 登録テーブル
# ============================================================

BUILTINS: Dict[str, Callable] = {
    # 比較
    'EQ': _bi_eq,
    'ALT': _bi_alt,
    # 算術
    'ATOI': _bi_atoi,
    'RANGE': _bi_range,
    # 文字列
    'FORMAT': _bi_format,
    'CONCAT': _bi_concat,
    'TOUPPER': _bi_toupper,
    'TOLOWER': _bi_tolower,
    'ESCSTR': _bi_escstr,
    'UNESCSTR': _bi_unescstr,
    'SPLIT': _bi_split,
    'REGEX_REPLACE': _bi_regex_replace,
    # リスト
    'LENGTH': _bi_length,
    'AT': _bi_at,
    'FIND': _bi_find,
    'APPEND': _bi_append,
    'REVERSE': _bi_reverse,
    'SORT': _bi_sort,
    'LSORT': _bi_lsort,
    # 値 / 環境
    'VALUE': _bi_value,
    'ENVIRON': _bi_environ,
    'CLEAN': _bi_clean,
    # 制御
    'DIE': _bi_die,
    'ISFUNCTION': _bi_isfunction,
    'CALL': _bi_call,
    'NOOP': _bi_noop,
    'GETTEXT': _bi_gettext,
    '_': _bi_gettext,
    # デバッグ
    'TRACE': _bi_trace,
    'DUMP': _bi_dump,
}
