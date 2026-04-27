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
 *  プロセッサ依存モジュール アセンブリ言語部（ARM Cortex-M33用）
 *
 *  ディスパッチャ構造は ASP3 (asp3/arch/arm_m_gcc/common/core_support.S) を
 *  踏襲する:
 *    - タスクコンテキストからのディスパッチ: do_dispatch() → dispatcher_0
 *      ・ 次タスクの再開番地が EXC_RETURN なら svc #0 で Handler モードへ
 *      ・ そうでなければ Thread モードのまま bx r2 で再開
 *    - 割込み出口でのディスパッチ: PendSV ハンドラ
 *      ・ 次タスクの再開番地が EXC_RETURN なら通常の例外リターン
 *      ・ そうでなければ偽の例外フレームを PSP に積んで例外リターン
 *  ATK2 固有の状態 (callevel_stat の TSYS_DISALLINT, nested_lock_os_int_cnt,
 *  saved_basepri, except_nest_cnt, p_runisr) はディスパッチャ内部で適切に
 *  更新する.
 */

#define TOPPERS_MACRO_ONLY
#define UINT_C(val)     (val)
#define CAST(type, val) (val)

#include "kernel_impl.h"
#include "arm_m.h"
#include "offset.h"

    .syntax unified
    .thumb


/*
 *  C2ISR 割込み入口処理
 *
 *  ベクタテーブルから直接呼び出される (Handler モード, MSP)
 *  ハードウェアは r0-r3,r12,lr,pc,xpsr を PSP または MSP に保存済み
 *  LR には EXC_RETURN が設定されている
 *
 *  終了時に p_runtsk != p_schedtsk なら PendSV をペンディングしてから
 *  例外リターンする．実際のディスパッチは pendsv_handler が行う．
 */
    .text
    .global interrupt_entry
    .thumb_func
    .balign FUNCTION_ALIGN_SIZE
interrupt_entry:
    /*
     *  callee-saved レジスタ (r4-r11) を MSP に退避.
     *  HW 例外フレームには r0-r3,r12,LR,PC,xPSR しか含まれず，AAPCS に
     *  より C ISR は r4-r11 を破壊できるため，ここで保存しておかないと
     *  プリエンプトされたタスクの r4-r11 が失われる (PendSV で TCB に
     *  保存される値もここで破壊された値になる).
     */
    push  {r4-r11}

    /* カーネル管理の割込みを禁止 (OS割込み禁止状態へ) */
    ldr   r2, =tmin_basepri
    ldr   r2, [r2]
    msr   basepri, r2

    /* IRQ番号を取得 (IPSR - 16) */
    mrs   r0, ipsr
    ubfx  r0, r0, #0, #9        /* r0 = IPSR & 0x1FF */
    sub   r1, r0, #16           /* r1 = IRQ番号 */

    /* except_nest_cnt のインクリメント */
    ldr   r2, =except_nest_cnt
    ldr   r3, [r2]
    add   r4, r3, #1
    str   r4, [r2]

    /* callevel_stat の保存と TCL_ISR2 の設定 */
    ldr   r2, =callevel_stat
    ldrh  r3, [r2]
    push  {r3, lr}              /* callevel_stat と EXC_RETURN を保存 */
    orr   r3, r3, #TCL_ISR2
    strh  r3, [r2]

    /* p_runisr の保存と設定 */
    ldr   r2, =p_runisr
    ldr   r3, [r2]
    push  {r3}                  /* p_runisr を保存 */
    ldr   r2, =isr_p_isrcb_tbl
    lsl   r4, r1, #2            /* r4 = IRQ番号 * 4 */
    ldr   r3, [r2, r4]
    ldr   r2, =p_runisr
    str   r3, [r2]

    /* OS割込み解除状態へ (C2ISR間のネストを許可) */
    movs  r2, #0
    msr   basepri, r2

    /* ISRハンドラの呼び出し */
    ldr   r2, =isr_tbl
    ldr   r0, [r2, r4]
    blx   r0

    /* C2ISR不正終了チェック */
    bl    exit_isr2

    /* OS割込み禁止状態へ */
    ldr   r2, =tmin_basepri
    ldr   r2, [r2]
    msr   basepri, r2

    /* p_runisr の復帰 */
    pop   {r3}
    ldr   r2, =p_runisr
    str   r3, [r2]

    /* callevel_stat の復帰, EXC_RETURN の復元 */
    pop   {r3, lr}
    ldr   r2, =callevel_stat
    strh  r3, [r2]

    /* except_nest_cnt のデクリメント */
    ldr   r2, =except_nest_cnt
    ldr   r3, [r2]
    sub   r3, r3, #1
    str   r3, [r2]

    /* ネスト > 0 ならそのまま戻る (ISRからISRへ) */
    cbnz  r3, interrupt_entry_ret

    /* p_runtsk != p_schedtsk ならディスパッチが必要 */
    ldr   r2, =p_runtsk
    ldr   r3, [r2]
    ldr   r2, =p_schedtsk
    ldr   r4, [r2]
    cmp   r3, r4
    beq   interrupt_entry_ret

    /* PendSV をセット (遅延ディスパッチ) */
    ldr   r2, =NVIC_ICSR
    ldr   r3, =NVIC_PENDSVSET
    str   r3, [r2]

