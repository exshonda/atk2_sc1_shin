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
 *  Os.h のターゲット依存部（EK_RA6M5_GCC用）
 *
 *  このインクルードファイルは，Os.h でインクルードされる
 */

#ifndef TOPPERS_TARGET_KERNEL_H
#define TOPPERS_TARGET_KERNEL_H

/*
 *  タスクスタックサイズの最小値
 */
#define TARGET_MIN_STKSZ    256U

/*
 *  非タスクコンテキスト用スタック最小値
 */
#define MINIMUM_OSTKSZ      512U

/*
 *  各スタックサイズのデフォルト値
 */
#define DEFAULT_TASKSTKSZ   (1024U)     /* 1KB */
#define DEFAULT_ISRSTKSZ    (1024U)     /* 1KB */
#define DEFAULT_HOOKSTKSZ   (1024U)     /* 1KB */
#define DEFAULT_OSSTKSZ     (8192U)     /* 8KB */

/*
 *  プロセッサ共通の定義
 *
 *  TMIN_INTNO / TMAX_INTNO / TNUM_INT / TBITW_IPRI は
 *  arch/arm_m_llvm/ra_fsp/chip_config.h で定義される
 *  (TMIN_INTNO=16, TMAX_INTNO=111, TNUM_INT=96, TBITW_IPRI=4)．
 */
#include "prc_kernel.h"

#endif /* TOPPERS_TARGET_KERNEL_H */
