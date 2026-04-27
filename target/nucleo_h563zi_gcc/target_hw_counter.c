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
 *  ハードウェアカウンタ実装（NUCLEO_H563ZI_GCC用）
 *
 *  MAIN_HW_COUNTER:
 *    TIM2: フリーランニング 32bit 上昇カウンタ (1MHz), 現在値タイマ
 *    TIM5: ワンショット 32bit 上昇カウンタ (1MHz), アラームタイマ
 *
 *  制御方針:
 *    get_hwcounter() → TIM2->CNT を直接返す（絶対時間）
 *    set_hwcounter(exprtick) → delta = exprtick - TIM2->CNT を TIM5 に設定
 *    TIM5 が delta カウント後に UIF 割込みを発生させる
 */

#include "Os.h"
#include "prc_sil.h"
#include "stm32h5xx_hal.h"          /* TIM2/TIM5/RCC レジスタ定義 */
#include "target_hw_counter.h"

/*
 *  TIM CR1 ビット定義
 */
#define TIM_CR1_CEN_BIT     (1U << 0U)
#define TIM_CR1_OPM_BIT     (1U << 3U)
#define TIM_CR1_ARPE_BIT    (1U << 7U)

/*
 *  TIM DIER ビット定義
 */
#define TIM_DIER_UIE_BIT    (1U << 0U)

/*
 *  TIM SR ビット定義
 */
#define TIM_SR_UIF_BIT      (1U << 0U)

/*
 *  TIM EGR ビット定義
 */
#define TIM_EGR_UG_BIT      (1U << 0U)

/*
 *  MAIN_HW_COUNTER 保持値（set_hwcounter で管理）
 */
static TickType MAIN_HW_COUNTER_maxval;

/*
 *  ハードウェアカウンタの初期化
 *  TIM2: フリーランニング上昇カウンタ起動
 *  TIM5: アラームタイマ設定（割込み有効, OPM モード）
 */
void
init_hwcounter_MAIN_HW_COUNTER(TickType maxval, TimeType nspertick)
{
    (void)nspertick;
    MAIN_HW_COUNTER_maxval = maxval;

    /* TIM2/TIM5 クロック有効 (STM32H5: APB1LENR) */
    RCC->APB1LENR |= RCC_APB1LENR_TIM2EN | RCC_APB1LENR_TIM5EN;
    (void)RCC->APB1LENR;    /* read back for clock enable propagation */

    /* ---- TIM2 初期化（フリーランニング） ---- */
    TIM2->CR1  = 0U;
    TIM2->PSC  = TIMER_PSC_VALUE;
    TIM2->ARR  = 0xFFFFFFFFU;
    TIM2->CNT  = 0U;
    TIM2->EGR  = TIM_EGR_UG_BIT;   /* レジスタ更新イベント */
    TIM2->SR   = 0U;                /* UIF クリア */
    TIM2->DIER = 0U;                /* 割込み不要 */
    TIM2->CR1  = TIM_CR1_ARPE_BIT; /* ARR プリロード有効, カウント停止 */

    /* ---- TIM5 初期化（ワンショットアラーム） ----
     *  ARPE は 0（ARR を即時反映 — set_hwcounter で UG を発行しなくて済むように）
     *  UG を都度発行すると UIF がセットされ，NVIC pending が立って次に割込みを
     *  許可した瞬間に spurious な割込みが走る（常に割込みが入り続ける原因）．
     */
    TIM5->CR1  = 0U;
    TIM5->PSC  = TIMER_PSC_VALUE;
    TIM5->ARR  = 0xFFFFFFFFU;
    TIM5->CNT  = 0U;
    TIM5->EGR  = TIM_EGR_UG_BIT;   /* 起動時のみ PSC ロード目的で UG */
    TIM5->SR   = 0U;                /* UG で立った UIF をクリア (DIER=0 なので NVIC には波及しない) */
    /* NVIC pending もクリアしておく（保険） */
    *((volatile uint32 *)0xE000E284) = (1U << (48U - 32U));   /* NVIC_ICPR1: bit 16 = IRQ48 */
    TIM5->DIER = TIM_DIER_UIE_BIT; /* Update 割込み有効 */
    /* OPM=1: 1回カウント後に自動停止．ARPE は 0 (ARR 即時反映) */
    TIM5->CR1  = TIM_CR1_OPM_BIT;
}

