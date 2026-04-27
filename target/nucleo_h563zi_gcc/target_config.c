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
 *  ターゲット依存モジュール（NUCLEO_H563ZI_GCC用）
 */

#include "kernel_impl.h"
#include "prc_sil.h"
#include "target_sysmod.h"

/*
 *  HAL タイマティック無効化（SysTick を ATK2 が使用しないため）
 *  HAL_Init() が SysTick を設定しないよう weak 関数を上書き
 */
HAL_StatusTypeDef HAL_InitTick(uint32_t TickPriority)
{
    (void)TickPriority;
    return HAL_OK;
}

uint32_t HAL_GetTick(void)
{
    return 0U;
}

/*
 *  エラーハンドラ
 */
void Error_Handler(void)
{
    __disable_irq();
    while (1) {
    }
}

/*
 *  USART3 初期化（PD8=TX, PD9=RX, 115200bps）
 *  HAL_UART を使うと huart->Instance->CR3 アクセスで例外になる事象を踏み、
 *  ASP3 と同じ方針で USART レジスタを直接操作する低レベル実装に切り替えた。
 */
static void usart3_low_init(void)
{
    /* ---- クロック有効 ---- */
    /* GPIOD クロック (AHB2ENR.GPIODEN) */
    RCC->AHB2ENR |= RCC_AHB2ENR_GPIODEN;
    (void)RCC->AHB2ENR;
    /* USART3 クロック (APB1LENR.USART3EN) */
    RCC->APB1LENR |= RCC_APB1LENR_USART3EN;
    (void)RCC->APB1LENR;

    /* ---- GPIO PD8 (TX) / PD9 (RX) を AF7 (USART3) に設定 ---- */
    /* MODER: 10b = Alternate function */
    GPIOD->MODER  = (GPIOD->MODER  & ~((3U << (8U * 2)) | (3U << (9U * 2))))
                                    | ((2U << (8U * 2)) | (2U << (9U * 2)));
    /* OTYPER: 0 = push-pull (デフォルト) */
    GPIOD->OTYPER &= ~((1U << 8U) | (1U << 9U));
    /* OSPEEDR: 11b = Very high speed */
    GPIOD->OSPEEDR = (GPIOD->OSPEEDR & ~((3U << (8U * 2)) | (3U << (9U * 2))))
                                     | ((3U << (8U * 2)) | (3U << (9U * 2)));
    /* PUPDR: 01b = pull-up */
    GPIOD->PUPDR  = (GPIOD->PUPDR  & ~((3U << (8U * 2)) | (3U << (9U * 2))))
                                    | ((1U << (8U * 2)) | (1U << (9U * 2)));
    /* AFR[1] (= AFRH, ピン8〜15): PD8/PD9 とも AF7 */
    GPIOD->AFR[1] = (GPIOD->AFR[1] & ~((0xFU << ((8U - 8U) * 4)) | (0xFU << ((9U - 8U) * 4))))
                                   | ((7U   << ((8U - 8U) * 4)) | (7U   << ((9U - 8U) * 4)));

    /* ---- USART3 設定 ---- */
    /* いったん全停止 */
    USART3->CR1 = 0U;
    USART3->CR2 = 0U;
    USART3->CR3 = 0U;
    /* BRR (OVER8=0, USARTDIV = PCLK1 / baud)
     *   PCLK1 = 250 MHz, baud = 115200 → BRR = 250000000 / 115200 ≈ 2170 */
    USART3->BRR  = (uint32)(CPU_CLOCK_HZ / BPS_SETTING);
    /* TE | RE | UE で送信・受信・本体を有効化、RXNEIE で受信割込み有効 */
    USART3->CR1 = USART_CR1_TE | USART_CR1_RE | USART_CR1_UE
                | USART_CR1_RXNEIE_RXFNEIE;
}

/*
 *  USART3 受信割込みハンドラ (C2ISR)
 *  target_serial.arxml で C2ISR(RxHwSerialInt) として INTNO=76 に登録
 *  受信文字を sysmod/serial.c の RxSerialInt() に通知する
 */
