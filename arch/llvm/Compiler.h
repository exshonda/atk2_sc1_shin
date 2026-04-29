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
 *      コンパイラ依存定義 (ARM LLVM / clang 用)
 *
 *  ATK2 で使用する AUTOSAR Compiler 抽象化マクロ (FUNC, P2VAR, INLINE,
 *  Asm, NoReturn 等) は，clang の GCC 互換属性 (`__inline__`,
 *  `__asm__ volatile`, `__attribute__((__noreturn__))`) でそのまま動作
 *  するため，本層は arch/gcc/Compiler.h をそのまま流用する．LLVM 固有
 *  の差異が必要になった場合は本ファイルで再定義してオーバライドする．
 *
 *  「arch/gcc/ を LLVM ビルドからも参照する」運用は arch/gcc/ という
 *  ディレクトリ名が GCC ビルド専用と誤読させるため，本ディレクトリ
 *  arch/llvm/ を経由する設計とした．
 */

#ifndef TOPPERS_COMPILER_H_LLVM_BRIDGE
#define TOPPERS_COMPILER_H_LLVM_BRIDGE

/*
 *  arch/gcc/Compiler.h の内容をそのまま取込．
 *  下記の相対インクルードは MANIFEST 配下構造 (arch/gcc/, arch/llvm/ が
 *  兄弟関係) を前提とする．
 */
#include "../gcc/Compiler.h"

#endif /* TOPPERS_COMPILER_H_LLVM_BRIDGE */