/*
 *  ハードウェアカウンタの開始
 */
void
start_hwcounter_MAIN_HW_COUNTER(void)
{
    TIM2->CR1 |= TIM_CR1_CEN_BIT;
}

/*
 *  ハードウェアカウンタの停止
 */
void
stop_hwcounter_MAIN_HW_COUNTER(void)
{
    TIM2->CR1 &= ~TIM_CR1_CEN_BIT;
    TIM5->CR1 &= ~TIM_CR1_CEN_BIT;
    TIM5->SR   = 0U;
}

/*
 *  ハードウェアカウンタへの満了時間の設定
 *  exprtick: 次に満了すべき絶対カウンタ値
 */
void
set_hwcounter_MAIN_HW_COUNTER(TickType exprtick)
{
    TickType curr;
    TickType delta;

    /* 現在のカウンタ値を取得 */
    curr  = (TickType)TIM2->CNT;
    /* 差分計算（32bit モジュラー算術でラップアラウンドを自動処理） */
    delta = (TickType)((uint32)exprtick - (uint32)curr);
    if (delta == 0U) {
        delta = 1U;
    }

    /* TIM5 を停止してから再設定．
     * UG（EGR=UG_BIT）は発行しない：ARPE=0 なので ARR は即時反映される．
     * UG を発行すると UIF が立ち，NVIC pending が残って即座に ISR が呼ばれ
     * 先に進まなくなるため（ASP3 の target_hrt_set_event と同じ方式）．
     */
    TIM5->CR1 &= ~TIM_CR1_CEN_BIT;
    TIM5->SR   = 0U;
    TIM5->ARR  = (uint32)delta;
    TIM5->CNT  = 0U;
    /* OPM 開始 */
    TIM5->CR1 |= TIM_CR1_CEN_BIT;
}

/*
 *  ハードウェアカウンタの現在時間の取得
 */
TickType
get_hwcounter_MAIN_HW_COUNTER(void)
{
    return (TickType)TIM2->CNT;
}

/*
 *  ハードウェアカウンタの設定された満了時間の取消
 */
void
cancel_hwcounter_MAIN_HW_COUNTER(void)
{
    TIM5->CR1 &= ~TIM_CR1_CEN_BIT;
    TIM5->SR   = 0U;
}

/*
 *  ハードウェアカウンタの強制割込み要求
 *  delta=1 で即座に UIF が発生する
 */
void
trigger_hwcounter_MAIN_HW_COUNTER(void)
{
    TIM5->CR1 &= ~TIM_CR1_CEN_BIT;
    TIM5->SR   = 0U;
    TIM5->ARR  = 1U;
    TIM5->CNT  = 0U;
    TIM5->EGR  = TIM_EGR_UG_BIT;
    TIM5->SR   = 0U;
    TIM5->CR1 |= TIM_CR1_CEN_BIT;
}

/*
 *  割込み要求のクリア（ISR 内から呼ばれる）
 */
void
int_clear_hwcounter_MAIN_HW_COUNTER(void)
{
    TIM5->SR = 0U;
}

/*
 *  割込み要求のキャンセル（ペンディング割込みをキャンセル）
 */
void
int_cancel_hwcounter_MAIN_HW_COUNTER(void)
{
    TIM5->SR = 0U;
}

/*
 *  ハードウェアカウンタのインクリメント
 *  （STM32H563ZI ターゲットでは未サポート）
 */
void
increment_hwcounter_MAIN_HW_COUNTER(void)
{
}