extern void RxSerialInt(uint8 character);

ISR(RxHwSerialInt)
{
    uint32 isr_flags = USART3->ISR;

    /* 受信データあり (RXFNE/RXNE) */
    if ((isr_flags & USART_ISR_RXNE_RXFNE) != 0U) {
        uint8 ch = (uint8)(USART3->RDR & 0xFFU);   /* 読み出しで RXNE 自動クリア */
        RxSerialInt(ch);
    }

    /* オーバーラン等のエラーフラグはクリアしておく */
    if ((isr_flags & (USART_ISR_ORE | USART_ISR_FE | USART_ISR_NE | USART_ISR_PE)) != 0U) {
        USART3->ICR = USART_ICR_ORECF | USART_ICR_FECF
                    | USART_ICR_NECF  | USART_ICR_PECF;
    }
}

/*
 *  USART3 1文字送信（ポーリング）
 */
static inline void usart3_putc(uint8 c)
{
    while ((USART3->ISR & USART_ISR_TXE_TXFNF) == 0U) {
        /* TX FIFO 空きを待つ */
    }
    USART3->TDR = (uint32)c;
}

/*
 *  文字列の出力（ポーリング，末尾に改行を追加）
 */
void
target_fput_str(const char8 *c)
{
    while (*c != '\0') {
        usart3_putc((uint8)*c);
        c++;
    }
    usart3_putc((uint8)'\r');
}

/*
 *  システムログ用の1文字出力
 */
void
target_fput_log(char8 c)
{
    usart3_putc((uint8)c);
    if (c == '\n') {
        usart3_putc((uint8)'\r');
    }    
}

/*
 *  シリアル sysmod が要求するハードウェア初期化フック
 *  InitSerial() → InitHwSerial() で最初に一度だけ呼ばれる。
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
 *  ハードウェア初期化フック（start.S から最初に呼び出される）
 *
 *  start.S 内で BSS/DATA 初期化より前に実行されるため、ここでは .bss/.data
 *  に依存しない最小限の処理だけを行う。
 *  ・SystemInit(): CMSIS 標準。VTOR 設定・FPU/キャッシュ等の早期 CPU 初期化
 *
 *  クロック設定や USART 初期化など、グローバル変数を使う初期化は
 *  target_hardware_initialize() で行う（start.S は BSS 初期化後に main を呼ぶ）。
 *
 *  ASP3 の hardware_init_hook と同じ役割。
 */
void
hardware_init_hook(void)
{
    SystemInit();
}

/*
 *  ハードウェアの初期化
 *  ATK2 StartOS() から呼ばれる．クロック・周辺回路を初期化する．
 */
void
target_hardware_initialize(void)
{
    /* HAL 基本初期化（SysTick 無効，HAL_InitTick は何もしない） */
    (void)HAL_Init();

    /* システムクロックを 250MHz に設定 */
    SystemClock_Config();

    /* USART3 初期化（デバッグ出力用） */
    usart3_low_init();

    /* プロセッサ依存ハードウェア初期化 */
    prc_hardware_initialize();
}

/*
 *  ターゲット依存の初期化
 *  StartOS() の最初に呼び出される (kernel/osctl_manage.c)。
 *  クロック・USART などのハードウェア初期化と、ARM Cortex-M33 の
 *  カーネル依存初期化 (VTOR, PendSV 優先度) をここで行う。
 */
void
target_initialize(void)
{
    /* クロック・USART3 などのハードウェア初期化 */
    target_hardware_initialize();

    /* ARM Cortex-M33 依存の初期化 (VTOR, PendSV/SVC 優先度設定) */
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
 *  NUCLEO-H563ZI では全割込みラインを制御可能
 */
boolean
target_is_int_controllable(InterruptNumberType intno)
{
    return ((intno >= TMIN_INTNO) && (intno <= TMAX_INTNO)) ? TRUE : FALSE;
}
