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
 *  ターゲット依存モジュール（EK_RA6M5_LLVM用）
 *
 *  カーネルのターゲット依存部のインクルードファイル
 *  kernel_impl.h のターゲット依存部の位置付けとなる
 */

#ifndef TOPPERS_TARGET_CONFIG_H
#define TOPPERS_TARGET_CONFIG_H

/*
 *  ボード依存ヘッダのインクルード
 */
#include "ek_ra6m5.h"

#ifndef TOPPERS_MACRO_ONLY

/*
 *  ハードウェアの初期化（クロック, 周辺回路）
 */
extern void target_hardware_initialize(void);

/*
 *  ターゲットシステム依存の初期化
 */
extern void target_initialize(void);

/*
 *  ターゲットシステムの終了
 */
extern void target_exit(void) NoReturn;

/*
 *  文字列の出力
 */
extern void target_fput_str(const char8 *c);

/*
 *  特定の割込み要求ラインの有効/無効を制御可能かを調べる処理
 */
extern boolean target_is_int_controllable(InterruptNumberType intno);

#endif /* TOPPERS_MACRO_ONLY */

/*
 *  チップ依存モジュール（RA6M5 FSP用）
 */
#include "chip_config.h"

#endif /* TOPPERS_TARGET_CONFIG_H */
