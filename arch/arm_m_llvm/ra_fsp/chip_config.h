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
 *  チップ依存モジュール (RA + Renesas FSP 共通; Cortex-M33 系)
 *
 *  対応 RA ファミリ: RA4M2/M3, RA4E1/E2, RA6M4/M5, RA6T2 等．
 *  個別チップは Makefile.target 側の MCU_GROUP / CORE_CPU 変数で選択する．
 *
 *  このインクルードファイルは target_config.h からインクルードされる
 */

#ifndef TOPPERS_CHIP_CONFIG_H
#define TOPPERS_CHIP_CONFIG_H

/*
 *  割込み番号に関する定義
 *  RA6M5 (R7FA6M5BH): IRQ0〜IRQ95 (例外番号16〜111)
 *  ICU.IELSR で 96 個のイベントリンクスロットを持つ (BSP_ICU_VECTOR_NUM_ENTRIES)．
 *  Cortex-M33 NVIC IRQ0..IRQ95 は ICU が任意の RA イベントへ動的に割付ける．
 *
 *  注意: RA ファミリの他チップ (RA6M4=96, RA4M2/M3=96, RA6T2=96, RA8M1=128 等)
 *        ではスロット数が異なる．本チップ層は RA ファミリ汎用だが，現状
 *        TMAX_INTNO/TNUM_INT は RA6M5/RA6M4/RA4M2/RA6T2 共通の 96 スロット
 *        前提でハードコードしている．RA8M1 等で広げる必要が出たら
 *        MCU_GROUP に応じて分岐する．
 */
#define TMIN_INTNO  UINT_C(16)   /* 最小割込み番号（IRQ0 = 例外番号16） */
#define TMAX_INTNO  UINT_C(111)  /* 最大割込み番号（IRQ95 = 例外番号111） */
#define TNUM_INT    UINT_C(96)   /* 割込み番号の個数 (= ICU IELSR スロット数) */

/*
 *  割込み優先度ビット幅
 *  RA6M5 Cortex-M33 NVIC は 4 ビット優先度 (上位 4 ビットのみ実装)．
 */
#define TBITW_IPRI  4U

#ifndef TOPPERS_MACRO_ONLY

/*
 *  Renesas FSP の BSP API をインクルード
 *
 *  bsp_api.h は CMSIS デバイスヘッダ (R7FA<MCU>.h．例: R7FA6M5BH.h,
 *  R7FA6M4AF.h) とチップ機能定義 (bsp_feature.h, bsp_peripheral.h) を
 *  取り込む．実際の bsp_cfg.h / bsp_clock_cfg.h は Smart Configurator
 *  が生成する target/<TARGET>/fsp/ra_cfg/ 以下に置かれる．
 */
#include "bsp_api.h"

#endif /* TOPPERS_MACRO_ONLY */

/*
 *  プロセッサ依存部のインクルード
 */
#include "prc_config.h"

#endif /* TOPPERS_CHIP_CONFIG_H */
