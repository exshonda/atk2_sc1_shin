# -*- coding: utf-8 -*-
#
#  TOPPERS ATK2 cfg (Python port) -- pass 2
#
#  C++ cfg2.cpp の Python 移植．
#  ARXML + cfg1_out.srec/syms + .tf テンプレートから
#  Os_Lcfg.c / Os_Lcfg.h / Os_Cfg_tmp.h / cfg2_out.tf を生成する．
#

import os
import sys
import time
from typing import List, Optional

import atk2_xml
import atk2_bind
import tf_engine
from gen_file import GenFile
from srecord import SRecord


CFG1_OUT_SREC = "cfg1_out.srec"
CFG1_OUT_SYMS = "cfg1_out.syms"


def run(args, output_dir: Optional[str] = None):
    if not args.ini_file_names:
        sys.exit("'--ini-file' must be specified for --kernel atk2")
    if not args.api_table_file_names:
        sys.exit("'--api-table' option must be specified")
    if not args.trb_file_names:
        sys.exit("'-T' template-file must be specified for pass 2")

    # 1. ARXML 木の構築
    xc = atk2_xml.build(
        arxml_paths=list(args.config_files),
        api_table_paths=args.api_table_file_names,
        ini_paths=args.ini_file_names,
    )

    # 2. cfg1_def_table の読み込み
    cfg1_def_table = atk2_xml.parse_cfg1_def_table(
        args.cfg1_def_table_file_names,
    )

    # 3. cfg1_out.srec / cfg1_out.syms の読み込み
    omit_symbol = bool(getattr(args, "omit_symbol", False))
    srec = None
    syms = None
    if not omit_symbol:
        srec_path = _resolve(CFG1_OUT_SREC, output_dir)
        syms_path = _resolve(CFG1_OUT_SYMS, output_dir)
        if os.path.exists(srec_path):
            srec = SRecord(srec_path, "srec")
        if os.path.exists(syms_path):
            syms = atk2_bind.read_symbol_file(syms_path)

    # 4. INCLUDES 文字列 (kernel.tf の $INCLUDES$ で展開される)
    includes_text = "".join(f'#include "{inc}"\n' for inc in xc.includes)

    # 5. binding 構築
    context = atk2_bind.build_context(
        xc, cfg1_def_table,
        srec=srec, syms=syms,
        pass_num=2,
        includes_text=includes_text,
        external_id=bool(getattr(args, "external_id", False)),
        timestamp=int(time.time()),
    )

    # 6. .tf テンプレート評価
    include_dirs = list(args.include_directories or [])
    outputs = tf_engine.run(
        list(args.trb_file_names),
        context=context,
        include_dirs=include_dirs,
    )

    # 7. 出力ファイルを GenFile に流し込む
    # 末尾 '\n' は tf_eval.switch_file が C++ 同様に管理する．
    for fname, text in outputs.items():
        if not fname:
            continue
        path = _resolve(fname, output_dir)
        GenFile(path).append(text)


def _resolve(name: str, output_dir: Optional[str]) -> str:
    if output_dir:
        return os.path.join(output_dir, name)
    return name
