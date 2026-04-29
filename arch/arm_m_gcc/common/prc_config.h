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
 *
 *  このインクルードファイルは target_config.h（または，そこからインク
 *  ルードされるファイル）のみからインクルードされる
 */

#ifndef TOPPERS_PRC_CONFIG_H
#define TOPPERS_PRC_CONFIG_H

#include "arm_m.h"

/*
 *  エラーチェック方法の指定
 */
#define CHECK_STKSZ_ALIGN   8   /* スタックサイズのアライン単位（8バイト） */
#define CHECK_FUNC_ALIGN    4   /* 関数のアライン単位 */
#define CHECK_FUNC_NONNULL      /* 関数の非NULLチェック */
#define CHECK_STACK_ALIGN   8   /* スタック領域のアライン単位 */
#define CHECK_STACK_NONNULL     /* スタック領域の非NULLチェック */

/*
 *  アセンブラのメモリ配置設定
 */
#ifndef FUNCTION_ALIGN_SIZE
#define FUNCTION_ALIGN_SIZE 4
#endif /* FUNCTION_ALIGN_SIZE */

/*
 *  割込み番号と割込み優先度ビット幅は **チップ依存** のため，本層では
 *  定義しない．チップ依存部 (chip_config.h) で以下を必ず定義すること:
 *
 *    TMIN_INTNO  : 最小割込み番号 (Cortex-M ではほぼ常に IRQ0 = 例外 16)
 *    TMAX_INTNO  : 最大割込み番号 (= IRQ最大番号 + 16)
 *    TNUM_INT    : 割込み番号の個数 (= TMAX_INTNO - TMIN_INTNO + 1)
 *    TBITW_IPRI  : NVIC IPR の優先度ビット幅 (Cortex-M33/M85 は通常 4)
 *
 *  この prc_config.h は target_config.h → chip_config.h 経由で取込まれ，
 *  かつ chip_config.h が末尾でこのファイルを include する設計のため，
 *  ここでは未定義のまま使用すれば良い (下記 VALID_INTNO / INT_IPM /
 *  EXT_IPM マクロの本体は使用時に展開される)．
 */

/*
 *  エラーフック呼び出しとシャットダウンフック呼び出し
 */
#define call_errorhook(ercd, svcid)     stack_change_and_call_func_2(&internal_call_errorhook, (ercd), (svcid))
#define call_shutdownhook(ercd)         stack_change_and_call_func_1(&internal_call_shtdwnhk, ((uint32) (ercd)))

/*
 *  割込み番号の範囲の判定
 */
#define VALID_INTNO(intno)  (((InterruptNumberType)(TMIN_INTNO) <= (intno)) \
                             && ((intno) <= (InterruptNumberType)(TMAX_INTNO)))

/*
 *  割込み番号からIRQ番号への変換（INTNO = IRQno + 16）
 */
#define INTNO_TO_IRQNO(intno)   ((intno) - 16U)

/*
 *  割込み番号からNVIC許可/禁止レジスタへのビットパターン
 */
#define INTNO_TO_NVIC_REG(intno)   ((volatile uint32 *)(NVIC_SETENA0) \
                                     + (INTNO_TO_IRQNO(intno) / 32U))
#define INTNO_TO_NVIC_CLRREG(intno) ((volatile uint32 *)(NVIC_CLRENA0) \
                                     + (INTNO_TO_IRQNO(intno) / 32U))
#define INTNO_TO_NVIC_BIT(intno)   (1U << (INTNO_TO_IRQNO(intno) % 32U))

/*
 *  割込み番号からNVIC優先度レジスタアドレスへの変換
 */
#define INTNO_TO_PRI_ADDR(intno)   ((volatile uint8 *)(NVIC_PRI0) \
                                    + INTNO_TO_IRQNO(intno))

#ifndef TOPPERS_MACRO_ONLY

/*
 *  非タスクコンテキスト用のスタック開始アドレス設定マクロ
 */
#define TOPPERS_OSTKPT(stk, stksz)  ((StackType *)((sint8 *)(stk) + (stksz)))

/*
 *  プロセッサの特殊命令のインライン関数定義
 */
