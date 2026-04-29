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
 *  ハードウェアカウンタ実装（EK_RA6M5_GCC用）
 *
 *  MAIN_HW_COUNTER:
 *    GPT320: フリーランニング 32bit 上昇カウンタ (1MHz), 現在値タイマ
 *    GPT321: ワンショット 32bit 上昇カウンタ (1MHz), アラームタイマ
 *
 *  制御方針:
 *    get_hwcounter() → GPT320->GTCNT を直接返す（絶対時間）
 *    set_hwcounter(exprtick) → delta = exprtick - GTCNT を GPT321 に設定
 *    GPT321 は OPM 相当 (GTUDDTYC=ONESHOT, GTPR=delta) で UDF/OVF 割込み
 *    を発生させる
 *
 *  RA6M5 GPT のクロック源は PCLKD．Smart Configurator 既定では 100MHz．
 *  1MHz tick を作るため，本実装では下記レジスタ操作を行う:
 *    GTCR.TPCS = 0  (PCLKD/1) ... ※下記 NOTE 参照
 *    GTPR (周期)= MAX (= 0xFFFFFFFF) でフリーラン
 *  1MHz 等価で扱うため，PCLKD=100MHz では実質 100tick/us となる．
 *  TIMER_CLOCK_HZ の最終値は target_hw_counter.h の TODO 解決時に決定．
 *
 *  Phase 2 完成時には Phase 2-A の bsp_clock_cfg.h で PCLKD を 100MHz
 *  以外 (例: 50MHz) に切替えるオプションを評価する．
 */

#include "Os.h"
#include "prc_sil.h"
#include "target_hw_counter.h"
#include "ek_ra6m5.h"

/*
 *  GPT320 / GPT321 ベースアドレス
 *  RA6M5 R_GPT_GTPCLK 領域: R_GPT0..R_GPT9 + R_GPT320 (32-bit GPT0)
 *                                          + R_GPT321 (32-bit GPT1)
 *  R7FA6M5BH のレジスタマップより:
 *    R_GPT320 = 0x40169000  (GPT320 = 32-bit ch0)
 *    R_GPT321 = 0x40169100  (GPT321 = 32-bit ch1)
 */
#define R_GPT320_BASE       0x40169000UL
#define R_GPT321_BASE       0x40169100UL

/*
 *  GPT レジスタオフセット (RA6M5 ハードウェアマニュアル GPTシリーズ)
 *    GTWP   : 0x00  Write Protection
 *    GTSTR  : 0x04  Start Source Select
 *    GTSTP  : 0x08  Stop Source Select
 *    GTCLR  : 0x0C  Clear Source Select
 *    GTCR   : 0x2C  Timer Control
 *    GTUDDTYC:0x30  Count Direction and Duty Setting
 *    GTIOR  : 0x34  I/O Control
 *    GTINTAD: 0x38  Interrupt Output Setting
 *    GTST   : 0x3C  Status
 *    GTBER  : 0x40  Buffer Enable
 *    GTCNT  : 0x48  Counter
 *    GTCCR[A-F] : 0x4C..0x60  Compare Capture
 *    GTPR   : 0x64  Cycle setting (Period)
 *    GTPBR  : 0x68  Cycle setting buffer
 */
#define GPT_GTWP            0x00U
#define GPT_GTSTR           0x04U
#define GPT_GTSTP           0x08U
#define GPT_GTCLR           0x0CU
#define GPT_GTCR            0x2CU
#define GPT_GTUDDTYC        0x30U
#define GPT_GTIOR           0x34U
#define GPT_GTINTAD         0x38U
#define GPT_GTST            0x3CU
#define GPT_GTBER           0x40U
#define GPT_GTCNT           0x48U
#define GPT_GTPR            0x64U
#define GPT_GTPBR           0x68U

#define GPT_REG32(base, off) (*(volatile uint32 *)((uintptr_t)(base) + (uintptr_t)(off)))

/* GTWP: 書込み保護解除 (0xA500 を上位に書く必要あり) */
#define GTWP_UNLOCK         0xA500U
/* GTWP.WP=1 で各種設定レジスタの書込みを許可 (0=保護, 1=書込み可)
   キーコード 0xA5 と組合せて 0xA501 で WP=1, 0xA500 で WP=0 */
#define GTWP_WRITE_ENABLE   0xA501U

/* GTCR.CST = bit0 : Count Start (1=count, 0=stop) */
#define GTCR_CST            (1U << 0U)
/* GTCR.MD[2:0] = bit16-18 : 0=Saw-wave PWM (default counting up) */
#define GTCR_MD_SAWWAVE     (0U << 16U)
/* GTCR.TPCS[3:0] = bit24-27 : Timer Prescaler (0=PCLKD/1, 1=PCLKD/4, 2=PCLKD/16, ...) */
#define GTCR_TPCS_DIV1      (0U << 24U)
#define GTCR_TPCS_DIV4      (1U << 24U)
#define GTCR_TPCS_DIV16     (2U << 24U)

