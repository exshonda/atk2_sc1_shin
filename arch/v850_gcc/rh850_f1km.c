/*
 *  TOPPERS ATK2
 *      Toyohashi Open Platform for Embedded Real-Time Systems
 *      Automotive Kernel Version 2
 *
 *  Copyright (C) 2015-2019 by Center for Embedded Computing Systems
 *              Graduate School of Information Science, Nagoya Univ., JAPAN
 *  Copyright (C) 2018-2019 by CRESCO LTD., JAPAN
 *  Copyright (C) 2018-2019 by ICOMSYSTECH Co.,Ltd., JAPAN
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
 *  $Id$
 */
/*
 *		RH850/F1KM-S1のハードウェア資源の設定
 *
 *  rh850_f1k.c (RH850/F1K) をベースに，F1KM-S1 (R7F701684) の
 *  保護コマンドレジスタ構成とクロック構成に合わせたもの．
 *  F1KM-S1 はサブ発振器を持たないため EnableSubOSC() は無い．
 */

#include "kernel_impl.h"
#include "rh850_f1km.h"
#include "Os.h"
#include "prc_sil.h"

/*******************************************************************************************/
/*  Outline      : Write protected register                                                */
/*  Argument     : Register address                                                        */
/*                 Register data                                                           */
/*                 Register No                                                             */
/*  Return value : 0: write success / 1: write error                                       */
/*  Description  : Write protected register                                                */
/*                                                                                         */
/*******************************************************************************************/
static uint32
write_protected_reg(uint32 addr, uint32 data, uint8 regno)
{
	uint8			wk;
	const uint32	cmd_reg[PNO_NUM] = {
		PROTCMD0, PROTCMD1, CLMA0PCMD, CLMA1PCMD, CLMA3PCMD, PROTCMDCLMA,
		JPPCMD0, PPCMD0, PPCMD8, PPCMD9, PPCMD10, PPCMD11,
		PROTCMDCVM, FLMDPCMD
	};
	const uint32	s_reg[PNO_NUM] = {
		PROTS0, PROTS1, CLMA0PS, CLMA1PS, CLMA3PS, PROTSCLMA,
		JPPROTS0, PPROTS0, PPROTS8, PPROTS9, PPROTS10, PPROTS11,
		PROTSCVM, FLMDPS
	};
	SIL_PRE_LOC;

	if (regno >= PNO_NUM) {
		return(UC_INVALIDPARAM);
	}

	SIL_LOC_INT();
	sil_wrw_mem((void *) cmd_reg[regno], 0xA5);

	sil_wrw_mem((void *) addr, data);
	sil_wrw_mem((void *) addr, ~data);
	sil_wrw_mem((void *) addr, data);
	SIL_UNL_INT();

	wk = sil_rew_mem((void *) s_reg[regno]);
	wk &= 0x01;

	return((wk == 0) ? UC_SUCCESS : UC_PROTREGERROR);
} /* write_protected_reg */

/*******************************************************************************************/
/*  Outline      : Main Oscillator enable                                                  */
/*  Argument     : Main Cscillator frequency(Hz)                                           */
/*  Return value : 0: successfly set / 1: set error                                        */
/*  Description  : Main Oscillator register setting                                        */
/*                                                                                         */
/*******************************************************************************************/
uint32
EnableMainOSC(uint32 clk_in)
{
	uint8 ampsel;

	/* MainOSC 起動 */
	if (write_protected_reg(MOSCE, PLL_ENABLE_TRG, PNO_CtrlProt0) != UC_SUCCESS) {
		return(UC_ERROR);
	}

	if (clk_in == CLK_MHz(8)) {
		ampsel = 0x03;
	}
	else if (CLK_MHz(8) < clk_in && clk_in <= CLK_MHz(16)) {
		ampsel = 0x02;
	}
	else if (CLK_MHz(16) < clk_in && clk_in <= CLK_MHz(20)) {
		ampsel = 0x01;
	}
	else if (CLK_MHz(20) < clk_in && clk_in <= CLK_MHz(24)) {
		ampsel = 0x00;
	}
	else {
		return(UC_INVALIDPARAM);
	}

	/* 発振許可を待つ */
	while (((sil_rew_mem((void *) MOSCS)) & CLK_S_CLKEN) != CLK_S_CLKEN) {
	}

	sil_wrw_mem((void *) MOSCC, 0x00 | ampsel); /* Normal stabilization time mode */
	sil_wrw_mem((void *) MOSCST, 0x00FF);       /* stabilization time -> Max */

	/* MainOSC start */
	if (write_protected_reg(MOSCE, PLL_ENABLE_TRG, PNO_CtrlProt0) != UC_SUCCESS) {
		return(UC_ERROR);
	}

	/* Wait stabilization */
	while (((sil_rew_mem((void *) MOSCS)) & CLK_S_CLKEN) == 0) {
	}

	return(UC_SUCCESS);
} /* EnableMainOSC */