#include "prc_insn.h"

/*
 *  例外（割込み/CPU例外）のネスト回数のカウント
 */
extern uint32       except_nest_cnt;

/*
 *  OS割込み禁止時のBASEPRI設定値（cfg toolが生成）
 *  tmin_basepri = INT_IPM(MIN_PRI_ISR2)
 */
extern const uint32 tmin_basepri;

/*
 *  割込み優先度マスクの内部表現(BASEPRI値)と外部表現(PriorityType)の変換
 *
 *  TBITW_IPRI=4の場合:
 *    INT_IPM(-1)  = (16-1)<<4 = 0xF0  (最低OS優先度 → 最大BASEPRI)
 *    INT_IPM(-15) = (16-15)<<4 = 0x10 (最高OS優先度 → 最小BASEPRI)
 */
#define INT_IPM(ipm) \
    ((uint32)(((uint32)(1U << TBITW_IPRI) \
               - (uint32)(-(PriorityType)(ipm))) << (8U - TBITW_IPRI)))

#define EXT_IPM(iipm) \
    (-((PriorityType)((uint32)(1U << TBITW_IPRI) \
                     - ((uint32)(iipm) >> (8U - TBITW_IPRI)))))

/*
 *  OS割込み禁止状態の時に割込み優先度マスクを保存する変数
 */
extern volatile uint32  saved_basepri;

/*
 *  x_nested_lock_os_int() のネスト回数
 */
extern volatile uint8   nested_lock_os_int_cnt;

/*
 *  全割込み禁止状態への移行（PRIMASKを使用）
 */
LOCAL_INLINE void
x_lock_all_int(void)
{
    Asm("cpsid i" ::: "memory");
}

/*
 *  全割込み禁止状態の解除
 */
LOCAL_INLINE void
x_unlock_all_int(void)
{
    Asm("cpsie i" ::: "memory");
}

/*
 *  OS割込み禁止
 *  BASEPRIをtmin_basepriに設定することでC2ISRを禁止する
 */
LOCAL_INLINE void
x_nested_lock_os_int(void)
{
    uint32 basepri;

    if (nested_lock_os_int_cnt == 0U) {
        basepri = get_basepri();
        set_basepri(tmin_basepri);
        saved_basepri = basepri;
    }
    nested_lock_os_int_cnt++;
    Asm("" ::: "memory");
}

/*
 *  OS割込み解除
 */
LOCAL_INLINE void
x_nested_unlock_os_int(void)
{
    Asm("" ::: "memory");
    ASSERT(nested_lock_os_int_cnt > 0U);
    nested_lock_os_int_cnt--;
    if (nested_lock_os_int_cnt == 0U) {
        set_basepri(saved_basepri);
    }
}

/*
 *  (モデル上の)割込み優先度マスクの設定
 *  OS割込み禁止状態で呼び出される
 */
LOCAL_INLINE void
x_set_ipm(PriorityType intpri)
{
    ASSERT(nested_lock_os_int_cnt > 0U);
    saved_basepri = INT_IPM(intpri);
}

/*
 *  (モデル上の)割込み優先度マスクの参照
 *  OS割込み禁止状態で呼び出される
 */
LOCAL_INLINE PriorityType
x_get_ipm(void)
{
    ASSERT(nested_lock_os_int_cnt > 0U);
    return(EXT_IPM(saved_basepri));
}

/*
 *  指定された割込み番号の割込みを禁止する（NVICを使用）
 */
LOCAL_INLINE void
x_disable_int(InterruptNumberType intno)
{
    *INTNO_TO_NVIC_CLRREG(intno) = INTNO_TO_NVIC_BIT(intno);
}

/*
 *  指定された割込み番号の割込みを許可する（NVICを使用）
 */
LOCAL_INLINE void
x_enable_int(InterruptNumberType intno)
{
    *INTNO_TO_NVIC_REG(intno) = INTNO_TO_NVIC_BIT(intno);
}

/*
 *  割込み要求ラインの属性の設定
 */
extern void x_config_int(InterruptNumberType intno, AttributeType intatr,
                          PriorityType intpri);

