# -*- coding: utf-8 -*-
#
#  TOPPERS ATK2 cfg (Python port) -- pass 1
#
#  Phase 4 で atk2_xml.build() を共通インフラとして使うように再構成．
#  ARXML 木の構築・マージ・リネーム・ID 振り分けを atk2_xml に委譲し，
#  pass1 の責務は cfg1_out.c の生成だけに絞る．
#

import os
import sys
from typing import List

from gen_file import GenFile
from atk2_xml import build, parse_cfg1_def_table, Cfg1Def

CFG1_OUT_C = "cfg1_out.c"


def _expand_cfg1_def_entry(d: Cfg1Def) -> str:
    """C++ cfg1_out.cpp do_generate_cfg1_def() の 1 行を Python に逐写．"""
    name = d.name
    expr = d.expression
    type_str = "signed_t" if d.is_signed else "unsigned_t"
    is_pp = expr.startswith("#")
    if d.value1 != "" or d.value2 != "":
        is_pp = True
    if is_pp:
        e = expr[1:] if expr.startswith("#") else expr
        v1 = d.value1 if d.value1 != "" else "1"
        v2 = d.value2 if d.value2 != "" else "0"
        return (
            f"const {type_str} TOPPERS_cfg_{name} = \n"
            f"#if {e}\n"
            f"({v1});\n"
            f"#else\n"
            f"({v2});\n"
            f"#endif\n"
        )
    if expr.startswith("@"):
        return (
            f"const volatile void* const TOPPERS_cfg_{name} "
            f"= ({expr[1:]});\n"
        )
    return f"const {type_str} TOPPERS_cfg_{name} = ( {type_str} ){expr};\n"


def _build_cfg1_out_c(includes: List[str], def_list: List[Cfg1Def],
                       valueof_macros: List[str]) -> str:
    """cfg1_out.c の本文を組み立てる (LF 区切り)．"""
    parts: List[str] = []
    parts.append('/* cfg1_out.c */\n')
    parts.append('#define TOPPERS_CFG1_OUT  1\n')
    parts.append('#include "kernel/kernel_int.h"\n')
    for inc in includes:
        parts.append(f'#include "{inc}"\n')
    parts.append('\n')
    # typedef ブロック
    parts.append(
        '\n'
        '#ifdef INT64_MAX\n'
        '  typedef sint64 signed_t;\n'
        '  typedef uint64 unsigned_t;\n'
        '#else\n'
        '  typedef sint32 signed_t;\n'
        '  typedef uint32 unsigned_t;\n'
        '#endif\n'
    )
    parts.append('\n#include "target_cfg1_out.h"\n\n')
    # do_generate_cfg1_def の冒頭固定部分
    parts.append(
        'const uint32 TOPPERS_cfg_magic_number = 0x12345678;\n'
        'const uint32 TOPPERS_cfg_sizeof_signed_t = sizeof(signed_t);\n'
        'const uint32 TOPPERS_cfg_sizeof_pointer = sizeof(const volatile void*);\n'
        '\n'
    )
    for d in def_list:
        parts.append(_expand_cfg1_def_entry(d))
    # cfg1_out_list_: /* #include "..." */ + valueof_*
    for inc in includes:
        parts.append(f'/* #include "{inc}" */\n')
    for line in valueof_macros:
        parts.append(line)
    parts.append('\n')
    return "".join(parts)


def run(args, output_dir=None):
    """pass1 のエントリ．cfg.py から `--kernel atk2 --pass 1` で呼ばれる．"""
    if not args.ini_file_names:
        sys.exit("'--ini-file' must be specified for --kernel atk2")
    if not args.api_table_file_names:
        sys.exit("'--api-table' option must be specified in pass 1")
    arxml_paths = list(args.config_files)
    xc = build(
        arxml_paths=arxml_paths,
        api_table_paths=args.api_table_file_names,
        ini_paths=args.ini_file_names,
    )
    def_list = parse_cfg1_def_table(args.cfg1_def_table_file_names)
    body = _build_cfg1_out_c(xc.includes, def_list, xc.valueof_macros)
    out_path = CFG1_OUT_C
    if output_dir:
        out_path = os.path.join(output_dir, CFG1_OUT_C)
    GenFile(out_path).append(body)
