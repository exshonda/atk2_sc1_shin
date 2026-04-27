# -*- coding: utf-8 -*-
#
#  TOPPERS ATK2 cfg (Python port) -- pass 3
#
#  C++ cfg3.cpp の Python 移植．
#  ARXML + ROM 像 + シンボルテーブル + .tf テンプレートから
#  offset.h (target_offset.tf) または check (target_check.tf) を生成する．
#

import os
import sys
import time
from typing import Optional

import atk2_xml
import atk2_bind
import tf_engine
from gen_file import GenFile
from srecord import SRecord
from tf_value import make_int


def run(args, output_dir: Optional[str] = None):
    if not args.ini_file_names:
        sys.exit("'--ini-file' must be specified for --kernel atk2")
    if not args.api_table_file_names:
        sys.exit("'--api-table' option must be specified")
    if not args.trb_file_names:
        sys.exit("'-T' template-file must be specified for pass 3")

    rom_image_path = getattr(args, "rom_image_file_name", None)
    rom_symbol_path = (getattr(args, "rom_symbol_file_name", None)
                        or getattr(args, "symbol_table_file_name", None))
    if not rom_image_path or not os.path.exists(rom_image_path):
        sys.exit(f"'--rom-image' file not found: {rom_image_path}")
    if not rom_symbol_path or not os.path.exists(rom_symbol_path):
        sys.exit(f"symbol table file not found: {rom_symbol_path}")

    # 1. ARXML 木
    xc = atk2_xml.build(
        arxml_paths=list(args.config_files),
        api_table_paths=args.api_table_file_names,
        ini_paths=args.ini_file_names,
    )
    # 2. cfg1_def_table
    cfg1_def_table = atk2_xml.parse_cfg1_def_table(
        args.cfg1_def_table_file_names,
    )
    # 3. ROM image / symbol table (atk2-sc1.srec/syms 等．SYMBOL/PEEK 用)
    if rom_image_path.endswith(".srec"):
        rom_srec = SRecord(rom_image_path, "srec")
    else:
        rom_srec = SRecord(rom_image_path, "dump")
    rom_syms = atk2_bind.read_symbol_file(rom_symbol_path)

    # 3b. cfg1_out.srec / cfg1_out.syms (cfg1_def_table 解決用．C++ pass3 も
    #     `cfg1_out->load_srec()` をデフォルトで読み込む)．
    cfg1_srec = None
    cfg1_syms = None
    cfg1_srec_path = "cfg1_out.srec"
    cfg1_syms_path = "cfg1_out.syms"
    if output_dir:
        cfg1_srec_path = os.path.join(output_dir, cfg1_srec_path)
        cfg1_syms_path = os.path.join(output_dir, cfg1_syms_path)
    if os.path.exists(cfg1_srec_path):
        cfg1_srec = SRecord(cfg1_srec_path, "srec")
    if os.path.exists(cfg1_syms_path):
        cfg1_syms = atk2_bind.read_symbol_file(cfg1_syms_path)

    # 4. INCLUDES
    includes_text = "".join(f'#include "{inc}"\n' for inc in xc.includes)

    # 5. binding．TOPPERS_cfg_* 解決には cfg1_out.{srec,syms} を使う．
    context = atk2_bind.build_context(
        xc, cfg1_def_table,
        srec=cfg1_srec if cfg1_srec is not None else rom_srec,
        syms=cfg1_syms if cfg1_syms is not None else rom_syms,
        pass_num=3,
        includes_text=includes_text,
        external_id=bool(getattr(args, "external_id", False)),
        timestamp=int(time.time()),
    )
    # SYMBOL/PEEK のクロージャは ROM image (atk2-sc1) を見るよう設定
    srec = rom_srec
    syms = rom_syms

    # 6. SYMBOL / PEEK / BCOPY / BZERO ビルトインを追加
    from tf_builtin import BUILTINS
    extra_builtins = dict(BUILTINS)

    def _bi_symbol(line_info, args_v, ctx):
        from tf_value import to_string
        name = to_string(args_v[0])
        addr = syms.get(name)
        if addr is None:
            return []
        return make_int(addr)

    def _bi_peek(line_info, args_v, ctx):
        from tf_value import to_integer
        addr = to_integer(args_v[0])
        size = to_integer(args_v[1]) if len(args_v) >= 2 else 1
        signed = bool(to_integer(args_v[2])) if len(args_v) >= 3 else False
        try:
            value = int(srec.get_value(addr, size, signed))
            return make_int(value)
        except Exception:
            return []

    def _bi_bcopy(line_info, args_v, ctx):
        from tf_value import to_integer
        if len(args_v) < 3:
            return []
        src = to_integer(args_v[0])
        dst = to_integer(args_v[1])
        size = to_integer(args_v[2])
        try:
            srec.copy_data(src, dst, size)
        except Exception:
            pass
        return []

    def _bi_bzero(line_info, args_v, ctx):
        from tf_value import to_integer
        if len(args_v) < 2:
            return []
        addr = to_integer(args_v[0])
        size = to_integer(args_v[1])
        try:
            srec.set_data(addr, "00" * size)
        except Exception:
            pass
        return []

    extra_builtins["SYMBOL"] = _bi_symbol
    extra_builtins["PEEK"] = _bi_peek
    extra_builtins["BCOPY"] = _bi_bcopy
    extra_builtins["BZERO"] = _bi_bzero

    # 7. テンプレート評価
    include_dirs = list(args.include_directories or [])
    # cfg2_out.tf を取り込めるよう output_dir も検索パスに足す
    if output_dir:
        include_dirs = [output_dir] + include_dirs
    else:
        include_dirs = ["."] + include_dirs
    outputs = tf_engine.run(
        list(args.trb_file_names),
        context=context,
        include_dirs=include_dirs,
        builtins=extra_builtins,
    )
    # 8. 出力
    for fname, text in outputs.items():
        if not fname:
            continue
        path = os.path.join(output_dir, fname) if output_dir else fname
        GenFile(path).append(text)
