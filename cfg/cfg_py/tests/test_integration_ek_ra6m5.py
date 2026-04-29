# -*- coding: utf-8 -*-
#
#  Phase 5 統合テスト: EK-RA6M5 ターゲットの cfg 出力をスナップショット
#  比較する．`cfg/cfg_py/tests/fixtures/ek_ra6m5/` に固めた arxml +
#  cfg1_out.{srec,syms} に対して `cfg/cfg_py/cfg.py` を pass1/2/3 まで
#  サブプロセス起動し，生成された cfg1_out.c / Os_Lcfg.{c,h} / Os_Cfg.h /
#  offset.h が `expected/` 配下のリファレンスと一致することを確認する．
#
#  H5 用 `test_integration_target_offset.py` は target_offset.tf を
#  tf_engine 経由で単体評価しオフセット値だけを比較していたが，本テスト
#  は cfg.py CLI ごと走らせる．EK-RA6M5 では C++ 版 cfg.exe との
#  バイト一致 baseline は取らないため，cfg_py 自身の出力スナップショット
#  に対する回帰検出が目的．
#
#  Phase 4 の実機検証で動作確認できた状態を expected/ として固定している．
#  expected/ の更新は意図的な仕様変更時のみ手動で行う．
#

import os
import shutil
import subprocess
import sys

import pytest


_HERE = os.path.dirname(os.path.abspath(__file__))
# tests/ -> cfg_py/ -> cfg/ -> repo root
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
_CFG_PY = os.path.join(_REPO_ROOT, "cfg", "cfg_py", "cfg.py")
_FIXTURE = os.path.join(_HERE, "fixtures", "ek_ra6m5")
_EXPECTED = os.path.join(_FIXTURE, "expected")

_TARGETDIR = os.path.join(_REPO_ROOT, "target", "ek_ra6m5_llvm")
_KERNEL_CSV = os.path.join(_REPO_ROOT, "kernel", "kernel.csv")
_KERNEL_DEF_CSV = os.path.join(_REPO_ROOT, "kernel", "kernel_def.csv")
_KERNEL_INI = os.path.join(_REPO_ROOT, "kernel", "kernel.ini")
_PRC_DEF_CSV = os.path.join(_REPO_ROOT, "arch", "arm_m_gcc", "common",
                             "prc_def.csv")

#  cfg.py が .tf / .csv を解決するための include パス．
#  Makefile が渡す全パスを再現する必要はなく，テンプレートが参照する
#  範囲だけで足りる:
#    - <repo>           : kernel/kernel.tf, arch/arm_m_gcc/common/prc.tf
#    - <repo>/kernel    : 一部 $INCLUDE が "kernel/" 抜きで書かれた場合の保険
#    - <repo>/arch      : "arm_m_gcc/common/prc.tf" 形式の解決
#    - <targetdir>      : target.tf, target_offset.tf, target_check.tf
#    - <repo>/arch/arm_m_gcc/common: prc_offset.tf 等
_INCLUDE_DIRS = [
    _REPO_ROOT,
    os.path.join(_REPO_ROOT, "kernel"),
    os.path.join(_REPO_ROOT, "arch"),
    _TARGETDIR,
    os.path.join(_REPO_ROOT, "arch", "arm_m_gcc", "common"),
]

#  arxml ファイル名 (basename)．workspace の cwd 直下に置いて basename
#  指定で cfg.py に渡す．OsInclude の中身は basename しか含まないので
#  cfg1_out.c の生成結果はパス非依存になる．
_ARXML_FILES = ["sample1.arxml", "target_serial.arxml",
                "target_hw_counter.arxml"]


# ---------------------------------------------------------------- helpers


def _have_fixtures():
    """fixture 一式が揃っているか確認．足りなければ skip．"""
    needed = [_CFG_PY, _FIXTURE, _EXPECTED]
    needed += [os.path.join(_FIXTURE, f) for f in _ARXML_FILES]
    needed += [os.path.join(_FIXTURE, "cfg1_out.srec"),
               os.path.join(_FIXTURE, "cfg1_out.syms")]
    needed += [os.path.join(_EXPECTED, f) for f in
               ("cfg1_out.c", "Os_Lcfg.c", "Os_Lcfg.h",
                "Os_Cfg.h", "offset.h")]
    return all(os.path.exists(p) for p in needed)


@pytest.fixture(scope="module")
def workspace(tmp_path_factory):
    """1 セッション 1 回だけ workspace を作って，arxml と cfg1_out.{srec,syms}
    を fixture からコピーする．pass1/pass2/pass3 はこの同じ tmp_path を
    使い，前段の出力が後段の比較対象を汚染しないよう pass ごとに
    `expected/` のファイルを workspace に上書きコピーしないよう注意．
    """
    if not _have_fixtures():
        pytest.skip("EK-RA6M5 fixtures not present "
                    "(see phase5.md for setup)")
    ws = tmp_path_factory.mktemp("ek_ra6m5_cfg_py")
    for f in _ARXML_FILES + ["cfg1_out.srec", "cfg1_out.syms"]:
        shutil.copy(os.path.join(_FIXTURE, f), str(ws))
    return str(ws)


