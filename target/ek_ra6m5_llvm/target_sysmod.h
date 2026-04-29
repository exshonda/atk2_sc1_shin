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
 *  システムモジュールのターゲット依存部（EK_RA6M5_LLVM用）
 */

#ifndef TOPPERS_TARGET_SYSMOD_H
#define TOPPERS_TARGET_SYSMOD_H

#include "prc_sil.h"
#include "ek_ra6m5.h"          /* TARGET_NAME */

/*
 *  システムログの低レベル出力のための文字出力
 */
extern void target_fput_log(char8 c);

#endif /* TOPPERS_TARGET_SYSMOD_H */
