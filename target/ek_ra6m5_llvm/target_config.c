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
 *  ターゲット依存モジュール（EK_RA6M5_GCC用）
 *
 *  起動経路 (start.S と整合):
 *    _kernel_start (start.S)
 *      └ hardware_init_hook()              ← BSS 初期化「前」．BSS を触らない
 *      └ BSS clear / DATA copy
 *      └ software_init_hook()              ← BSS 初期化「後」(weak default)
 *      └ main()
 *           └ StartOS()
 *                └ target_initialize()
 *                     ├ target_hardware_initialize() ← クロック/UART/GPIO
 *                     │     └ SystemInit() (FSP) を「ここで」呼ぶ
 *                     └ prc_initialize()              ← VTOR を ATK2 ベクタへ
 *
 *  この順序により FSP `SystemInit()` の BSS 依存処理 (bsp_init_uninitialized_vars)
 *  が安全に動作する．VTOR の最終確定は prc_initialize() で行うため，FSP
 *  `SystemInit()` 内の VTOR 書込み (FSP の __VECTOR_TABLE 指定) はその後
 *  上書きされる．
 */

#include "kernel_impl.h"
#include "prc_sil.h"
#include "target_sysmod.h"
#include "target_serial.h"

/*
 *  FSP BSP API (bsp_api.h は chip_config.h 経由で取り込み済み)
 *  Smart Configurator 出力 (ra_cfg/, ra_gen/) のヘッダ群が
 *  Makefile.target の INCLUDES で追加されることが前提．
 *
 *  hal_data.h: g_ioport_ctrl, g_uart_log_ctrl 等のインスタンス制御構造体宣言
 *              (Smart Configurator 生成 ra_gen/hal_data.h)．これを取り込むと
 *              ioport_cfg_t / ioport_instance_ctrl_t / R_IOPORT_* も
 *              間接的に解決される．
 */
#include "bsp_api.h"
#include "common_data.h"
#include "hal_data.h"

/*
 *  Smart Configurator 出力のシンボル
 *  Phase 2-A 完了後にビルドに含まれる (g_interrupt_event_link_select は
 *  ra_gen/vector_data.c，g_bsp_pin_cfg は ra_gen/pin_data.c で定義)．
 */
extern const bsp_interrupt_event_t g_interrupt_event_link_select[];

/*
 *  FSP startup.c からの参照を満たす最小スタブ
 *
 *  ATK2 は arch/arm_m_gcc/common/start.S をリセットエントリとし，FSP の
 *  startup.c (Reset_Handler / __VECTOR_TABLE / g_main_stack を提供) は
 *  リンクしない．ところが FSP `system.c` の SystemInit 内で次の 2 シンボル
 *  を参照するため，本層で適切な値を提供する:
 *
 *    - __VECTOR_TABLE (= __Vectors after CMSIS6 alias):
 *        SCB->VTOR = (uint32_t)&__VECTOR_TABLE で VTOR が書き換わる．
 *        ここで「空 1 entry stub + 後続ゴミ」を渡すと SystemInit 中に
 *        例外が発生した場合に壊れたハンドラへ飛んで HardFault 連鎖
 *        になる．代わりに ATK2 の kernel_vector_table (= 0x00000000，
 *        cfg pass2 生成 + .vectors セクション配置) のエイリアスに
 *        することで，SystemInit 中も常に正しい vector table が
 *        active になる．prc_initialize() が後で同アドレスへ再書込み
 *        するが no-op となる．
 *
 *    - g_main_stack[] : MSP 初期化と stack guard 用．ATK2 は既に start.S
 *                       で kernel_ostkpt を MSP に設定済み．SystemInit が
 *                       触るアドレス空間が有効でありさえすれば良い．
 *                       BSS 先頭 (.bss.g_main_stack) に配置することで
 *                       MSPLIM が SRAM 低位になり MSP との関係を保つ．
 */
/*
 *  __Vectors (= __VECTOR_TABLE after CMSIS6 alias) は
 *  リンカスクリプト r7fa6m5bh.ld で
 *      PROVIDE(__Vectors = kernel_vector_table);
 *  により kernel_vector_table のエイリアスとして定義．
 *  C 側で `extern` 宣言だけしておけば，FSP system.c が
 *  &__VECTOR_TABLE を取った時に kernel_vector_table の
 *  アドレス (= 0x00000000) が返る．
 */
