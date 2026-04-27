/*
 *  TOPPERS ATK2
 *      Toyohashi Open Platform for Embedded Real-Time Systems
 *      Automotive Kernel Version 2
 *
 *  Copyright (C) 2008-2017 by Center for Embedded Computing Systems
 *              Graduate School of Information Science, Nagoya Univ., JAPAN
 *
 *  上記著作権者は，以下の(1)〜(4)の条件を満たす場合に限り，本ソフトウェ
 *  ア（本ソフトウェアを改変したものを含む．以下同じ）を使用・複製・改
 *  変・再配布（以下，利用と呼ぶ）することを無償で許諾する．
 *  (1) 本ソフトウェアをソースコードの形で利用する場合には，上記の著作
 *      権表示，この利用条件および下記の無保証規定が，そのままの形でソー
 *      スコード中に含まれていること．
 *  (2) 本ソフトウェアを，ライブラリ形式など，他のソフトウェア開発に使
 *      用できる形で再配布する場合には，再配布に伴うドキュメント（利用
 *      者マニュアルなど）に，上記の著作権表示，この利用条件および下記
 *      の無保証規定を掲載すること．
 *  (3) 本ソフトウェアを，機器に組み込むなど，他のソフトウェア開発に使
 *      用できない形で再配布する場合には，次のいずれかの条件を満たすこ
 *      と．
 *    (a) 再配布に伴うドキュメント（利用者マニュアルなど）に，上記の著
 *        作権表示，この利用条件および下記の無保証規定を掲載すること．
 *    (b) 再配布の形態を，別に定める方法によって，TOPPERSプロジェクトに
 *        報告すること．
 *  (4) 本ソフトウェアの利用により直接的または間接的に生じるいかなる損
 *      害からも，上記著作権者およびTOPPERSプロジェクトを免責すること．
 *      また，本ソフトウェアのユーザまたはエンドユーザからのいかなる理
 *      由に基づく請求からも，上記著作権者およびTOPPERSプロジェクトを
 *      免責すること．
 *
 *  本ソフトウェアは，AUTOSAR（AUTomotive Open System ARchitecture）仕
 *  様に基づいている．上記の許諾は，AUTOSARの知的財産権を許諾するもので
 *  はない．AUTOSARは，AUTOSAR仕様に基づいたソフトウェアを商用目的で利
 *  用する者に対して，AUTOSARパートナーになることを求めている．
 *
 *  本ソフトウェアは，無保証で提供されているものである．上記著作権者お
 *  よびTOPPERSプロジェクトは，本ソフトウェアに関して，特定の使用目的
 *  に対する適合性も含めて，いかなる保証も行わない．また，本ソフトウェ
 *  アの利用により直接的または間接的に生じたいかなる損害に関しても，そ
 *  の責任を負わない．
 */

/*
 *  ハードウェアカウンタのターゲット依存定義（NUCLEO_H563ZI_GCC用）
 *
 *  MAIN_HW_COUNTER: TIM2 (フリーランニング) + TIM5 (ワンショットアラーム)
 *    TIM2: 32bit 上昇カウンタ, 1MHz (SYSCLK/250), 割込みなし
 *    TIM5: 32bit 上昇カウンタ, 1MHz, OPM=1, 割込みあり (TIM5_IRQn)
 */

#ifndef TOPPERS_TARGET_HW_COUNTER_H
#define TOPPERS_TARGET_HW_COUNTER_H

/*
 *  カウンタ最大値 (32bit フリーランニングカウンタ上限)
 */
#define MAX_TIMER_CNT       ((uint32) 0xFFFFFFFFU)

/*
 *  カウンタ周期最大値 (MAX_TIMER_CNT / 2)
 */
#define MAX_CNT_CYCLE       ((uint32) 0x7FFFFFFFU)

/*
 *  タイマクロック周波数 (SYSCLK=250MHz, PSC=249 → 1MHz)
 */
#define TIMER_CLOCK_HZ      ((uint32) 1000000U)

/*
 *  サンプル用ティック数定義（タイマクロック1MHz基準）
 */
#define TICK_FOR_1MS        (TIMER_CLOCK_HZ / 1000)
#define TICK_FOR_10MS       (TIMER_CLOCK_HZ / 100)
#define TICK_FOR_1S         (TIMER_CLOCK_HZ)

/*
 *  TIM2 割込み番号 (フリーランニング, 割込み未使用)
 *  TIM2_IRQn = 45 → INTNO = 45 + 16 = 61
 */
#define TIM2_INTNO          UINT_C(61)

/*
 *  TIM5 割込み番号 (アラーム用, CATEGORY_2 ISR)
 *  TIM5_IRQn = 48 → INTNO = 48 + 16 = 64
 */
#define TIM5_INTNO          UINT_C(64)

/*
 *  タイマクロック分周比 (250MHz → 1MHz)
 */
#define TIMER_PSC_VALUE     (249U)

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