/* GTUDDTYC.UD = bit0 : 1=count up, 0=count down */
#define GTUDDTYC_UP         (1U << 0U)
/* GTUDDTYC.UDF = bit1 : 1=write enable */
#define GTUDDTYC_UDF        (1U << 1U)

/* GTINTAD.GTINTPR = bit0 : 0=no interrupt, 1=enable Period interrupt (overflow) */
#define GTINTAD_GTINTPR_OVF (1U << 0U)

/* GTST.TUCF = bit15 : count direction flag */
/* GTST.TCFPO = bit6 : Overflow flag (clear by writing 0) */
#define GTST_TCFPO          (1U << 6U)

/*
 *  GPT モジュールクロック有効化
 *  RA6M5 では Module Stop Control Register D (MSTPCRD) で GPT を制御．
 *  R_MSTP_BASE = R_MSTP (0x40047000), MSTPCRD は offset 0x4C．
 *    MSTPCRD.MSTPD5 = 1 : GPT320 (32-bit timer) を停止
 *    MSTPCRD.MSTPD6 = 1 : GPT321 を停止 (?: 仕様要確認)
 *    実際には MSTPD5 が 32-bit GPT 全体 (GPT320 + GPT321) を制御するため
 *    1 ビット解除すれば両方有効になる．
 *  本実装は Phase 2-A の hal_data.c が R_GPT_Open 内で行う MSTP 解除を
 *  期待するが，ATK2 が直叩きする場合は事前にここでも解除する．
 */
#define R_MSTPCRD_ADDR      0x4001E01CUL
#define MSTPD_GPT320_321    (1UL << 5U)   /* MSTPD5 (Phase 2-A で要確認) */

/*
 *  MAIN_HW_COUNTER 保持値（set_hwcounter で管理）
 */
static TickType MAIN_HW_COUNTER_maxval;

/*
 *  ハードウェアカウンタの初期化
 *  GPT320: フリーランニング上昇カウンタ起動
 *  GPT321: アラームタイマ設定（割込み有効, ワンショット）
 *
 *  PCLKD = 100MHz, GTCR.TPCS=DIV1 で 100MHz クロック源．
 *  Phase 2 では実 1MHz 化のためのソースクロック調整は Smart Configurator
 *  側で行うことを前提とし，ここでは frequency_hz 換算を呼出側に委ねる．
 */
void
init_hwcounter_MAIN_HW_COUNTER(TickType maxval, TimeType nspertick)
{
    (void)nspertick;
    MAIN_HW_COUNTER_maxval = maxval;

    /* GPT モジュールストップ解除 (保険．Smart Configurator が行うはず) */
    GPT_REG32(R_MSTPCRD_ADDR, 0U) &= ~MSTPD_GPT320_321;
    (void)GPT_REG32(R_MSTPCRD_ADDR, 0U);

    /* ---- GPT320 初期化 (フリーランニング, 割込み未使用) ---- */
    GPT_REG32(R_GPT320_BASE, GPT_GTWP)     = GTWP_WRITE_ENABLE;
    GPT_REG32(R_GPT320_BASE, GPT_GTCR)     = 0U;                      /* 停止 */
    GPT_REG32(R_GPT320_BASE, GPT_GTUDDTYC) = GTUDDTYC_UP | GTUDDTYC_UDF; /* 上昇カウント */
    GPT_REG32(R_GPT320_BASE, GPT_GTINTAD)  = 0U;                      /* 割込み無効 */
    GPT_REG32(R_GPT320_BASE, GPT_GTPR)     = 0xFFFFFFFFU;              /* 最大周期でフリーラン */
    GPT_REG32(R_GPT320_BASE, GPT_GTPBR)    = 0xFFFFFFFFU;
    GPT_REG32(R_GPT320_BASE, GPT_GTCNT)    = 0U;
    GPT_REG32(R_GPT320_BASE, GPT_GTST)     = 0U;                       /* status クリア */
    GPT_REG32(R_GPT320_BASE, GPT_GTCR)     = GTCR_TPCS_DIV1 | GTCR_MD_SAWWAVE; /* CST=0 でまだ停止 */

    /* ---- GPT321 初期化 (ワンショットアラーム, 割込み有効) ---- */
    GPT_REG32(R_GPT321_BASE, GPT_GTWP)     = GTWP_WRITE_ENABLE;
    GPT_REG32(R_GPT321_BASE, GPT_GTCR)     = 0U;
    GPT_REG32(R_GPT321_BASE, GPT_GTUDDTYC) = GTUDDTYC_UP | GTUDDTYC_UDF;
    GPT_REG32(R_GPT321_BASE, GPT_GTINTAD)  = GTINTAD_GTINTPR_OVF;      /* 周期 (オーバーフロー) 割込み有効 */
    GPT_REG32(R_GPT321_BASE, GPT_GTPR)     = 0xFFFFFFFFU;
    GPT_REG32(R_GPT321_BASE, GPT_GTPBR)    = 0xFFFFFFFFU;
    GPT_REG32(R_GPT321_BASE, GPT_GTCNT)    = 0U;
    GPT_REG32(R_GPT321_BASE, GPT_GTST)     = 0U;
    GPT_REG32(R_GPT321_BASE, GPT_GTCR)     = GTCR_TPCS_DIV1 | GTCR_MD_SAWWAVE;
}

