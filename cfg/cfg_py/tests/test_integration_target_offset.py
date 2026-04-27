# -*- coding: utf-8 -*-
#
#  Phase 3 統合テスト: target_offset.tf を Python tf_engine で評価し，
#  cfg.exe の生成する offset.h と一致することを確認する．
#
#  cfg.exe は pass3 で srec/syms から各 cfg1_def_table エントリの値を
#  解決して macro_processor の変数として注入する．Phase 3 段階では
#  syms から事前に取得した値を合成 context として渡し，テンプレート
#  単体の評価結果を確認する．Phase 4 で srec/syms 連携を本実装する．
#

import os
import sys

import pytest

# テスト対象パス．tests/ -> cfg_py/ -> cfg/ -> atk2-sc1_nios2/
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
_TARGET_OFFSET_TF = os.path.join(
    _REPO_ROOT, "target", "nucleo_h563zi_gcc", "target_offset.tf",
)
_REFERENCE_OFFSET_H = os.path.join(
    _REPO_ROOT, "obj", "obj_nucleo_h563zi", "offset.h",
)
_INCLUDE_DIRS = [
    _REPO_ROOT,
    os.path.join(_REPO_ROOT, "kernel"),
    os.path.join(_REPO_ROOT, "arch"),
    os.path.join(_REPO_ROOT, "target", "nucleo_h563zi_gcc"),
]


def _load_offset_values_from_syms_and_srec():
    """obj_nucleo_h563zi/cfg1_out.{syms,srec} を読んで cfg1_def_table の
    各エントリの値を取り出す．

    Phase 4 の atk2_pass3 ではここで実装するが，テストではシンプルに
    既存の cfg.exe 生成済 offset.h から逆算した値を使う．
    """
    # 期待値は offset.h から逆引き
    return {
        "offsetof_TCB_p_tinib": 8,
        "offsetof_TCB_curpri": 12,
        "offsetof_TCB_sp": 32,
        "offsetof_TCB_pc": 36,
        "offsetof_TCB_fpu_flag": 40,
        "offsetof_TINIB_task": 0,
        "offsetof_TINIB_exepri": 16,
        "offsetof_INTINIB_remain_stksz": 12,
        "offsetof_ISRCB_p_intinib": 0,
    }


@pytest.mark.skipif(
    not os.path.exists(_TARGET_OFFSET_TF),
    reason="target_offset.tf not found",
)
def test_target_offset_tf_matches_reference():
    """target_offset.tf を評価して offset.h と一致するか確認．"""
    from tf_engine import run
    from tf_builtin import BUILTINS
    from tf_value import make_int, make_str

    # SYMBOL / PEEK / BCOPY / BZERO は pass3 で srec/syms 経由で実体が
    # 登録される．Phase 3 単体テストではテーブルベースのダミーを使う．
    # 期待値: cfg.exe が生成した cfg1_out.exe の MAGIC_1/2/4 シンボル．
    SYMBOL_TABLE = {"MAGIC_1": 0, "MAGIC_2": 1, "MAGIC_4": 3}
    # MAGIC_n はそれぞれ {0x12}, {0x34, 0x12} (little endian),
    # {0x78, 0x56, 0x34, 0x12} (little endian) のバイト列を持つ．
    PEEK_TABLE = {0: 0x12,
                  1: 0x34, 2: 0x12,
                  3: 0x78, 4: 0x56, 5: 0x34, 6: 0x12}

    def _bi_symbol(line_info, args, ctx):
        from tf_value import to_string
        name = to_string(args[0])
        if name in SYMBOL_TABLE:
            return make_int(SYMBOL_TABLE[name])
        return []

    def _bi_peek(line_info, args, ctx):
        from tf_value import to_integer
        addr = to_integer(args[0])
        return make_int(PEEK_TABLE.get(addr, 0))

    extra = dict(BUILTINS)
    extra["SYMBOL"] = _bi_symbol
    extra["PEEK"] = _bi_peek

    context = {
        # 標準特殊変数
        "NL": "\n",
        "TAB": "\t",
        "SPC": " ",
        # cfg1_def_table 由来 (本来は srec/syms から取得．ここでは決め打ち)
        "SIL_ENDIAN_BIG": 0,
        "SIL_ENDIAN_LITTLE": 1,
        **_load_offset_values_from_syms_and_srec(),
    }
    outputs = run(
        [_TARGET_OFFSET_TF],
        context=context,
        include_dirs=_INCLUDE_DIRS,
        builtins=extra,
    )
    # `$FILE "offset.h"$` で切替え後の出力を取得
    actual = outputs.get("offset.h", "")
    if not os.path.exists(_REFERENCE_OFFSET_H):
        pytest.skip(f"reference offset.h not found at {_REFERENCE_OFFSET_H}")
    with open(_REFERENCE_OFFSET_H, "r", encoding="utf-8") as f:
        expected = f.read()
    # 改行コード差を吸収 (cfg.exe は Windows text-mode で CRLF を吐く)
    actual_norm = actual.replace("\r\n", "\n")
    expected_norm = expected.replace("\r\n", "\n")
    assert actual_norm == expected_norm, (
        f"offset.h mismatch.\n--- expected ---\n{expected_norm!r}\n"
        f"--- actual ---\n{actual_norm!r}\n"
    )
