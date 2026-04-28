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
 *      シリアルI/Oデバイス（SIO）ドライバ（EK_RA6M5用）
 *
 *  SCI9 を target_config.c で直接初期化しているため，ここでは
 *  sample1 が要求する INTNO_SIO / INTPRI_SIO のみを定義する．
 */

#ifndef TOPPERS_TARGET_SERIAL_H
#define TOPPERS_TARGET_SERIAL_H

#include "ek_ra6m5.h"

/*
 *  SCI9 受信割込みのベクタ番号 / 割込み優先度
 *
 *  RA6M5 の NVIC スロット番号は Smart Configurator (vector_data.c) が
 *  決定する．Phase 2-A 完了後，生成された vector_data.c の
 *  g_interrupt_event_link_select[] で SCI9_RXI に割り当てられたスロット
 *  番号 N を確認し，下記 INTNO_SIO = N + 16 に修正すること．
 *  本値は暫定．
 *  TODO[Phase 2-A]: vector_data.c 受領後に確定値に置換し，
 *                   target_serial.arxml の <VALUE> も合わせること．
 */
#define INTNO_SIO       UINT_C(16)   /* IRQ0 暫定 */
#define INTPRI_SIO      UINT_C(2)

#ifndef TOPPERS_MACRO_ONLY

/*
 *  H/W シリアルの初期化／終了処理
 *  target_config.c で定義．sysmod/serial.c の InitSerial / TermSerial
 *  から呼ばれる．
 */
extern void InitHwSerial(void);
extern void TermHwSerial(void);

#endif /* TOPPERS_MACRO_ONLY */

#endif /* TOPPERS_TARGET_SERIAL_H */
