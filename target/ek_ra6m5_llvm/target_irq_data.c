/*
 *  TOPPERS ATK2
 *      Toyohashi Open Platform for Embedded Real-Time Systems
 *      Automotive Kernel Version 2
 *
 *  Copyright (C) 2026 by Center for Embedded Computing Systems
 *              Graduate School of Information Science, Nagoya Univ., JAPAN
 *
 *  本ソフトウェアは，無保証で提供されているものである．
 */

/*
 *  IELSR (Interrupt Event Link Select Register) テーブル抽出版
 *
 *  Smart Configurator 生成 fsp/ra_gen/vector_data.c には次の 2 シンボルが
 *  同居する:
 *    - g_vector_table[]                : ARM Cortex-M ベクタテーブル
 *      → ATK2 cfg pass2 が生成する kernel_vector_table と衝突．かつ
 *        FSP の `gpt_counter_overflow_isr` 等 r_sci_uart / r_gpt の
 *        ISR シンボルへの参照を含み，それらをリンクしない本ポートでは
 *        未定義シンボル参照になる．
 *    - g_interrupt_event_link_select[] : ICU.IELSR テーブル
 *      → 本ポートで必須．`R_ICU->IELSR[i] = g_interrupt_event_link_select[i]`
 *        により NVIC スロットと FSP イベントの紐付けを設定する．
 *
 *  Phase 2-B 設計判断 (a) に従い，vector_data.c をビルド対象から外し
 *  (g_vector_table 衝突回避)，本ファイルで g_interrupt_event_link_select
 *  のみ抽出してリンクする．
 *
 *  configuration.xml の Stack 構成および Properties → Interrupts の
 *  Priority 設定が変わったら，fsp/ra_gen/vector_data.c の
 *  g_interrupt_event_link_select[] 部分を本ファイルに転記し直す
 *  (target_serial.h INTNO_SIO / target_hw_counter.h GPT321_INTNO とも
 *  一致させる)．
 */

#include "bsp_api.h"

#if BSP_FEATURE_ICU_HAS_IELSR
const bsp_interrupt_event_t g_interrupt_event_link_select[BSP_ICU_VECTOR_NUM_ENTRIES] =
{
    [0] = BSP_PRV_VECT_ENUM(EVENT_GPT1_COUNTER_OVERFLOW, GROUP0), /* GPT321 OVF (Overflow)        — INTNO 16 */
    [1] = BSP_PRV_VECT_ENUM(EVENT_SCI7_RXI,              GROUP1), /* SCI7 RXI  (Receive Full)     — INTNO 17 */
    [2] = BSP_PRV_VECT_ENUM(EVENT_SCI7_TXI,              GROUP2), /* SCI7 TXI  (Transmit Empty)   — INTNO 18 (送信ポーリングのため未使用) */
    [3] = BSP_PRV_VECT_ENUM(EVENT_SCI7_TEI,              GROUP3), /* SCI7 TEI  (Transmit End)     — INTNO 19 (未使用) */
    [4] = BSP_PRV_VECT_ENUM(EVENT_SCI7_ERI,              GROUP4), /* SCI7 ERI  (Receive Error)    — INTNO 20 (未使用) */
};
#endif
