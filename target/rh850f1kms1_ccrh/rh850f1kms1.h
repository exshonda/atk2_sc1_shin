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
 *		RH850/F1KM-S1 (R7F701684) の構成定義
 *
 *  hsbrh850f1k.h をベースに，F1KM-S1 のクロック構成と
 *  ログ出力に使用する RLIN32 の端子設定へ差し替えたもの．
 */

#ifndef TOPPERS_RH850F1KMS1_H
#define TOPPERS_RH850F1KMS1_H

#include "v850_gcc/rh850_f1km.h"

/*
 *  クロック速度
 */

/*
 *  PLL関連の定義
 *
 *  PLL1 VCOOUT:480MHz / PLLOUT(VCOOUT/4):120MHz
 */
#define MAINOSC_CLOCK_MHZ	20      /* Main OSC is 20MHz */
#define INTOSCH_CLK_MHZ		8       /* High Speed Internal OSC Clock is 8MHz */
#define INTOSCL_CLK_KHZ		240     /* Low Speed Internal OSC Clock is 240kHz */

#define PLL1_CLK_MHZ		120 /* PLL1 is 120MHz */
#define PLL1C_DEFAULT_VALUE	0x00010300U
#define PLL1C_mr			2       /* M[1:0]   */
#define PLL1C_nr			48      /* N[5:0]+1 */

/*
 *  CPUクロック分周選択レジスタ(C_ISO_CPUCLK)の設定値
 */
#define CPUCLKDCSID_DIVIDE_1	(1U)
#define CPUCLKDCSID_DIVIDE_2	(2U)
#define CPUCLKDCSID_DIVIDE_4	(3U)
#define CPUCLKDCSID_DIVIDE_8	(4U)

#define CPUCLKDPLL_MAX_80		(0U << 3)
#define CPUCLKDPLL_MAX_96		(1U << 3)
#define CPUCLKDPLL_MAX_120		(2U << 3)

/*
 *  TAUJ クロックドメインの設定値
 */
#define ATAUJSCSID_HS_INTOSC	(1U)
#define ATAUJSCSID_MAINOSC		(2U)
#define ATAUJSCSID_LS_INTOSC	(3U)
#define ATAUJSCSID_PPLLCLK2		(4U)

#define ATAUJDCSID_DIVIDE_1		(1U)
#define ATAUJDCSID_DIVIDE_2		(2U)
#define ATAUJDCSID_DIVIDE_4		(3U)
#define ATAUJDCSID_DIVIDE_8		(4U)

/*
 *  Port 10 Configration for RLIN32
 *   P10_14 : RLIN32TX (第2兼用)
 *   P10_13 : RLIN32RX (第2兼用)
 */
#define RLIN32_P10_MASK			((uint16) 0x6000)
#define RLIN32_PMC10_INIT		((uint16) 0x6000)
#define RLIN32_PFC10_INIT		((uint16) 0x6000)
#define RLIN32_PM10_INIT		((uint16) 0x2000)
#define RLIN32_PIBC10_INIT		((uint16) 0x2000)

#endif /* TOPPERS_RH850F1KMS1_H */