def _common_cfg_args():
    """全 pass 共通の引数 (kernel + include + table 群)．"""
    args = ["--kernel", "atk2"]
    for d in _INCLUDE_DIRS:
        args += ["-I", d]
    args += [
        "--api-table", _KERNEL_CSV,
        "--cfg1-def-table", _KERNEL_DEF_CSV,
        "--ini-file", _KERNEL_INI,
        "--cfg1-def-table", _PRC_DEF_CSV,
    ]
    return args


def _run_cfg(workspace, extra_args):
    """cfg.py を workspace を cwd にしてサブプロセス起動する．
    standard out/err を tee 的に capture する．失敗時は stderr を含めて
    AssertionError．"""
    cmd = [sys.executable, _CFG_PY] + _common_cfg_args() + extra_args + \
          _ARXML_FILES
    #  Windows + Python 3.14 + pytest の組合せで stdin がクローズ済の場合
    #  capture_output=True の内部 _make_inheritable が WinError 6 を出す．
    #  stdin に明示的に DEVNULL を与えると回避できる．
    result = subprocess.run(cmd, cwd=workspace,
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True, encoding="utf-8")
    assert result.returncode == 0, (
        f"cfg.py failed (exit {result.returncode})\n"
        f"cmd: {' '.join(cmd)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}\n"
    )
    return result


def _diff_against_expected(workspace, name, actual_name=None):
    """workspace/<actual_name or name> と _EXPECTED/<name> を改行コード差
    を吸収してバイト比較する．

    `actual_name` を別名で指定するのは Os_Cfg.h 用．cfg_py は pass2 で
    `Os_Cfg_tmp.h` を生成し，Makefile が cmp して差異があれば
    `Os_Cfg.h` に mv するという 2 段階．本テストは「cfg_py 出力そのもの」
    を見たいので Os_Cfg_tmp.h を直接拾う．
    """
    actual_path = os.path.join(workspace, actual_name or name)
    expected_path = os.path.join(_EXPECTED, name)
    assert os.path.exists(actual_path), \
        f"{actual_name or name} was not generated"
    with open(actual_path, "r", encoding="utf-8") as f:
        actual = f.read().replace("\r\n", "\n")
    with open(expected_path, "r", encoding="utf-8") as f:
        expected = f.read().replace("\r\n", "\n")
    #  Update hint: for Os_Cfg.h, cfg_py emits Os_Cfg_tmp.h (Makefile renames).
    #  The build's obj/ holds the post-rename Os_Cfg.h which is byte-equal to
    #  the cmp_tmp.h emitted just before, so we can still source from
    #  obj/obj_ek_ra6m5/Os_Cfg.h to refresh the fixture.
    assert actual == expected, (
        f"{name} mismatch (cfg_py output vs fixture).\n"
        f"  expected: {expected_path}\n"
        f"  actual:   {actual_path}\n"
        f"  hint: if this change is intentional, run a full "
        f"`make -C obj/obj_ek_ra6m5` and copy obj/obj_ek_ra6m5/{name} "
        f"into expected/{name}."
    )


# ---------------------------------------------------------------- tests


def test_pass1_generates_expected_cfg1_out_c(workspace):
    """pass1: arxml + def csv → cfg1_out.c"""
    _run_cfg(workspace, ["--pass", "1"])
    _diff_against_expected(workspace, "cfg1_out.c")


def test_pass2_generates_expected_os_lcfg_and_os_cfg(workspace):
    """pass2: target.tf 評価 → Os_Lcfg.c / Os_Lcfg.h / Os_Cfg.h

    pass2 は cfg1_out.{srec,syms} を直接は読まないが，--rom-image /
    --symbol-table の指定有無で挙動が変わらないことを利用して，本ターゲット
    の Makefile と同じ呼び出し (rom-image/symbol-table 無し) で実行する．
    """
    target_tf = os.path.join(_TARGETDIR, "target.tf")
    _run_cfg(workspace, ["--pass", "2", "-T", target_tf])
    _diff_against_expected(workspace, "Os_Lcfg.c")
    _diff_against_expected(workspace, "Os_Lcfg.h")
    #  cfg_py は Os_Cfg_tmp.h で出力する (Makefile が cmp 後に Os_Cfg.h
    #  へ mv する).  Phase 4 build 時の expected/Os_Cfg.h は mv 済の
    #  内容でこれは Os_Cfg_tmp.h とバイト一致する．
    _diff_against_expected(workspace, "Os_Cfg.h",
                           actual_name="Os_Cfg_tmp.h")


def test_pass3_offset_generates_expected_offset_h(workspace):
    """pass3 (target_offset.tf): cfg1_out.{srec,syms} + arxml → offset.h

    Makefile の `make offset.h` 経路を再現する．cfg.py は --rom-image と
    --symbol-table を受けて SYMBOL/PEEK 組込関数で値を解決する．
    """
    offset_tf = os.path.join(_TARGETDIR, "target_offset.tf")
    _run_cfg(workspace, [
        "--pass", "3",
        "--rom-image", "cfg1_out.srec",
        "--symbol-table", "cfg1_out.syms",
        "-T", offset_tf,
    ])
    _diff_against_expected(workspace, "offset.h")