#ifndef BSP_CFG_STACK_MAIN_BYTES
#define BSP_CFG_STACK_MAIN_BYTES (0x400)   /* fall-back: bsp_cfg.h と同値 */
#endif
/*
 *  g_main_stack を `.bss.g_main_stack` 専用セクションに置く．
 *  リンカスクリプト r7fa6m5bh.ld の .bss セクションで本セクションを
 *  最先頭にマッピングする．これにより `&g_main_stack[0] = __bss_start`
 *  となり，FSP system.c の `__set_MSPLIM(&g_main_stack[0])` で設定される
 *  MSPLIM が SRAM 低位 (BSS 先頭) になり，ATK2 が start.S で設定する
 *  MSP (= kernel_ostkpt．BSS 内の高位アドレス) より必ず低い状態が保証
 *  される．これを行わないと MSPLIM > MSP となり，SystemInit 中の最初の
 *  push で stack-underflow → 強制 HardFault が発生する．
 */
__attribute__((used, aligned(8), section(".bss.g_main_stack")))
uint8_t g_main_stack[BSP_CFG_STACK_MAIN_BYTES];

/*
 *  R_BSP_WarmStart のフックを ATK2 が握る場合の弱定義 override 例．
 *  target_hardware_initialize() で SystemInit() を呼ぶことで FSP の
 *  R_BSP_WarmStart(BSP_WARM_START_RESET / POST_CLOCK / POST_C) が順次
 *  呼ばれる．本ターゲットで追加処理が必要になったら以下を有効化する．
 */
#if 0
void R_BSP_WarmStart(bsp_warm_start_event_t event)
{
    if (event == BSP_WARM_START_POST_C) {
        /* C runtime 初期化後．ATK2 専用の早期ハードウェア処理が必要なら追加 */
    }
}
#endif

/*
 *  SCI7 レジスタアクセス
 *
 *  RA6M5 の R_SCI7 構造体 (R7FA6M5BH.h で定義) を使ってレジスタを直接操作する．
 *  R_SCI7 のメンバは Smart Configurator が出す `r_sci_uart.c` と整合する:
 *      SMR / BRR / SCR / TDR / SSR / RDR / SCMR / SEMR / ...
 *  非同期 (調歩同期) モードでは SMR/BRR/SCR/TDR/SSR/RDR の 8-bit レジスタ群
 *  に並ぶ．
 *
 *  Phase 2 ではレジスタ直叩きを採用．Phase 4 で FSP r_sci_uart を評価する．
 */

/* SCR bits */
#define SCR_TIE             (1U << 7U)   /* TX 割込み許可 */
#define SCR_RIE             (1U << 6U)   /* RX 割込み許可 */
#define SCR_TE              (1U << 5U)   /* TX 有効 */
#define SCR_RE              (1U << 4U)   /* RX 有効 */

/* SSR bits (非同期モード) */
#define SSR_TDRE            (1U << 7U)   /* Transmit Data Register Empty */
#define SSR_RDRF            (1U << 6U)   /* Receive Data Register Full */
#define SSR_ORER            (1U << 5U)   /* Overrun Error */
#define SSR_FER             (1U << 4U)   /* Framing Error */
#define SSR_PER             (1U << 3U)   /* Parity Error */

/*
 *  SCI7 初期化（115200bps, 8N1, RX 割込み有効）
 *
 *  クロック有効化 (MSTPCRB のビット解除) と PFS によるピン設定は
 *  本来 Smart Configurator 生成の bsp_clocks.c (R_BSP_WarmStart 内)
 *  および pin_data.c (R_IOPORT_Open) で行われる．
 *  ここでは BRR / SMR / SCR の SCI7 個別設定のみ行う．
 *
 *  BRR 計算: 非同期 baseclock = PCLKB．
 *    PCLKB = ICLK/2 = 100MHz (Smart Configurator 既定，要確認)
 *    BRR = (PCLKB / (64 / (1<<(2*n)) * baud)) - 1
 *    n=0 (デフォルト) なら: BRR = PCLKB / (32 * baud) - 1
 *                    100e6 / (32 * 115200) - 1 ≈ 26.13 → 26
 *    BRR=26 で実baud ≈ 100e6/(32*27) ≈ 115740 (誤差 +0.47%)
 *  SEMR の BGDM=1 / ABCS=1 を使えば誤差を減らせる．Phase 4 で精度向上
 *  検討．
 */
