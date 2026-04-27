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
 *
 *  本ソフトウェアは，無保証で提供されているものである．
 */

/*
 *		シリアルI/Oデバイス（SIO）ドライバ（NUCLEO_H563ZI用）
 *
 *  USART3 を target_config.c で直接初期化しているため、ここでは
 *  sample1 が要求する INTNO_SIO / INTPRI_SIO のみを定義する．
 */

#ifndef TOPPERS_TARGET_SERIAL_H
#define TOPPERS_TARGET_SERIAL_H

#include "nucleo_h563zi.h"

/*
 *  USART3 の割込みハンドラのベクタ番号 / 割込み優先度
 *  USART3_IRQn=60, INTNO=60+16=76
 */
#define INTNO_SIO	UINT_C(76)
#define INTPRI_SIO	UINT_C(2)

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
