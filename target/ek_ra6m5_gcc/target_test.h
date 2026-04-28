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
 *  テストプログラムのターゲット依存定義（EK_RA6M5用）
 */

#ifndef TOPPERS_TARGET_TEST_H
#define TOPPERS_TARGET_TEST_H

/*
 *  sample1で使用するCPU例外の発生方法
 *  ARM Cortex-M33: UDF（未定義命令）で UsageFault を発生させる
 */
#define RAISE_CPU_EXCEPTION	Asm("udf #0")

/*
 *  sample1で使用するアラームの周期
 *  タイマクロック1MHz × 1,000,000 = 1秒
 */
#define COUNTER_MIN_CYCLE	((uint32) 1000000)

#endif /* TOPPERS_TARGET_TEST_H */
