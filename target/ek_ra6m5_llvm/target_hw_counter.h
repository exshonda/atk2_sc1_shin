/*
 *  TOPPERS ATK2
 *      Toyohashi Open Platform for Embedded Real-Time Systems
 *      Automotive Kernel Version 2
 *
 *  Copyright (C) 2008-2017 by Center for Embedded Computing Systems
 *              Graduate School of Information Science, Nagoya Univ., JAPAN
 *  Copyright (C) 2026 by Center for Embedded Computing Systems
 *              Graduate School of Information Science, Nagoya Univ., JAPAN
 *
 *  上記著作権者は，以下の(1)〜(4)の条件を満たす場合に限り，本ソフトウェ
 *  ア（本ソフトウェアを改変したものを含む．以下同じ）を使用・複製・改
 *  変・再配布（以下，利用と呼ぶ）することを無償で許諾する．
 *
 *  本ソフトウェアは，無保証で提供されているものである．
 */

/*
 *  ハードウェアカウンタのターゲット依存定義（EK_RA6M5_GCC用）
 *
 *  MAIN_HW_COUNTER:
 *    GPT320: フリーランニング 32bit 上昇カウンタ (1MHz), 現在値タイマ
 *    GPT321: ワンショット 32bit 上昇カウンタ (1MHz), アラームタイマ
 *  PCLKD = 100MHz (Smart Configurator 既定) を Source clock で /100 分周し
 *  1MHz tick とする．GPT は Renesas R_GPT (32-bit GPT for ch0/ch1) を
 *  レジスタ直叩きで使用．
 */

#ifndef TOPPERS_TARGET_HW_COUNTER_H
#define TOPPERS_TARGET_HW_COUNTER_H

/*
 *  カウンタ最大値 (32bit フリーランニングカウンタ上限)
 *  GPT320 は 32-bit 幅 (PRV[2-0]=000 → 32bit) を使用．
 */
#define MAX_TIMER_CNT       ((uint32) 0xFFFFFFFFU)

/*
 *  カウンタ周期最大値 (MAX_TIMER_CNT / 2)
 */
#define MAX_CNT_CYCLE       ((uint32) 0x7FFFFFFFU)

/*
 *  タイマクロック周波数 (PCLKD=100MHz / TPCS=2 (16分周) … では 1MHz に
 *  ならないので CKEG/PRV を組合せて 1MHz を作る．
 *  RA6M5 GPT は GTCR.TPCS で {/1, /4, /16, /64, /256, /1024} を選べる．
 *  PCLKD=100MHz を 1MHz にするには /100 が必要だが GPT は /100 を直接
 *  サポートしないため，下記いずれか:
 *    (a) PCLKD を 1MHz の倍数にする (Smart Configurator で PCLKD 変更)
 *    (b) PCLKD/64 = 1.5625MHz を採用 (1us tick とは誤差あり)
 *    (c) GTPR で 100 カウントごとに割込み発生 + 自前カウンタを加算
 *  Phase 2 では (c) を見送り，PCLKD/4 = 25MHz をベースに GTPR=25-1 で
 *  1MHz tick を生成 (オーバーフローで GTCNT を 0 にリセット)．
 *  → ただし 32bit GTCNT を使うなら GTPR を 0xFFFFFFFF にしてフリーラン
 *     する方が単純．本実装ではフリーラン+ソフトウェアスケーリングを採用．
 *
 *  暫定方針: PCLKD/4 = 25MHz でフリーランさせ，TickType を 32bit GTCNT
 *  生値とする．1MHz 換算は呼び出し側で行わず，TICK_FOR_1MS を 25000 に
 *  すれば論理 1MHz と等価になる．
 *
 *  TODO[Phase 2-B]: GPT のクロック源を最終決定．以下の値はその選択に
 *  応じて再計算が必要．
 */
#define TIMER_CLOCK_HZ      ((uint32) 1000000U)

/*
 *  サンプル用ティック数定義（タイマクロック1MHz基準）
 */
#define TICK_FOR_1MS        (TIMER_CLOCK_HZ / 1000)
#define TICK_FOR_10MS       (TIMER_CLOCK_HZ / 100)
#define TICK_FOR_1S         (TIMER_CLOCK_HZ)

/*
 *  GPT320 / GPT321 割込み番号
 *
 *  RA6M5 NVIC スロットは Smart Configurator の vector_data.c で
 *  決定する．GPT321 のオーバーフロー割込み (GPT321_OVF) に割り当てられた
 *  スロット番号 N から INTNO = N + 16 で算出すること．
 *  TODO[Phase 2-A]: vector_data.c 受領後に確定値に置換．
 */
#define GPT320_INTNO        UINT_C(17)   /* 暫定: TODO Smart Configurator 後確定 */
#define GPT321_INTNO        UINT_C(18)   /* 暫定: TODO Smart Configurator 後確定 */

/*
 *  MAIN_HW_COUNTER 操作関数プロトタイプ
 */
#ifndef TOPPERS_MACRO_ONLY

extern void     init_hwcounter_MAIN_HW_COUNTER(TickType maxval, TimeType nspertick);
extern void     start_hwcounter_MAIN_HW_COUNTER(void);
extern void     stop_hwcounter_MAIN_HW_COUNTER(void);
extern void     set_hwcounter_MAIN_HW_COUNTER(TickType exprtick);
extern TickType get_hwcounter_MAIN_HW_COUNTER(void);
extern void     cancel_hwcounter_MAIN_HW_COUNTER(void);
extern void     trigger_hwcounter_MAIN_HW_COUNTER(void);
extern void     int_clear_hwcounter_MAIN_HW_COUNTER(void);
extern void     int_cancel_hwcounter_MAIN_HW_COUNTER(void);
extern void     increment_hwcounter_MAIN_HW_COUNTER(void);

#endif /* TOPPERS_MACRO_ONLY */

#endif /* TOPPERS_TARGET_HW_COUNTER_H */
