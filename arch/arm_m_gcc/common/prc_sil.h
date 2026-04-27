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
 *  (1) 本ソフトウェアをソースコードの形で利用する場合には，上記の著作
 *      権表示，この利用条件および下記の無保証規定が，そのままの形でソー
 *      スコード中に含まれていること．
 *  (2) 本ソフトウェアを，ライブラリ形式など，他のソフトウェア開発に使
 *      用できる形で再配布する場合には，再配布に伴うドキュメント（利用
 *      者マニュアルなど）に，上記の著作権表示，この利用条件および下記
 *      の無保証規定を掲載すること．
 *  (3) 本ソフトウェアを，機器に組み込むなど，他のソフトウェア開発に使
 *      用できない形で再配布する場合には，次のいずれかの条件を満たすこ
 *      と．
 *    (a) 再配布に伴うドキュメント（利用者マニュアルなど）に，上記の著
 *        作権表示，この利用条件および下記の無保証規定を掲載すること．
 *    (b) 再配布の形態を，別に定める方法によって，TOPPERSプロジェクトに
 *        報告すること．
 *  (4) 本ソフトウェアの利用により直接的または間接的に生じるいかなる損
 *      害からも，上記著作権者およびTOPPERSプロジェクトを免責すること．
 *      また，本ソフトウェアのユーザまたはエンドユーザからのいかなる理
 *      由に基づく請求からも，上記著作権者およびTOPPERSプロジェクトを
 *      免責すること．
 *
 *  本ソフトウェアは，AUTOSAR（AUTomotive Open System ARchitecture）仕
 *  様に基づいている．上記の許諾は，AUTOSARの知的財産権を許諾するもので
 *  はない．AUTOSARは，AUTOSAR仕様に基づいたソフトウェアを商用目的で利
 *  用する者に対して，AUTOSARパートナーになることを求めている．
 *
 *  本ソフトウェアは，無保証で提供されているものである．上記著作権者お
 *  よびTOPPERSプロジェクトは，本ソフトウェアに関して，特定の使用目的
 *  に対する適合性も含めて，いかなる保証も行わない．また，本ソフトウェ
 *  アの利用により直接的または間接的に生じたいかなる損害に関しても，そ
 *  の責任を負わない．
 */

/*
 *  メモリ及び周辺アドレスアクセスのためのプロセッサ依存部（ARM Cortex-M33用）
 */

#ifndef TOPPERS_PRC_SIL_H
#define TOPPERS_PRC_SIL_H

/*
 *  プロセッサのエンディアン（Cortex-M33はリトルエンディアン）
 */
#define SIL_ENDIAN_LITTLE

#ifndef TOPPERS_MACRO_ONLY

/*
 *  NMIを除くすべての割込みの禁止（PRIMASKを使用）
 */
LOCAL_INLINE uint32
TOPPERS_disint(void)
{
	uint32 primask;
	Asm("mrs %0, primask" : "=r" (primask));
	Asm("cpsid i" ::: "memory");
	return(primask);
}

/*
 *  割込み許可状態の復元
 */
LOCAL_INLINE void
TOPPERS_set_primask(uint32 primask)
{
	Asm("msr primask, %0" :: "r" (primask) : "memory");
}

/*
 *  全割込みロック状態の制御
 */
#define SIL_PRE_LOC      uint32 TOPPERS_primask
#define SIL_LOC_INT()    (TOPPERS_primask = TOPPERS_disint())
#define SIL_UNL_INT()    (TOPPERS_set_primask(TOPPERS_primask))

/*
 *  メモリマップドI/O 32ビット読み書き
 *  ARM Cortex-MはI/O空間とメモリ空間の区別はないが，
 *  バリアのために専用関数を用意する
 */
LOCAL_INLINE uint32
sil_rew_iop(void *mem)
{
	uint32 val;
	Asm("ldr %0, [%1]" : "=r" (val) : "r" (mem) : "memory");
	return(val);
}

LOCAL_INLINE void
sil_wrw_iop(void *mem, uint32 data)
{
	Asm("str %0, [%1]" :: "r" (data), "r" (mem) : "memory");
}

#endif /* TOPPERS_MACRO_ONLY */

#endif /* TOPPERS_PRC_SIL_H */
