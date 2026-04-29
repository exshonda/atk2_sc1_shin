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
 *  チップ依存モジュール（STM32H5XX_STM32CUBE用）
 *
 *  このインクルードファイルは target_config.h からインクルードされる
 */

#ifndef TOPPERS_CHIP_CONFIG_H
#define TOPPERS_CHIP_CONFIG_H

/*
 *  割込み番号に関する定義
 *  STM32H563ZI: IRQ0〜IRQ131 (例外番号16〜147)
 */
#define TMIN_INTNO  UINT_C(16)   /* 最小割込み番号（IRQ0 = 例外番号16） */
#define TMAX_INTNO  UINT_C(147)  /* 最大割込み番号（IRQ131 = 例外番号147） */
#define TNUM_INT    UINT_C(132)  /* 割込み番号の個数 */

/*
 *  割込み優先度ビット幅
 *  STM32H5xx は 4 ビット優先度 (NVIC IPR は上位 4 ビットのみ実装)．
 */
#define TBITW_IPRI  4U

#ifndef TOPPERS_MACRO_ONLY

/*
 *  STM32H5xx HAL ドライバのインクルード
 */
#include "stm32h5xx_hal.h"

/*
 *  システムクロック設定
 */
extern void SystemClock_Config(void);

/*
 *  エラーハンドラ
 */
extern void Error_Handler(void);

/*
 *  HAL タイマティック（SysTick を使わない場合のダミー）
 */
extern HAL_StatusTypeDef HAL_InitTick(uint32_t TickPriority);
extern uint32_t HAL_GetTick(void);

#endif /* TOPPERS_MACRO_ONLY */

/*
 *  プロセッサ依存部のインクルード
 */
#include "prc_config.h"

#endif /* TOPPERS_CHIP_CONFIG_H */
