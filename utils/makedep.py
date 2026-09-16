#!/usr/bin/env python3
#
#  TOPPERS ATK2
#      Toyohashi Open Platform for Embedded Real-Time Systems
#      Automotive Kernel Version 2
#
#  ヘッダファイル依存関係生成ツール
#
#  gcc の -MMD -MP 相当の依存関係ファイル (.d) を生成する．
#
#  CC-RH (ccrh) にも -MMD/-MP は存在するが，出力される依存先のパスが
#  Windows 形式の絶対パス (バックスラッシュ区切り) になるため，Cygwin/MSYS
#  の make では解決できない．さらにパスに非 ASCII 文字が含まれる場合は
#  CP932 で出力されるため，テキスト処理による変換も現実的でない．
#  そこで本スクリプトで，Makefile が与えたのと同じ相対パス表現のまま
#  依存関係を生成する．
#
#  使い方:
#      python makedep.py -o <objfile> -f <depfile> <source> [-I<dir> ...]
#
#  <source> の #include を再帰的に辿り，-I で与えられたディレクトリ
#  （および include 元ファイルのあるディレクトリ）から見つかったものだけを
#  依存先として出力する．見つからないもの（コンパイラ添付のヘッダなど）は
#  無視する．アセンブリソースの `$include (file)` 形式にも対応する．
#
#  プリプロセッサの条件分岐は解釈しない（すべての #include を辿る）．
#  依存関係としては安全側（過剰に依存する）に倒れるため問題ない．
#

import argparse
import os
import re
import sys

INCLUDE_RE = re.compile(rb'^\s*#\s*include\s*([<"])([^>"]+)[>"]')
ASM_INCLUDE_RE = re.compile(rb'^\s*\$\s*include\s*\(\s*([^)]+?)\s*\)')


def norm(path):
    """make が扱いやすいようにスラッシュ区切りへ正規化する．"""
    return os.path.normpath(path).replace(os.sep, '/')


def scan(path):
    """1 ファイル中の include 指定を (is_system, name) のリストで返す．"""
    result = []
    try:
        with open(path, 'rb') as f:
            for line in f:
                m = INCLUDE_RE.match(line)
                if m:
                    result.append((m.group(1) == b'<',
                                   m.group(2).decode('utf-8', 'replace')))
                    continue
                m = ASM_INCLUDE_RE.match(line)
                if m:
                    result.append((False,
                                   m.group(1).decode('utf-8', 'replace')))
    except OSError:
        pass
    return result


def resolve(name, from_dir, incdirs, quoted):
    dirs = ([from_dir] if quoted else []) + incdirs
    for d in dirs:
        cand = os.path.join(d, name) if d else name
        if os.path.isfile(cand):
            return norm(cand)
    return None


def collect(src, incdirs):
    """src から辿れる依存ファイルの集合を返す．"""
    deps = []
    seen = set()
    queue = [src]
    while queue:
        cur = queue.pop(0)
        for is_system, name in scan(cur):
            path = resolve(name, os.path.dirname(cur), incdirs,
                           not is_system)
            if path is None or path in seen:
                continue
            seen.add(path)
            deps.append(path)
            queue.append(path)
    return deps


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-o', '--obj', required=True)
    parser.add_argument('-f', '--out', required=True)
    parser.add_argument('-h', '--help', action='help')
    args, rest = parser.parse_known_args()

    incdirs = []
    source = None
    for arg in rest:
        if arg.startswith('-I'):
            incdirs.append(arg[2:] or '.')
        elif not arg.startswith('-'):
            source = arg

    if source is None:
        sys.stderr.write('makedep.py: no source file given\n')
        return 1

    deps = collect(source, incdirs)

    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    lines = ['%s: %s%s\n' % (norm(args.obj), norm(source),
                             ''.join(' \\\n  ' + d for d in deps))]
    #  -MP 相当．ヘッダが削除された時に make が止まらないようにする．
    lines += ['%s:\n' % d for d in deps]
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(lines)
    return 0


if __name__ == '__main__':
    sys.exit(main())
