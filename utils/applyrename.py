#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  TOPPERS Software
#      Toyohashi Open Platform for Embedded Real-Time Systems
#
#  Copyright (C) 2003 by Embedded and Real-Time Systems Laboratory
#                              Toyohashi Univ. of Technology, JAPAN
#  Copyright (C) 2004-2011 by Embedded and Real-Time Systems Laboratory
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#
#  本ソフトウェアは TOPPERS ライセンスに従う．
#  詳細はオリジナルの Perl 版 utils/applyrename を参照．
#

"""シンボル一括リネームツール．

`<prefix>_rename.def` を読み込み，与えられた各ファイル内の対象シンボル
`<sym>` を `kernel_<sym>` (または `_kernel_<sym>`) に書き換える．

書き換え対象がある場合のみ元ファイルを `.bak` 退避して新内容に置換する．
差分が無いファイルは触らない．
"""

import filecmp
import os
import re
import sys


def apply_rename(in_file, syms_re):
    """ファイルの内容を syms_re に従って置換する.

    元ファイルと一致しない場合のみ in_file.bak を作って入れ替える．
    """
    out_file = in_file + ".new"

    with open(in_file, "r", encoding="utf-8", errors="surrogateescape") as fin, \
         open(out_file, "w", encoding="utf-8",
              errors="surrogateescape", newline="") as fout:
        for line in fin:
            # Perl 版: $line =~ s/\b(_?)($syms)\b/$1_kernel_$2/gc
            new_line = syms_re.sub(r'\1_kernel_\2', line)
            fout.write(new_line)

    # 内容比較 (バイナリ一致)
    if filecmp.cmp(in_file, out_file, shallow=False):
        os.remove(out_file)
        return False

    bak = in_file + ".bak"
    if os.path.exists(bak):
        os.remove(bak)
    os.rename(in_file, bak)
    os.rename(out_file, in_file)
    sys.stderr.write(f"Modified: {in_file}\n")
    return True


def main():
    if len(sys.argv) < 3:
        sys.exit("Usage: applyrename.py <prefix> <filelist>")

    prefix = sys.argv[1]
    files = sys.argv[2:]

    deffile = prefix + "_rename.def"
    syms = []
    try:
        with open(deffile, "r", encoding="utf-8",
                  errors="surrogateescape") as fp:
            for raw in fp:
                line = raw.rstrip("\r\n")
                if line.startswith("#"):
                    continue
                if re.match(r'^INCLUDE[ \t]+', line):
                    continue
                if line.strip() == "":
                    continue
                syms.append(line)
    except OSError as e:
        sys.exit(f"Cannot open {deffile}: {e}")

    if not syms:
        return

    # syms を or 連結した正規表現
    pattern = r'\b(_?)(' + "|".join(re.escape(s) for s in syms) + r')\b'
    syms_re = re.compile(pattern)

    for in_file in files:
        if not os.path.isfile(in_file):
            continue
        if in_file == deffile:
            continue
        apply_rename(in_file, syms_re)


if __name__ == "__main__":
    main()
