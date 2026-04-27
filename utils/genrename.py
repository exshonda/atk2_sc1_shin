#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  TOPPERS Software
#      Toyohashi Open Platform for Embedded Real-Time Systems
#
#  Copyright (C) 2003 by Embedded and Real-Time Systems Laboratory
#                              Toyohashi Univ. of Technology, JAPAN
#  Copyright (C) 2005-2011 by Embedded and Real-Time Systems Laboratory
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#
#  本ソフトウェアは TOPPERS ライセンスに従う．
#  詳細はオリジナルの Perl 版 utils/genrename を参照．
#

"""`<prefix>_rename.h` / `<prefix>_unrename.h` を生成するスクリプト．

`<prefix>_rename.def` を読んで，シンボル名のリストから `#define` /
`#undef` のリネームヘッダを 2 本生成する．
"""

import re
import sys


def prefix_string(sym):
    """記号が小文字を含むなら kernel_，無ければ KERNEL_ を返す．"""
    return "kernel_" if re.search(r'[a-z]', sym) else "KERNEL_"


def emit_define(fp, sym, prefix):
    head = f"#define {prefix}{sym}"
    # 4 文字単位でタブを足し込む (Perl 版と同じ整列)
    pad = ""
    total_len = len(prefix) + len(sym)
    for limit in (4, 8, 12, 16, 20, 24):
        if total_len < limit:
            pad += "\t"
    fp.write(f"{head}{pad}\t{prefix}{prefix_string(sym)}{sym}\n")


def emit_undef(fp, sym, prefix):
    fp.write(f"#undef {prefix}{sym}\n")


def emit_include(file_token, suffix):
    """`INCLUDE <hdr.h>` 行を `#include <hdr_rename.h>` 等に置換する．"""
    return "#include " + re.sub(r'([>"])$', f'_{suffix}.h\\1',
                                  file_token) + "\n"


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: genrename.py <prefix>")

    name = sys.argv[1]
    name_upper = name.upper()
    infile = name + "_rename.def"
    header_def = "TOPPERS_" + name_upper + "_RENAME_H"

    try:
        with open(infile, "r", encoding="utf-8",
                  errors="surrogateescape") as fp:
            lines = [ln.rstrip("\r\n") for ln in fp]
    except OSError as e:
        sys.exit(f"Cannot open {infile}: {e}")

    # rename.h
    includes = ""
    out_path = name + "_rename.h"
    with open(out_path, "w", encoding="utf-8",
              errors="surrogateescape", newline="\n") as fp:
        fp.write(f"/* This file is generated from {infile} by genrename. */\n\n"
                 f"#ifndef {header_def}\n"
                 f"#define {header_def}\n\n")
        for sym in lines:
            if sym.startswith("#"):
                fp.write("/*\n")
                fp.write(f" * {sym[1:]}\n")
                fp.write(" */\n")
            elif (m := re.match(r'^INCLUDE[ \t]+(.*)$', sym)):
                includes += emit_include(m.group(1), "rename")
            elif sym != "":
                emit_define(fp, sym, "")
            else:
                fp.write("\n")
        fp.write("\n")
        fp.write(includes)
        fp.write(f"#endif /* {header_def} */\n")

    # unrename.h
    includes = ""
    out_path = name + "_unrename.h"
    with open(out_path, "w", encoding="utf-8",
              errors="surrogateescape", newline="\n") as fp:
        fp.write(f"/* This file is generated from {infile} by genrename. */\n\n"
                 f"/* This file is included only when "
                 f"{name}_rename.h has been included. */\n"
                 f"#ifdef {header_def}\n"
                 f"#undef {header_def}\n\n")
        for sym in lines:
            if sym.startswith("#"):
                fp.write("/*\n")
                fp.write(f" * {sym[1:]}\n")
                fp.write(" */\n")
            elif (m := re.match(r'^INCLUDE[ \t]+(.*)$', sym)):
                includes += emit_include(m.group(1), "unrename")
            elif sym != "":
                emit_undef(fp, sym, "")
            else:
                fp.write("\n")
        fp.write("\n")
        fp.write(includes)
        fp.write(f"#endif /* {header_def} */\n")


if __name__ == "__main__":
    main()
