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
 *  ハードウェアカウンタのターゲット依存定義（EK_RA6M5_LLVM用）
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
 *  タイマクロック周波数
 *
 *  RA6M5 GPT のプリスケーラ TPCS は {/1, /4, /16, /64, /256, /1024} の
 *  6 値しか選べないため，Smart Configurator 既定の PCLKD=100MHz から
 *  正確に 1MHz を作ることはできない．本実装では下記を採用:
 *
 *    GTCR.TPCS = /4   →  100 MHz / 4 = 25 MHz (= 40 ns / tick)
 *
 *  この選択により:
 *    - GPT の実カウンタ更新は 25 MHz (誤差なしの整数分周)
 *    - TIMER_CLOCK_HZ = 25 MHz とし，AUTOSAR の OsSecondsPerTick に
 *      4.0e-08 (= 40 ns/tick) を整合させる (target_hw_counter.arxml)
 *    - 32-bit フリーラン GTCNT の最大周期 = 0xFFFFFFFF / 25MHz ≈ 171 秒
 *    - 1ms = 25000 tick， 1秒 = 25M tick．sample1 の 5 秒ウェイトも
 *      余裕で 32-bit 範囲内 (5 × 25M = 125M < 4.29G)．
 *
 *  「1MHz 1us tick」を厳守したい場合は Smart Configurator で
 *  PCLKD を 64 MHz (or 16 MHz 等の 2 のべき倍数) に変更し
 *  TPCS=/64 (or /16) で 1MHz を作るのが望ましいが，本ポートでは
 *  既定 PCLKD=100MHz を尊重し，AUTOSAR 契約側を 25 MHz tick に
 *  揃える．
 */
#define TIMER_CLOCK_HZ      ((uint32) 25000000U)    /* PCLKD / 4 = 25 MHz */

/*
 *  サンプル用ティック数定義 (TIMER_CLOCK_HZ = 25 MHz 基準)
 *  sample1.c は TICK_FOR_1MS / TICK_FOR_10MS / TICK_FOR_1S を使う．
 */
#define TICK_FOR_1MS        (TIMER_CLOCK_HZ / 1000)     /* = 25000 */
#define TICK_FOR_10MS       (TIMER_CLOCK_HZ / 100)      /* = 250000 */
#define TICK_FOR_1S         (TIMER_CLOCK_HZ)            /* = 25000000 */

/*
 *  GPT320 / GPT321 割込み番号
 *
 *  Phase 2-A で確定した値．
 *  fsp/ra_gen/vector_data.c の g_interrupt_event_link_select[] において:
 *    [0] = BSP_PRV_VECT_ENUM(EVENT_GPT1_COUNTER_OVERFLOW, GROUP0)
 *           → GPT321 (= g_timer_alarm) OVF．スロット 0 + 16 = 16
 *  configuration.xml で GPT321 Overflow Priority=13 を設定したため，
 *  FSP が IRQ0 スロット (NVIC 優先度 0xD0) を割り当てた．
 *  target_hw_counter.arxml の OsIsrInterruptNumber も同じ値．
 *
 *  GPT320 はフリーランニングで割込み未使用 (Disabled)．INTNO は参照
 *  されないが cfg ツール都合で形式上定義．
 */
#define GPT320_INTNO        UINT_C(0)    /* 未使用 (フリーランで IRQ Disabled) */
#define GPT321_INTNO        UINT_C(16)   /* GPT321 OVF = NVIC スロット 0 + 16 */

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
