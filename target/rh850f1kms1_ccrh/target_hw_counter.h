/*
 *  TOPPERS ATK2
 *      Toyohashi Open Platform for Embedded Real-Time Systems
 *      Automotive Kernel Version 2
 *
 *  Copyright (C) 2014-2016 by Center for Embedded Computing Systems
 *              Graduate School of Information Science, Nagoya Univ., JAPAN
 *  Copyright (C) 2014 by FUJI SOFT INCORPORATED, JAPAN
 *  Copyright (C) 2014 by Spansion LLC, USA
 *  Copyright (C) 2014 by NEC Communication Systems, Ltd., JAPAN
 *  Copyright (C) 2014 by Panasonic Advanced Technology Development Co., Ltd., JAPAN
 *  Copyright (C) 2014 by Renesas Electronics Corporation, JAPAN
 *  Copyright (C) 2014 by Sunny Giken Inc., JAPAN
 *  Copyright (C) 2014 by TOSHIBA CORPORATION, JAPAN
 *  Copyright (C) 2014 by Witz Corporation, JAPAN
 *
 *  上記著作権者は，以下の(1)～(4)の条件を満たす場合に限り，本ソフトウェ
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
 *
 *  $Id: target_hw_counter.h 911 2020-07-24 06:25:32Z nces-mtakada $
 */

/*
 *		ハードウェアカウンタのターゲット依存定義（RH850/F1KM-S1用）
 */

#ifndef TOPPERS_TARGET_HW_COUNTER_H
#define TOPPERS_TARGET_HW_COUNTER_H

/*
 *  使用するタイマーのユニット番号と差分タイマと現在値タイマのチャネル
 */
#define HWC_DTIM_UNIT  0  /* 0 or 1 */
#define HWC_DTIM_ID    14
#define HWC_CTIM_UNIT  0  /* 0 or 1 */
#define HWC_CTIM_ID    15

/*
 *  割込み番号
 */
#if (HWC_DTIM_UNIT == 0)
#define HWC_DTIM_INTNO  (TAUB0I0_INTNO + HWC_DTIM_ID)
#elif (HWC_DTIM_UNIT == 1)
#define HWC_DTIM_INTNO  (TAUB1I0_INTNO + HWC_DTIM_ID)
#else /*(HWC_DTIM_UNIT == 1) */
#error define HWC_UNIT  0 or 1.
#endif /* (HWC_DTIM_UNIT == 0) */

/*
 *  割込み優先度
 */
#define HWC_DTIM_INTPRI  1

/*
 *  タイマクロック周波数（Hz）（625kHz = PCLK(40MHz)/64）
 */
#define TIMER_CLOCK_HZ		((uint32) 625000)

/*
 *  TAUB関連レジスタ
 *
 *  TAUB のチャネルデータ／カウンタレジスタは 16bit 幅である．
 */
#define TAUB_BASE(n)	((uint32) (0xffe30000U + (n * 0x1000U)))
#define TAUBTPS(n)		(TAUB_BASE(n) + 0x240U)
#define TAUBCDR(n, ch)	(TAUB_BASE(n) + (ch * 0x04U))
#define TAUBCNT(n, ch)	(TAUB_BASE(n) + 0x80U + (ch * 0x04U))
#define TAUBCMOR(n, ch)	(TAUB_BASE(n) + 0x200U + (ch * 0x04U))
#define TAUBCMUR(n, ch)	(TAUB_BASE(n) + 0xC0U + (ch * 0x04U))
#define TAUBTS(n)		(TAUB_BASE(n) + 0x1C4U)
#define TAUBTT(n)		(TAUB_BASE(n) + 0x1C8U)

#define MCU_TAUB_MASK_CK0				((uint16) 0xfff0)
#define MCU_TAUB_CK0_0					((uint16) 0x0006) /* 64分周 */
#define MCU_TAUB00_CMOR					((uint16) 0x0000)
#define MCU_TAUB00_CMUR					((uint8) 0x01)

/*
 *  TAUBのユニット番号とチャネルから入力割込み番号への変換
 */
#define TAUB_INTNO(n, ch)	(n == 0)? ((uint32) ((TAUB0I0_INTNO + ch))) : ((uint32) (TAUB1I0_INTNO + ch))

/*
 *  割込み要求のクリア
 */
LOCAL_INLINE void
HwcounterClearInterrupt(uint32 intno)
{
	/* 割込み制御レジスタ */
	uint32 eic_address = EIC_ADDRESS(intno);

	/* 割込み要求ビットのクリア */
	sil_wrh_mem((void *) eic_address,
				sil_reh_mem((void *) eic_address) & ~EIRFn);
}

/*
 *  割込み禁止／許可設定
 */
LOCAL_INLINE void
HwcounterDisableInterrupt(uint32 intno)
{
	/* 割込み制御レジスタ */
	uint32 eic_address = EIC_ADDRESS(intno);

	/* 割込みマスクビットのセット */
	sil_wrh_mem((void *) eic_address,
				sil_reh_mem((void *) eic_address) | EIMKn);
}

LOCAL_INLINE void
HwcounterEnableInterrupt(uint32 intno)
{
	/* 割込み制御レジスタ */
	uint32 eic_address = EIC_ADDRESS(intno);

	/* 割込みマスクビットのセット */
	sil_wrh_mem((void *) eic_address,
				sil_reh_mem((void *) eic_address) & ~EIMKn);
}

/*
 *  TAUBn タイマの動作開始／停止処理
 */
LOCAL_INLINE void
SetTimerStartTAUB(uint8 n, uint8 ch)
{
	/* タイマ開始処理 */
	sil_wrh_mem((void *) TAUBTS(n), (1 << ch));
}

LOCAL_INLINE void
SetTimerStopTAUB(uint8 n, uint8 ch)
{
	/* タイマ停止処理 */
	sil_wrh_mem((void *) TAUBTT(n), (1 << ch));
}

/*
 *  TAUBnハードウェアカウンタ現在ティック値取得
 */
LOCAL_INLINE TickType
GetCurrentTimeTAUB(uint8 n, uint8 ch, TickType maxval)
{
	TickType	count;
	TickType	curr_time = 0U;

	count = sil_reh_mem((void *) (TAUBCNT(n, ch)));

	/* ダウンカウンタの為，現在チック値に変換 */
	curr_time = maxval - count;
	curr_time = (curr_time % maxval);

	return(curr_time);
}


/* MAIN_HW_COUNTERの定義 */
extern void init_hwcounter_MAIN_HW_COUNTER(TickType maxval, TimeType nspertick);
extern void start_hwcounter_MAIN_HW_COUNTER(void);
extern void stop_hwcounter_MAIN_HW_COUNTER(void);
extern void set_hwcounter_MAIN_HW_COUNTER(TickType exprtick);
extern TickType get_hwcounter_MAIN_HW_COUNTER(void);
extern void cancel_hwcounter_MAIN_HW_COUNTER(void);
extern void trigger_hwcounter_MAIN_HW_COUNTER(void);
extern void int_clear_hwcounter_MAIN_HW_COUNTER(void);
extern void int_cancel_hwcounter_MAIN_HW_COUNTER(void);
extern void increment_hwcounter_MAIN_HW_COUNTER(void);

/*
 *  10msと一致するティック値(サンプルプログラム用)
 */
#define TICK_FOR_10MS	TIMER_CLOCK_HZ / 100

#endif /* TOPPERS_TARGET_HW_COUNTER_H */
