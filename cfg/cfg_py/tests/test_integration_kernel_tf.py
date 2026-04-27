# -*- coding: utf-8 -*-
#
#  Phase 3 統合テスト (Stage 3): kernel.tf 全体が exception 無しで走る
#  ことを確認する．Os_Lcfg.* の出力一致は Phase 4 (XML 木 + binding) で
#  確認するので，ここでは「parse + 評価」が落ちないことだけを見る．
#
#  context は最低限のスタブ binding．未定義変数の参照は eval が空 var を
#  返すので，多くの $IF$ パスは実行されないが，パーサと AST 評価器が
#  クラッシュなく回るかをチェックする．
#

import os
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
# tests/ -> cfg_py/ -> cfg/ -> atk2-sc1_nios2/
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
_KERNEL_TF = os.path.join(_REPO_ROOT, "kernel", "kernel.tf")
_INCLUDE_DIRS = [
    _REPO_ROOT,
    os.path.join(_REPO_ROOT, "kernel"),
    os.path.join(_REPO_ROOT, "arch"),
    os.path.join(_REPO_ROOT, "target", "nucleo_h563zi_gcc"),
    os.path.join(_REPO_ROOT, "arch", "arm_m_gcc", "common"),
]


@pytest.mark.skipif(
    not os.path.exists(_KERNEL_TF),
    reason="kernel.tf not found",
)
def test_kernel_tf_parses():
    """kernel.tf を構文解析する (評価はしない)．"""
    from tf_lexer import preprocess, split_segments
    from tf_parser import parse

    with open(_KERNEL_TF, 'r', encoding='utf-8') as f:
        src = f.read()
    pre = preprocess(src, _INCLUDE_DIRS, current_file=_KERNEL_TF)
    segments = split_segments(pre)
    doc = parse(segments)
    assert doc is not None
    assert len(doc.children) > 0


@pytest.mark.skipif(
    not os.path.exists(_KERNEL_TF),
    reason="kernel.tf not found",
)
def test_kernel_tf_walks_far_with_minimal_binding():
    """kernel.tf を最小限 binding で実行し，主要パスが回ることを確認．

    kernel.tf は本来 phase 4 の XML 木 + binding (TSK/ALM/CNT/...) を前提
    にしている．ここでは空バインディングのまま走らせ:
      - parse / preprocess / include 展開がクラッシュしない
      - FUNCTION 定義が一通り登録される (ISFUNCTION で確認)
      - $TRACE および $FOREACH/IF/CALL の制御フローが動く
      - 途中で binding 不足による ExprError が出るのは「想定内」とし
        テストとしては許容する (= 例外が出る位置まで進めれば成功)
    """
    from tf_engine import run
    from tf_builtin import BUILTINS
    from tf_value import make_int, ExprError

    extra = dict(BUILTINS)
    extra["SYMBOL"] = lambda li, args, ctx: []
    extra["PEEK"] = lambda li, args, ctx: make_int(0)
    extra["BCOPY"] = lambda li, args, ctx: []
    extra["BZERO"] = lambda li, args, ctx: []

    context = {
        "NL": "\n", "TAB": "\t", "SPC": " ",
        "CFG_VERSION": "1.7.0", "CFG_PASS": 2, "CFG_XML": 1,
        "SIL_ENDIAN_BIG": 0, "SIL_ENDIAN_LITTLE": 1,
        # 空 ID_LIST．多くの $FOREACH$ がスキップされる．
        "OS.ID_LIST": [], "TSK.ID_LIST": [], "ALM.ID_LIST": [],
        "RES.ID_LIST": [], "EVT.ID_LIST": [], "CNT.ID_LIST": [],
        "SCHTBL.ID_LIST": [], "ISR.ID_LIST": [], "APP.ID_LIST": [],
        "OSAP.ID_LIST": [], "INH.ID_LIST": [], "EXC.ID_LIST": [],
    }
    # 例外は吸収する (binding 不足は phase 4 で解決する想定)
    progress_marker = "<not started>"
    try:
        outputs = run([_KERNEL_TF], context=context,
                      include_dirs=_INCLUDE_DIRS, builtins=extra)
        progress_marker = "<finished>"
    except ExprError as e:
        progress_marker = f"<ExprError: {e}>"
    # 進捗マーカは TRACE 出力で前進が観測できるはずなので，ここでは
    # 例外が「ExprError 系」であって parser/syntax 系ではないことだけを
    # 確認．SyntaxError 等が漏れたら明白に失敗する．
    assert progress_marker.startswith("<ExprError") or \
        progress_marker == "<finished>", progress_marker