interrupt_entry_ret:
    /* OS割込み解除 */
    movs  r2, #0
    msr   basepri, r2
    /* callee-saved レジスタを復帰 */
    pop   {r4-r11}
    bx    lr                    /* EXC_RETURN → 例外リターン */


/*
 *  遅延ディスパッチ (PendSV ハンドラ)
 *
 *  ASP3 の pendsv_handler 相当.
 *  Handler モードで MSP を使用して実行される.
 *  入口時点で LR = EXC_RETURN, PSP は被プリエンプトタスクの状態を
 *  保持している.
 */
    .text
    .global pendsv_handler
    .thumb_func
    .balign FUNCTION_ALIGN_SIZE
pendsv_handler:
    /* OS 割込み禁止 (カーネル管理割込みをマスク) */
    ldr   r1, =tmin_basepri
    ldr   r0, [r1]
    msr   basepri, r0

    ldr   r1, =p_runtsk
    ldr   r0, [r1]
    /* p_runtsk == NULL <=> アイドル中 -> コンテキスト保存不要 */
    cbz   r0, pendsv_handler_1

    /* 実行中タスクのコンテキストを PSP に保存 */
    mrs   r2, psp
#ifdef TOPPERS_FPU_CONTEXT
    /*
     *  EXC_RETURN.FType (bit 4) が 0 ならタスクは FPU を使用していて HW
     *  が拡張フレームを積んでいる. callee-saved の s16-s31 を退避する．
     *  Lazy Stacking 有効時も vstmdb の発行で s0-s15 が遅延ストールされる．
     */
    tst   lr, #EXC_RETURN_FP
    bne   pendsv_handler_save_no_fp
    vstmdb r2!, {s16-s31}