static void sci7_low_init(void)
{
    /*
     *  SCI7 モジュールクロック有効化．
     *  リセット直後 R_MSTP->MSTPCRB はすべて 1 (= 全モジュール停止) で，
     *  この状態で SCI7 レジスタに書込んでも読み出しても 0 (drop)．
     *  R_BSP_MODULE_START マクロで SCI7 (= MSTPCRB.MSTPB24) を有効化．
     */
    R_BSP_MODULE_START(FSP_IP_SCI, 7);

    /* 送受信とも一旦停止 */
    R_SCI7->SCR  = 0U;
    /* 8bit, no parity, 1 stop, /1 baseclock */
    R_SCI7->SMR  = 0U;
    /* SCMR は default のまま (SCI 互換モード) */
    R_SCI7->SCMR = 0xF2U;
    /* SEMR は default (BGDM/ABCS 未使用 → /32) */
    R_SCI7->SEMR = 0U;
    /* BRR: 100MHz / (32 * 115200) - 1 ≈ 26 */
    R_SCI7->BRR  = 26U;
    /* SSR の Error フラグをクリア (1 → 0 で書込み) */
    R_SCI7->SSR  = (uint8_t)~(SSR_ORER | SSR_FER | SSR_PER);
    /* TE | RE | RIE で送信・受信・受信割込みを有効化 */
    R_SCI7->SCR  = SCR_TE | SCR_RE | SCR_RIE;
}

/*
 *  SCI7 受信割込みハンドラ (C2ISR)
 *  target_serial.arxml で C2ISR(RxHwSerialInt) として登録．INTNO は
 *  Smart Configurator (vector_data.c) の SCI7_RXI スロットに依存 (TODO)．
 */
extern void RxSerialInt(uint8 character);

ISR(RxHwSerialInt)
{
    uint8 ssr = R_SCI7->SSR;

    /* 受信データあり (RDRF) */
    if ((ssr & SSR_RDRF) != 0U) {
        uint8 ch = R_SCI7->RDR;             /* 読み出しで RDRF クリア */
        /* SSR の RDRF は SCI7 では「読み込み後に 1 を 0 で書き戻す」必要 */
        R_SCI7->SSR = (uint8)(ssr & (uint8)~SSR_RDRF);
        RxSerialInt(ch);
    }

    /* オーバーラン等のエラーフラグはクリアしておく */
    if ((ssr & (SSR_ORER | SSR_FER | SSR_PER)) != 0U) {
        R_SCI7->SSR =
            (uint8)(ssr & (uint8)~(SSR_ORER | SSR_FER | SSR_PER));
    }

    /*
     *  RA6M5 の ICU.IELSR[N].IR を明示クリア．
     *  これをしないと NVIC が即再発火して HardFault 連鎖になる．
     *  SCI7 RXI は NVIC スロット 1 (= INTNO_SIO - 16)．
     */
    R_BSP_IrqStatusClear((IRQn_Type)(INTNO_SIO - 16U));
}

/*
 *  SCI7 1文字送信（ポーリング）
 */
static inline void sci7_putc(uint8 c)
{
    /* TDRE が立つまで待つ */
    while ((R_SCI7->SSR & SSR_TDRE) == 0U) {
    }
    R_SCI7->TDR = c;
    /* TDRE のクリアは TDR への書込みで HW が自動的に行う (RA6M5 SCI 仕様) */
}

/*
 *  文字列の出力（ポーリング，末尾に CR を追加）
 */
void
target_fput_str(const char8 *c)
{
    while (*c != '\0') {
        sci7_putc((uint8)*c);
        c++;
    }
    sci7_putc((uint8)'\r');
}

/*
 *  システムログ用の1文字出力
 */
void
target_fput_log(char8 c)
{
    sci7_putc((uint8)c);
    if (c == '\n') {
        sci7_putc((uint8)'\r');
    }
}

/*
 *  シリアル sysmod が要求するハードウェア初期化フック
 *  InitSerial() → InitHwSerial() で最初に一度だけ呼ばれる．
 */
void
InitHwSerial(void)
{
}

void
TermHwSerial(void)
{
}

/*
 *  エラーハンドラ
 */
void Error_Handler(void)
{
    Asm("cpsid i" ::: "memory");
    while (1) {
    }
}

/*
 *  ハードウェア初期化フック（start.S から最初に呼び出される）
 *
 *  start.S 内で BSS/DATA 初期化「前」に実行される．FSP `SystemInit()`
 *  は BSS 領域変数 (bsp_init_uninitialized_vars 等) を触るためここでは
 *  「呼ばない」．Phase 2-B 設計判断 (α): SystemInit を target_hardware_initialize
 *  へ移送する方式．
 *
 *  本フックでは BSS 非依存の最小処理のみ行う．現状は何もしない．
 */
void
hardware_init_hook(void)
{
    /* 何もしない (FPU 有効化は FSP SystemInit に委ねる) */
}

