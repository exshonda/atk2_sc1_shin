$
$  TOPPERS ATK2
$      Toyohashi Open Platform for Embedded Real-Time Systems
$      Automotive Kernel Version 2
$
$  Copyright (C) 2008-2017 by Center for Embedded Computing Systems
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
$   パス2のチップ依存テンプレート (STM32H5xx)
$
$   prc.tf より前に target.tf から取り込まれることで，アーキ層 (prc.tf)
$   と kernel.tf 共通部にチップ固有値を渡す．
$

$
$  有効な割込み番号
$  STM32H563ZI: IRQ0 (例外16) 〜 IRQ131 (例外147)
$
$INTNO_VALID = { 16,17,...,147 }$

$
$  制御可能な割込み番号
$
$INTNO_CONTROLLABLE = INTNO_VALID$

$
$  割込み優先度の個数 (4ビット: 16段階)
$
$TNUM_INTPRI = 16$

$
$  CRE_ISR2 で使用できる割込み番号
$
$INTNO_CREISR2_VALID = INTNO_VALID$