/*
 *  ハードウェアカウンタの開始
 *  GPT320 をスタート (CST=1)．GPT321 は set_hwcounter() で起動する．
 */
void
start_hwcounter_MAIN_HW_COUNTER(void)
{
    GPT_REG32(R_GPT320_BASE, GPT_GTCR) |= GTCR_CST;
}

/*
 *  ハードウェアカウンタの停止
 */
void
stop_hwcounter_MAIN_HW_COUNTER(void)
{
    GPT_REG32(R_GPT320_BASE, GPT_GTCR) &= ~GTCR_CST;
    GPT_REG32(R_GPT321_BASE, GPT_GTCR) &= ~GTCR_CST;
    GPT_REG32(R_GPT321_BASE, GPT_GTST)  = 0U;
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

    curr  = (TickType)GPT_REG32(R_GPT320_BASE, GPT_GTCNT);
    delta = (TickType)((uint32)exprtick - (uint32)curr);
    if (delta == 0U) {
        delta = 1U;
    }

    /* GPT321 を停止して再設定．
     * 周期 (GTPR) を delta にして CST=1 で起動 → delta カウントで OVF．
     */
    GPT_REG32(R_GPT321_BASE, GPT_GTCR) &= ~GTCR_CST;
    GPT_REG32(R_GPT321_BASE, GPT_GTST)  = 0U;
    GPT_REG32(R_GPT321_BASE, GPT_GTPR)  = (uint32)delta;
    GPT_REG32(R_GPT321_BASE, GPT_GTPBR) = (uint32)delta;
    GPT_REG32(R_GPT321_BASE, GPT_GTCNT) = 0U;
    GPT_REG32(R_GPT321_BASE, GPT_GTCR) |= GTCR_CST;
}

/*
 *  ハードウェアカウンタの現在時間の取得
 */
TickType
get_hwcounter_MAIN_HW_COUNTER(void)
{
    return (TickType)GPT_REG32(R_GPT320_BASE, GPT_GTCNT);
}

/*
 *  ハードウェアカウンタの設定された満了時間の取消
 */
void
cancel_hwcounter_MAIN_HW_COUNTER(void)
{
    GPT_REG32(R_GPT321_BASE, GPT_GTCR) &= ~GTCR_CST;
    GPT_REG32(R_GPT321_BASE, GPT_GTST)  = 0U;
}

/*
 *  ハードウェアカウンタの強制割込み要求
 *  delta=1 で即座に OVF 割込みを発生させる
 */
void
trigger_hwcounter_MAIN_HW_COUNTER(void)
{
    GPT_REG32(R_GPT321_BASE, GPT_GTCR) &= ~GTCR_CST;
    GPT_REG32(R_GPT321_BASE, GPT_GTST)  = 0U;
    GPT_REG32(R_GPT321_BASE, GPT_GTPR)  = 1U;
    GPT_REG32(R_GPT321_BASE, GPT_GTPBR) = 1U;
    GPT_REG32(R_GPT321_BASE, GPT_GTCNT) = 0U;
    GPT_REG32(R_GPT321_BASE, GPT_GTCR) |= GTCR_CST;
}

/*
 *  割込み要求のクリア（ISR 内から呼ばれる）
 *  GPT のオーバーフローフラグ TCFPO を 0 でクリア．
 *  RA6M5 の R_BSP_IrqStatusClear (IELSR.IR=0) も target_config.c の
 *  ISR ラッパで呼ぶこと．
 */
void
int_clear_hwcounter_MAIN_HW_COUNTER(void)
{
    GPT_REG32(R_GPT321_BASE, GPT_GTST) = 0U;
}

/*
 *  割込み要求のキャンセル（ペンディング割込みをキャンセル）
 */
void
int_cancel_hwcounter_MAIN_HW_COUNTER(void)
{
    GPT_REG32(R_GPT321_BASE, GPT_GTST) = 0U;
}

/*
 *  ハードウェアカウンタのインクリメント
 *  EK-RA6M5 ターゲットでは未サポート（GPT320 が自走するため）
 */
void
increment_hwcounter_MAIN_HW_COUNTER(void)
{
}
