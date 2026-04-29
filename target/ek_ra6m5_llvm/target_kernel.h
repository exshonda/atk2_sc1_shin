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
 *  TMIN_INTNO / TMAX_INTNO / TBITW_IPRI は arch/arm_m_gcc/common/prc_config.h
 *  で定義される (TMIN_INTNO=16, TMAX_INTNO=147, TBITW_IPRI=4)．
 *
 *  RA6M5 の NVIC スロット数は 96 (BSP_ICU_VECTOR_NUM_ENTRIES) で
 *  IRQ0..IRQ95 → INTNO 16..111 の範囲しか持たないが，prc_config.h は
 *  「arch/arm_m_gcc/common は変更しない」方針のもと変更不可，かつ #ifndef
 *  ガードが無いため target 層からの単純な #undef/#define では上書きできない．
 *
 *  TMAX_INTNO=147 は H5 から流用された上位互換値．VALID_INTNO の範囲外
 *  検出が IRQ95..IRQ131 の範囲で甘くなる (実害なし，Smart Configurator が
 *  IRQ95 を超える値を割り当てない)．Phase 4 で共通部に
 *  `#ifndef TMAX_INTNO` ガードを足す等の改善を別途検討．
 *
 *  TODO[Phase 4]: prc_config.h に TMAX_INTNO の override 機構を入れて
 *                 ここで UINT_C(111) に絞り込む．
 */
#include "prc_kernel.h"

#endif /* TOPPERS_TARGET_KERNEL_H */