/*
 *  ハードウェアの初期化
 *  ATK2 StartOS() → target_initialize() から呼ばれる．BSS 初期化済みの
 *  状態で動くため，BSS 依存の FSP 初期化を安全に行える．
 *
 *  順序:
 *    1. SystemInit() で FSP のクロック/CPACR/VTOR(暫定)/WarmStart チェイン
 *    2. R_IOPORT_Open() でピン設定 (Smart Configurator 生成 g_bsp_pin_cfg)
 *    3. SCI7 low-level 初期化 (本ファイル内 sci7_low_init)
 *    4. prc_hardware_initialize() (ATK2 共通)
 */
void
target_hardware_initialize(void)
{
    /*
     *  (1) FSP SystemInit: ICLK 200MHz / VTOR(FSP)/ WarmStart チェイン
     *
     *  注: SystemInit() 内で TrustZone 対応 RA6M5 は
     *      __set_MSPLIM(&g_main_stack[0]) を実行する．本層では g_main_stack
     *      stub をリンカスクリプトで BSS 先頭に配置することで MSPLIM を
     *      SRAM 低位に固定し，ATK2 が start.S で設定する MSP (kernel_ostkpt)
     *      が常に MSPLIM より高位になるよう保証している．
     */
    SystemInit();

    /* (2) IOPORT 初期化．Smart Configurator 生成 g_bsp_pin_cfg を参照する．
     *     pin_data.c が ra_gen/ に置かれてから有効化．
     *     TODO[Phase 2-A]: g_bsp_pin_cfg を含む pin_data.c が揃ったら
     *     #if 1 へ切替 (or #define で制御)．
     */
#if defined(EK_RA6M5_USE_FSP_PINCFG)
    extern const ioport_cfg_t g_bsp_pin_cfg;
    extern ioport_instance_ctrl_t g_ioport_ctrl;
    R_IOPORT_Open(&g_ioport_ctrl, &g_bsp_pin_cfg);
#endif

    /* (3) SCI7 low-level 初期化 */
    sci7_low_init();

    /* (4) プロセッサ依存ハードウェア初期化 */
    prc_hardware_initialize();
}

/*
 *  ターゲット依存の初期化
 *  StartOS() の最初に呼び出される (kernel/osctl_manage.c)．
 *  クロック・SCI7 などのハードウェア初期化と，ARM Cortex-M33 の
 *  カーネル依存初期化 (VTOR, PendSV/SVC 優先度) をここで行う．
 *  さらに RA6M5 固有の ICU.IELSR テーブルを Smart Configurator 生成の
 *  g_interrupt_event_link_select[] からセットする．
 */
void
target_initialize(void)
{
    /* (1) クロック・SCI7・GPIO のハードウェア初期化 */
    target_hardware_initialize();

    /* (2) RA6M5 ICU.IELSR を Smart Configurator 生成テーブルから設定．
     *     これがないと NVIC スロットに紐づく事象が決まらず割込みが入らない．
     *     R_BSP_IrqCfgInit 相当の処理 (bsp_irq.c の bsp_irq_cfg) を Phase 2
     *     では target が肩代わりする (FSP 標準は Reset_Handler 経由で行うが
     *     ATK2 は start.S を使うため)．
     *
     *     ループ範囲は BSP_ICU_VECTOR_NUM_ENTRIES (= ra_cfg/.../bsp_irq_cfg
     *     で定義される)．Smart Configurator 出力が無い段階ではこのコードを
     *     有効化できないため #if defined(EK_RA6M5_HAVE_VECTOR_DATA) で囲む．
     *     Phase 2-A 完了時に Makefile.target で同マクロを定義し有効化．
     */
#if defined(EK_RA6M5_HAVE_VECTOR_DATA)
    {
        uint32_t i;
        for (i = 0U; i < BSP_ICU_VECTOR_NUM_ENTRIES; i++) {
            R_ICU->IELSR[i] = (uint32_t) g_interrupt_event_link_select[i];
        }
    }
#endif

    /* (3) ARM Cortex-M33 依存の初期化 (VTOR を ATK2 ベクタへ書換 + PendSV/SVC 優先度) */
    prc_initialize();
}

/*
 *  ターゲット依存の終了処理
 */
void
target_exit(void)
{
    target_fput_str("Kernel Exit...");

    /* 全割込み禁止 */
    prc_terminate();

    while (1) {
    }
}

/*
 *  特定の割込み要求ラインの有効/無効を制御可能かを調べる処理
 *  EK-RA6M5 では全割込みラインを制御可能
 */
boolean
target_is_int_controllable(InterruptNumberType intno)
{
    return ((intno >= TMIN_INTNO) && (intno <= TMAX_INTNO)) ? TRUE : FALSE;
}