/*
 *  割込みハンドラの入り口/出口で必要なIRC操作（NVICは自動管理）
 */
LOCAL_INLINE void
i_begin_int(InterruptNumberType intno)
{
    (void)intno;
}

LOCAL_INLINE void
i_end_int(InterruptNumberType intno)
{
    (void)intno;
}

/*
 *  未定義の割込みが入った場合の処理
 */
extern void default_int_handler(void);

extern void prc_hardware_initialize(void);

/*
 *  プロセッサ依存の初期化
 */
extern void prc_initialize(void);

/*
 *  プロセッサ依存の終了時処理
 */
extern void prc_terminate(void);

/*
 *  最高優先順位タスクへのディスパッチ（prc_support.S）
 *
 *  ASP3 の _kernel_dispatch() と同等．タスクコンテキストから呼び出され
 *  たサービスコール処理内で，OS 割込み禁止状態で呼び出さなければなら
 *  ない．
 *
 *  dispatch() マクロは，p_runtsk と p_schedtsk を引数として do_dispatch()
 *  に渡すことで効率化している．
 */
extern void do_dispatch(void *p_runtsk_arg, void *p_schedtsk_arg,
                        void *pp_runtsk);

#define dispatch()  do_dispatch(p_runtsk, p_schedtsk, &p_runtsk)

/*
 *  ディスパッチャの動作開始（prc_support.S）
 *
 *  カーネル起動時に呼び出す，すべての割込みを禁止した状態で呼び出す
 */
extern void start_dispatch(void) NoReturn;

/*
 *  現在のコンテキストを捨ててディスパッチ（prc_support.S）
 *
 *  OS割込み禁止状態で呼び出さなければならない
 */
extern void exit_and_dispatch(void) NoReturn;

/*
 *  タスクコンテキストブロックの定義
 *
 *  fpu_flag は TOPPERS_FPU_CONTEXT 有効時のみ意味を持つ:
 *    0           : このタスクは FPU を未使用 (s16-s31 を保存していない)
 *    CONTROL_FPCA: FPU 使用済み (s16-s31 を TCB.sp の下に保存している)
 *  TOPPERS_FPU_CONTEXT が未定義のときも 4 バイト分のフィールドだけ
 *  確保しておく (cfg ツールの offsetof 計算とビルド条件分岐の単純化のため)．
 */
typedef struct task_context_block {
    void            *sp;        /* スタックポインタ（PSP） */
    FunctionRefType  pc;        /* プログラムカウンタまたはEXC_RETURN値 */
    uint32           fpu_flag;  /* FPU レジスタを復帰するかのフラグ */
} TSKCTXB;

/*
 *  タスクコンテキストの初期化
 *
 *  activate_contextをマクロ定義としているのは，この時点でTCBが
 *  定義されていないためである
 */
extern void start_r(void);

/*
 *  ディスパッチャ (dispatcher_1) は pop {r4-r11} で 8 ワード分のレジスタ
 *  を復帰する．新タスクの SP はスタック先頭から 8 ワード (= 32 バイト)
 *  下げておく必要がある．ASP3 と同じく uint32 * のポインタ演算にして
 *  - 8 と書く．fpu_flag は新タスクが FPU レジスタを未使用であることを
 *  表す 0 で初期化する．
 */
#define activate_context(p_tcb) do { \
    (p_tcb)->tskctxb.sp = (uint32 *)((char8 *)((p_tcb)->p_tinib->stk) \
                                     + (p_tcb)->p_tinib->stksz) - 8; \
    (p_tcb)->tskctxb.pc = (FunctionRefType) &start_r; \
    (p_tcb)->tskctxb.fpu_flag = 0U; \
} while (0)

/*
 *  フック呼び出しのためのスタック切り替え関数（prc_support.S）
 */
extern void stack_change_and_call_func_1(void (*func)(StatusType ercd),
                                          uint32 arg1);

extern void stack_change_and_call_func_2(void (*func)(StatusType ercd,
                                                       OSServiceIdType svcid),
                                          uint8 arg1, uint8 arg2);

#endif /* TOPPERS_MACRO_ONLY */

#endif /* TOPPERS_PRC_CONFIG_H */
