/*
 *  TOPPERS ATK2
 *      Toyohashi Open Platform for Embedded Real-Time Systems
 *      Automotive Kernel Version 2
 *
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
 *      コンパイラ設定 (ARM LLVM / clang 用)
 *
 *  UINT_C, offsetof 等のヘルパマクロは GCC/LLVM 共通．arch/gcc/Compiler_Cfg.h
 *  をそのまま取込．LLVM 固有の差異が必要になった場合は本ファイルで再定義
 *  してオーバライドする．
 */

#ifndef TOPPERS_COMPILER_CFG_H_LLVM_BRIDGE
#define TOPPERS_COMPILER_CFG_H_LLVM_BRIDGE

#include "../gcc/Compiler_Cfg.h"

#endif /* TOPPERS_COMPILER_CFG_H_LLVM_BRIDGE */
