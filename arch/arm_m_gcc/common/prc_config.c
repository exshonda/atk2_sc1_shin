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
 *  プロセッサ依存モジュール（ARM Cortex-M33用）
 */
#include "kernel_impl.h"

/*
 *  例外（割込み/CPU例外）のネスト回数のカウント
 *  コンテキスト参照のために使用
 */
uint32          except_nest_cnt;

/*
 *  x_nested_lock_os_int() のネスト回数
 */
volatile uint8  nested_lock_os_int_cnt;

/*
 *  OS割込み禁止状態の時にBASEPRIの値を保存する変数
 */
volatile uint32 saved_basepri;

/*
 *  プロセッサハードウェアの初期化
 *  target_hardware_initialize() から呼び出される
 */
void
prc_hardware_initialize(void)
{
    /* NVICの初期設定はprc_initialize()で実施 */
}

/*
 *  プロセッサ依存の初期化
 *  target_initialize() から呼び出される
 */
void
prc_initialize(void)
{
    /*
     *  カーネル起動時は非タスクコンテキストとして動作させるため1に
     */
    except_nest_cnt = 1U;

    /*
     *  PendSV と SysTick の優先度を最低（0xFF）に設定する
     *  PendSV はディスパッチャ専用、最低優先度にすることで全 ISR を
     *  処理し終わった後に走らせる（テールチェイン）。
     *  NVIC_SYS_PRI3(SHPR3, 0xE000ED20):
     *    byte 2 (bits 23:16) = PendSV
     *    byte 3 (bits 31:24) = SysTick
     */
    *((volatile uint32 *)NVIC_SYS_PRI3) =
        (*((volatile uint32 *)NVIC_SYS_PRI3) & 0x0000ffffU) | 0xffff0000U;

    /*
     *  ベクタテーブルオフセットレジスタを設定する
     *  kernel_vector_table は Os_Lcfg.c で生成される
     */
    extern const uint32 kernel_vector_table[];
    *((volatile uint32 *)NVIC_VECTTBL) = (uint32)kernel_vector_table;
    Asm("dsb" ::: "memory");
    Asm("isb" ::: "memory");

#ifdef TOPPERS_FPU_ENABLE
    /*
     *  FPU の有効化と FPCCR の設定 (TOPPERS_FPU_ENABLE 時のみ)．
     *    CPACR.CP10/CP11 = 0b11  : Full Access (FPU 有効化)
     *    FPCCR           : ASPEN/LSPEN ビットで Lazy Stacking を制御．
     *  FPCCR_INIT は arm_m.h が TOPPERS_FPU_NO_PRESERV /
     *  TOPPERS_FPU_NO_LAZYSTACKING / TOPPERS_FPU_LAZYSTACKING に応じて
     *  選択する．
     */
    *((volatile uint32 *)CPACR) |= CPACR_FPU_ENABLE;
    *((volatile uint32 *)FPCCR) = FPCCR_INIT;
    Asm("dsb" ::: "memory");
    Asm("isb" ::: "memory");
#endif /* TOPPERS_FPU_ENABLE */
}

/*
 *  プロセッサ依存の終了処理
 */
void
prc_terminate(void)
{
    /* 全割込みを禁止する */
    Asm("cpsid i" ::: "memory");
}

/*
 *  割込み要求ラインの属性の設定
 *  intno: TMIN_INTNO〜TMAX_INTNO (IRQno + 16)
 *  intpri: -1〜-15 (C2ISR) または 0 (C1ISR)
 */
void
x_config_int(InterruptNumberType intno, AttributeType intatr, PriorityType intpri)
{
    ASSERT(VALID_INTNO(intno));

    /* NVIC割込み優先度を設定 */
    *INTNO_TO_PRI_ADDR(intno) = (uint8)INT_IPM(intpri);

    /* 割込み許可/禁止の設定 */
    if ((intatr & ENABLE) != 0U) {
        x_enable_int(intno);
    }
    else {
        x_disable_int(intno);
    }
}

#ifndef OMIT_DEFAULT_INT_HANDLER

/*
 *  未定義の割込みが入った場合の処理
 */
void
default_int_handler(void)
{
    target_fput_str("Unregistered Interrupt occurs.");
    ASSERT_NO_REACHED;
}

#endif /* OMIT_DEFAULT_INT_HANDLER */