/*******************************************************************************************/
/*  Outline      : PLL enable                                                              */
/*  Argument     : none                                                                    */
/*  Return value : 0: successfly set / 1: set error                                        */
/*  Description  : PLL1 register setting                                                   */
/*                                                                                         */
/*******************************************************************************************/
uint32
EnablePLL(void)
{
	uint32	reg;

	/*
	 *  PLL1 の入力クロックは CKSC_PLL1IS_CTL のデフォルト (メインクロック)
	 *  をそのまま使用する．
	 */

	/* stop PLL1 */
	if (write_protected_reg(PLL1E, PLL_DISABLE_TRG, PNO_CtrlProt1) != UC_SUCCESS) {
		return(UC_ERROR);
	}

	reg = PLL1C_DEFAULT_VALUE;
	reg |= (((uint32) (PLL1C_mr - 1) << 11) | ((uint32) (PLL1C_nr - 1)));
	sil_wrw_mem((void *) PLL1C, reg);

	/* start PLL1 */
	if (write_protected_reg(PLL1E, PLL_ENABLE_TRG, PNO_CtrlProt1) != UC_SUCCESS) {
		return(UC_ERROR);
	}

	/* Wait stabilization */
	while (((sil_rew_mem((void *) PLL1S)) & CLK_S_CLKEN) == 0) {
	}

	/* Set Multiplexer[CKSC_PPLLCLK] = PPLLOUT */
	if (write_protected_reg(CKSC_PPLLCLKS_CTL, PPLLCLKSCSID_PPLLOUT,
							PNO_CtrlProt1) != UC_SUCCESS) {
		return(UC_ERROR);
	}

	return(UC_SUCCESS);
} /* EnablePLL */

/*******************************************************************************************/
/*  Outline      : Clock switcher setting                                                  */
/*  Argument     : Selector Control reginster address                                      */
/*                 Selector Status reginster address                                       */
/*                 Register No                                                             */
/*                 Select No                                                               */
/*                 Divider Control reginster address                                       */
/*                 Divider Status reginster address                                        */
/*                 divider                                                                 */
/*  Return value : 0: successfly set / 1: set error                                        */
/*  Description  : Select clock source of CKSCLK_mn                                        */
/*                                                                                         */
/*******************************************************************************************/
uint32
SetClockSelection(uint32 s_control, uint32 s_status, uint8 regno, uint16 sel,
				  uint32 d_control, uint32 d_status, uint8 divider)
{
	/* Set Selector */
	if (write_protected_reg(s_control, sel, regno) != UC_SUCCESS) {
		return(UC_ERROR);
	}

	/* Set Divider */
	if (d_control != 0) {
		if (write_protected_reg(d_control, divider, regno) != UC_SUCCESS) {
			return(UC_ERROR);
		}
	}

	/* Wait untile enable */
	while (sil_rew_mem((void *) s_control) != sil_rew_mem((void *) s_status)) {
	}

	if (d_control != 0) {
		while (sil_rew_mem((void *) d_control) != sil_rew_mem((void *) d_status)) {
		}
	}

	return(UC_SUCCESS);
}