pendsv_handler_save_no_fp:
#endif /* TOPPERS_FPU_CONTEXT */
    stmfd r2!, {r4-r11}
    str   r2, [r0, #TCB_sp]
    str   lr, [r0, #TCB_pc]    /* lr = EXC_RETURN */

pendsv_handler_1:
    /* p_runtsk = p_schedtsk */
    ldr   r0, =p_schedtsk
    ldr   r0, [r0]
    str   r0, [r1]

    /* p_runtsk == NULL ならアイドル処理 */
    cbz   r0, return_to_idle

    /* TCB.pc が EXC_RETURN なら通常の例外リターンで Thread モードへ */
    ldr   r1, [r0, #TCB_pc]
    ands  r2, r1, #EXC_RETURN_PREFIX
    cmp   r2, #EXC_RETURN_PREFIX
    bne   return_to_thread

    /*
     *  EXC_RETURN ケース:
     *  TCB.sp 上に r4-r11 が積まれており，FPU を使用していたタスクは
     *  その上に s16-s31 も積まれている．さらに PSP の上に HW 例外フレーム
     *  が残っている. r4-r11 (および必要なら s16-s31) を復帰し PSP を更新
     *  して例外リターンするだけでプリエンプト前の状態に戻れる.
     */
    ldr   r2, [r0, #TCB_sp]
    ldmfd r2!, {r4-r11}
#ifdef TOPPERS_FPU_CONTEXT
    /* TCB.pc (= 保存済 EXC_RETURN) の FType ビットで判定 */
    tst   r1, #EXC_RETURN_FP
    bne   pendsv_handler_no_fp_restore
    vldmia r2!, {s16-s31}
pendsv_handler_no_fp_restore:
#endif /* TOPPERS_FPU_CONTEXT */
    msr   psp, r2

    /* OS 状態を「タスク実行中・OS lock 解除」に戻す */
    ldr   r2, =except_nest_cnt
    movs  r3, #0
    str   r3, [r2]
    ldr   r2, =nested_lock_os_int_cnt
    strb  r3, [r2]
    /* basepri = 0 (FAULTMASK で保護) */
    cpsid f
    msr   basepri, r3
    bx    r1                    /* EXC_RETURN → Thread モード */

return_to_thread:
    /*
     *  非 EXC_RETURN ケース (do_dispatch で保存されたコンテキスト)
     *  TCB.sp 上に r4-r11 が積まれており，TCB.pc は do_dispatch の戻り
     *  番地 (または start_r). 偽の例外フレームを PSP に積んで例外リターン
     *  することで Thread モードに復帰する.
     *  r0 = p_runtsk, r1 = TCB.pc
     *
     *  FPU を使用していたタスクは r4-r11 の下に s16-s31 が積まれている．
     *  そのままでは例外リターンで s16-s31 を復帰できないため，PC を
     *  return_to_thread_fp トランポリンに向けて HW フレームを構築し，
     *  そこで vpop {s16-s31} を行ってから本来の TCB.pc へジャンプする．
     */
#ifdef TOPPERS_FPU_CONTEXT
    ldr   r2, [r0, #TCB_fpu_flag]
    cbz   r2, return_to_thread_no_fp
    /* FPU ケース: フェイクフレームに pc=return_to_thread_fp, lr=TCB.pc */
    ldr   r2, =return_to_thread_fp
    movs  r3, #EPSR_T
    ldr   r0, [r0, #TCB_sp]
    ldmfd r0!, {r4-r11}         /* r4-r11 復帰．r0 = s16-s31 の先頭 */
    stmfd r0!, {r1, r2, r3}     /* push lr=TCB.pc, pc=return_to_thread_fp,
                                   xpsr=EPSR_T (上位 3 ワード) */
    subs  r0, #(4 * 5)          /* reserve r0-r3, r12 (未使用) */
    b     return_to_thread_0
return_to_thread_no_fp:
#endif /* TOPPERS_FPU_CONTEXT */
    ldr   r0, [r0, #TCB_sp]
    ldmfd r0!, {r4-r11}         /* r4-r11 復帰，r0 = 保存時の sp */
    movs  r2, #EPSR_T
    stmfd r0!, {r1, r2}         /* push pc=TCB.pc, xpsr (上位 2 ワード) */
    subs  r0, #(4 * 6)          /* reserve r0-r3, r12, lr (未使用) */
#ifdef TOPPERS_FPU_CONTEXT
return_to_thread_0:
#endif /* TOPPERS_FPU_CONTEXT */
    msr   psp, r0

    /* OS 状態を「タスク実行中・OS lock 状態」に戻す
     * (do_dispatch の戻り点なので呼び出し側は OS-locked 前提) */
    ldr   r2, =except_nest_cnt
    movs  r3, #0
    str   r3, [r2]
    ldr   r2, =nested_lock_os_int_cnt
    movs  r3, #1
    strb  r3, [r2]
    ldr   r2, =saved_basepri
    movs  r3, #0
    str   r3, [r2]
    /* basepri は tmin_basepri のまま */
    ldr   pc, exc_return_const

#ifdef TOPPERS_FPU_CONTEXT
    /*
     *  FPU タスク用の Thread モード復帰トランポリン
     *  例外リターンで pc=return_to_thread_fp, lr=本来の TCB.pc，
     *  PSP は s16-s31 の先頭を指す状態で到達する．
     */
    .thumb_func
return_to_thread_fp:
    vpop  {s16-s31}             /* CONTROL.FPCA もセットされる */
    bx    lr                    /* lr = TCB.pc */
#endif /* TOPPERS_FPU_CONTEXT */

return_to_idle:
    /*
     *  実行可能タスクなし: PSP に idle_loop を実行するための偽フレームを
     *  積み，例外リターンで Thread モードのアイドルへ移行する.
     */
    mrs   r0, psp
    ldr   r1, =idle_loop
    movs  r2, #EPSR_T
    stmfd r0!, {r1, r2}         /* push pc=idle_loop, xpsr=#EPSR_T */
    subs  r0, #(4 * 6)          /* reserve r0-r3, r12, lr */
    msr   psp, r0
    /* OS 状態をアイドル相当に戻す (CPU unlock) */
    ldr   r2, =except_nest_cnt
    movs  r3, #0
    str   r3, [r2]
    ldr   r2, =nested_lock_os_int_cnt
    strb  r3, [r2]
    ldr   r2, =saved_basepri
    str   r3, [r2]
    cpsid f
    msr   basepri, r3
    ldr   pc, exc_return_const

exc_return_const:
    .word EXC_RETURN


/*
 *  SVC ハンドラ
 *
 *  do_dispatch → dispatcher_0 が EXC_RETURN タスクを発見したときに
 *  Thread モードから Handler モードへ移行するために発行される.
 *  Entry: r4 = p_runtsk, r5 = TCB.pc (= EXC_RETURN 値)
 */
    .text
    .global svc_handler
    .thumb_func
    .balign FUNCTION_ALIGN_SIZE
svc_handler:
    /* OS 状態を「タスク実行中・OS lock 解除」に戻す */
    ldr   r0, =except_nest_cnt
    movs  r1, #0
    str   r1, [r0]
    ldr   r0, =nested_lock_os_int_cnt
    strb  r1, [r0]
    ldr   r0, =saved_basepri
    str   r1, [r0]
    /* basepri = 0 (FAULTMASK で保護してから) */
    cpsid f
    msr   basepri, r1

    /* r4-r11 (および必要なら s16-s31) 復帰，PSP 更新，例外リターン */
    ldr   r0, [r4, #TCB_sp]
    movs  r1, r5
    ldmfd r0!, {r4-r11}
#ifdef TOPPERS_FPU_CONTEXT
    /* TCB.pc (= 保存済 EXC_RETURN) の FType ビットで判定 */
    tst   r1, #EXC_RETURN_FP
    bne   svc_handler_no_fp_restore
    vldmia r0!, {s16-s31}
svc_handler_no_fp_restore:
#endif /* TOPPERS_FPU_CONTEXT */
    msr   psp, r0
    bx    r1


/*
 *  do_dispatch — タスクコンテキストからのディスパッチエントリ
 *
 *  C シグネチャ:
 *      void do_dispatch(TCB *p_runtsk, TCB *p_schedtsk, TCB **pp_runtsk)
 *  r0 = p_runtsk, r1 = p_schedtsk, r2 = &p_runtsk
 *
 *  OS 割込み禁止状態・ディスパッチ許可状態 (Thread モード, SPSEL=1) で
 *  呼び出される. r4-r11 と LR と PSP を p_runtsk のコンテキストに保存し
 *  dispatcher_0 へ遷移する.
 */
    .text
    .global do_dispatch
    .thumb_func
    .balign FUNCTION_ALIGN_SIZE
do_dispatch:
#ifdef TOPPERS_FPU_CONTEXT
    /*
     *  CONTROL.FPCA が 1 ならカレントタスクが FPU を使用済みなので
     *  callee-saved の s16-s31 を退避する．使用していない場合は退避不要．
     *  TCB.fpu_flag に保存量を表すフラグ (0 / CONTROL_FPCA) を残し，
     *  復帰側 (dispatcher_1 / return_to_thread) で使う．
     */
    mrs   r3, control
    ands  r3, r3, #CONTROL_FPCA
    beq   do_dispatch_no_fp
    vpush {s16-s31}               /* PSP 上に s16-s31 を保存 */
    movs  r3, #CONTROL_INIT       /* FPCA をクリア */
    msr   control, r3
    isb
do_dispatch_no_fp:
    str   r3, [r0, #TCB_fpu_flag] /* 0 または CONTROL_FPCA */
#endif /* TOPPERS_FPU_CONTEXT */
    push  {r4-r11}                /* PSP 上に callee-saved を保存 */
    str   lr, [r0, #TCB_pc]       /* TCB.pc = caller の戻り番地 */
    str   sp, [r0, #TCB_sp]       /* TCB.sp = 保存後の PSP */
    /* fall through to dispatcher_0 */


/*
 *  dispatcher_0 — ディスパッチャ本体
 *  r1 = p_schedtsk, r2 = &p_runtsk
 */
    .thumb_func
dispatcher_0:
    /*
     *  TSYS_DISALLINT がセットされていれば全割込み禁止 (PRIMASK) を解除
     *  ATK2 独自: DisableAllInterrupts() のフラグ管理
     */
    ldr   r0, =callevel_stat
    ldrh  r3, [r0]
    tst   r3, #TSYS_DISALLINT
    beq   dispatcher_0_1
    bic   r3, r3, #TSYS_DISALLINT
    strh  r3, [r0]
    cpsie i

dispatcher_0_1:
    str   r1, [r2]                /* p_runtsk = p_schedtsk */
    cbz   r1, idle_loop_entry     /* 実行可能タスクなしならアイドルへ */
    ldr   r2, [r1, #TCB_pc]
    /* 実行再開番地が EXC_RETURN なら svc #0 で Handler モードへ */
    ands  r0, r2, #EXC_RETURN_PREFIX
    cmp   r0, #EXC_RETURN_PREFIX
    bne   dispatcher_1
    /* EXC_RETURN: SVC bridge.  r1, r2 は SVC ハンドラの先頭で未定義に
     * なる可能性があるため r4, r5 へ退避してから svc を発行する */
    movs  r4, r1
    movs  r5, r2
    svc   #0
    /* SVC ハンドラから戻ってこない */


/*
 *  dispatcher_1 — Thread モードでコンテキスト復帰
 *  r1 = p_runtsk, r2 = TCB.pc
 */
    .thumb_func
dispatcher_1:
    ldr   r3, =except_nest_cnt
    movs  r0, #0
    str   r0, [r3]
    ldr   sp, [r1, #TCB_sp]       /* sp は PSP (Thread + SPSEL=1) */
    pop   {r4-r11}
#ifdef TOPPERS_FPU_CONTEXT
    /* FPU を使用していたタスクなら s16-s31 も復帰 (CONTROL.FPCA も復活) */
    ldr   r3, [r1, #TCB_fpu_flag]
    cbz   r3, dispatcher_2
    vpop  {s16-s31}
dispatcher_2:
#endif /* TOPPERS_FPU_CONTEXT */
    bx    r2


/*
 *  idle_loop_entry — dispatcher_0 から呼ばれるアイドル開始
 *
 *  Thread モード, PSP のまま wfi で待つ. ASP3 と同様に CPU lock を
 *  解除し，BASEPRI を全許可にしてから wfi に入る.
 */
    .thumb_func
idle_loop_entry:
    ldr   r3, =except_nest_cnt
    movs  r4, #0
    str   r4, [r3]
    ldr   r3, =nested_lock_os_int_cnt
    strb  r4, [r3]
    ldr   r3, =saved_basepri
    str   r4, [r3]
    msr   basepri, r4
    /* fall through */

    .thumb_func
idle_loop:
    dsb
    wfi
    b     idle_loop


/*
 *  start_dispatch — ディスパッチャの動作開始
 *
 *  カーネル起動時, 全割込み禁止 (PRIMASK=1) 状態で呼び出される.
 *  ASP3 と異なり ATK2 では非タスクコンテキスト用の OS スタック (ostkpt)
 *  を MSP に設定する.
 */
    .text
    .global start_dispatch
    .thumb_func
    .balign FUNCTION_ALIGN_SIZE
start_dispatch:
    /* MSP を OS スタック先頭に設定 */
    ldr   r0, =ostkpt
    ldr   r1, [r0]
    msr   msp, r1

    /* CONTROL.SPSEL = 1: Thread モードで PSP を使用 */
    movs  r0, #CONTROL_INIT
    msr   control, r0
    isb

    /* OS 割込み禁止状態 (BASEPRI = tmin_basepri) */
    ldr   r0, =tmin_basepri
    ldr   r0, [r0]
    msr   basepri, r0
    ldr   r0, =nested_lock_os_int_cnt
    movs  r1, #1
    strb  r1, [r0]
    ldr   r0, =saved_basepri
    movs  r1, #0
    str   r1, [r0]

    /* PRIMASK を解除 (全割込み禁止状態の解除) */
    cpsie i

    /* dispatcher_0 へ */
    ldr   r1, =p_schedtsk
    ldr   r1, [r1]
    ldr   r2, =p_runtsk
    b     dispatcher_0


/*
 *  exit_and_dispatch — 現在のコンテキストを捨ててディスパッチ
 *
 *  OS 割込み禁止状態で呼び出さなければならない.
 */
    .text
    .global exit_and_dispatch
    .thumb_func
    .balign FUNCTION_ALIGN_SIZE
exit_and_dispatch:
#ifdef TOPPERS_FPU_CONTEXT
    /* FPU コンテキストを捨てる (FPCA をクリア) */
    movs  r3, #CONTROL_INIT
    msr   control, r3
    isb
#endif /* TOPPERS_FPU_CONTEXT */
    ldr   r1, =p_schedtsk
    ldr   r1, [r1]
    ldr   r2, =p_runtsk
    b     dispatcher_0


/*
 *  start_r — タスク起動時処理
 *
 *  dispatcher_1 から TCB.pc = &start_r としてジャンプされる.
 *  OS 割込み禁止状態で呼ばれる前提だが，タスク本体は OS 割込み解除状態で
 *  動作するため，ここで CPU lock を解除する.
 */
    .text
    .global start_r
    .thumb_func
    .balign FUNCTION_ALIGN_SIZE
start_r:
    /* OS 状態を「タスク実行中・OS lock 解除」に戻す */
    ldr   r0, =nested_lock_os_int_cnt
    movs  r1, #0
    strb  r1, [r0]
    ldr   r0, =saved_basepri
    str   r1, [r0]
    msr   basepri, r1

    /* 念のため PRIMASK も解除 */
    cpsie i

    /* curpri ← exepri (ATK2 独自) */
    ldr   r0, =p_runtsk
    ldr   r0, [r0]
    ldr   r1, [r0, #TCB_p_tinib]
    ldrb  r2, [r1, #TINIB_exepri]
    strb  r2, [r0, #TCB_curpri]

    /* タスク本体が return した場合は exit_task を呼ぶ */
    ldr   lr, =exit_task
    ldr   r2, [r1, #TINIB_task]
    bx    r2


/*
 *  フック呼び出しのためのスタック管理関数
 *
 *  stack_change_and_call_func_1(func, arg1)
 *    r0 = func (void (*)(StatusType))
 *    r1 = arg1 (uint32)
 *
 *  stack_change_and_call_func_2(func, arg1, arg2)
 *    r0 = func (void (*)(StatusType, OSServiceIdType))
 *    r1 = arg1 (uint8)
 *    r2 = arg2 (uint8)
 */
    .text
    .global stack_change_and_call_func_1
    .global stack_change_and_call_func_2
    .balign FUNCTION_ALIGN_SIZE
    .thumb_func
stack_change_and_call_func_1:
    .thumb_func
stack_change_and_call_func_2:
    push  {r4, r5, lr}

    /* func を r4 に退避 */
    movs  r4, r0

    /* except_nest_cnt をインクリメント */
    ldr   r5, =except_nest_cnt
    ldr   r0, [r5]
    add   r3, r0, #1
    str   r3, [r5]

    /* 引数を設定して関数呼び出し: func(arg1, arg2) */
    movs  r0, r1
    movs  r1, r2
    blx   r4

    /* except_nest_cnt をデクリメント */
    ldr   r0, [r5]
    sub   r0, r0, #1
    str   r0, [r5]

    pop   {r4, r5, pc}
