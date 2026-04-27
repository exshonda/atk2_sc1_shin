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
 *  カーネル用スタートアップモジュール（ARM Cortex-M33用）
 */

#define OMIT_INCLUDE_OS_CFG     /* Os_Cfg.hインクルード抑止 */
#define TOPPERS_MACRO_ONLY
#define UINT_C(val)     (val)
#define CAST(type, val) (val)

#include "kernel_impl.h"
#include "arm_m.h"

    .syntax unified
    .thumb

/*
 *  スタートアップルーチン
 *
 *  リセット直後，Handler モード (MSP) で呼び出される
 */
    .text
    .global _kernel_start
    .thumb_func
    .balign FUNCTION_ALIGN_SIZE
_kernel_start:
    /* 全割込みを禁止 */
    cpsid i

#ifdef INIT_MSP
    /*
     *  MSP の設定
     *  リセット直後のベクタテーブル先頭に配置された SRAM 末尾値が MSP に
     *  読み込まれているが、ATK2 の OS スタック (kernel_ostkpt) を MSP に
     *  改めて設定する。
     *
     *  CONTROL.SPSEL=0 (MSP 有効) を確実にしてから msp に kernel_ostkpt を
     *  ロードする。kernel_ostkpt は Os_Lcfg.c で
     *      StackType * const kernel_ostkpt = TOPPERS_OSTKPT(...)
     *  と定義された読み取り専用ポインタなので [r0] でロードする。
     */
    mov   r0, #CONTROL_MSP   /* CONTROL.SPSEL = 0, nPRIV = 0 */
    msr   control, r0
    isb                       /* control 操作後の同期 */
    ldr   r0, =kernel_ostkpt
    ldr   r1, [r0]
    msr   msp, r1
#endif /* INIT_MSP */

    /* hardware_init_hook の呼び出し */
    bl    hardware_init_hook

    /* BSSセクションの初期化 */
    ldr   r0, =BSS_START
    ldr   r1, =BSS_END
    movs  r2, #0
    cmp   r0, r1
    bhs   start_data
start_bss:
    str   r2, [r0]
    add   r0, r0, #4
    cmp   r0, r1
    blo   start_bss

    /* DATAセクションの初期化 (ROMから RAMへコピー) */
start_data:
    ldr   r0, =IDATA_START
    ldr   r1, =IDATA_END
    ldr   r2, =DATA_START
    cmp   r0, r1
    bhs   start_main
start_data_copy:
    ldr   r3, [r0]
    str   r3, [r2]
    add   r0, r0, #4
    add   r2, r2, #4
    cmp   r0, r1
    blo   start_data_copy

    /* software_init_hook の呼び出し */
start_main:
    bl    software_init_hook

    /*
     *  main() の呼び出し
     *  ハードウェア初期化 (target_hardware_initialize) は
     *  StartOS()→target_initialize() から行うため、ここでは呼ばない。
     */
    bl    main

    /* main から戻った場合は無限ループ */
start_end:
    b     start_end


/*
 *  デフォルトの hardware_init_hook (弱定義)
 */
    .text
    .weak hardware_init_hook
    .thumb_func
hardware_init_hook:
    bx    lr


/*
 *  デフォルトの software_init_hook (弱定義)
 */
    .text
    .weak software_init_hook
    .thumb_func
software_init_hook:
    bx    lr


/*
 *  デフォルトの CPU例外ハンドラ (弱定義)
 *  ハードフォルトなど未定義の例外の場合に無限ループ
 */
    .text
    .global default_exc_handler
    .weak   default_exc_handler
    .thumb_func
default_exc_handler:
    b     default_exc_handler

