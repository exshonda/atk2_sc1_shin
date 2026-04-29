$
$  TOPPERS ATK2
$      Toyohashi Open Platform for Embedded Real-Time Systems
$      Automotive Kernel Version 2
$
$  Copyright (C) 2011-2017 by Center for Embedded Computing Systems
$              Graduate School of Information Science, Nagoya Univ., JAPAN
$  Copyright (C) 2026 by Center for Embedded Computing Systems
$              Graduate School of Information Science, Nagoya Univ., JAPAN
$
$  上記著作権者は，以下の(1)〜(4)の条件を満たす場合に限り，本ソフトウェ
$  ア（本ソフトウェアを改変したものを含む．以下同じ）を使用・複製・改
$  変・再配布（以下，利用と呼ぶ）することを無償で許諾する．
$
$  本ソフトウェアは，無保証で提供されているものである．
$

$
$     パス2のターゲット依存テンプレート（EK_RA6M5_LLVM用）
$

$
$  チップ依存テンプレートのインクルード (INTNO_VALID, TNUM_INTPRI 等)
$  arch 共通 (prc.tf) と kernel.tf に値を渡すため，prc.tf より前に
$  取込む必要がある．
$
$INCLUDE "arm_m_llvm/ra_fsp/chip.tf"$

$
$  プロセッサ依存テンプレートのインクルード
$
$INCLUDE "arm_m_gcc/common/prc.tf"$
