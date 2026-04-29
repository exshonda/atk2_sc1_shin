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
 *  ARMv8-M (Cortex-M33) ハードウェア資源の定義
 */

#ifndef TOPPERS_ARM_M_H
#define TOPPERS_ARM_M_H

/*
 *  EPSRのTビット
 */
#define EPSR_T              0x01000000

/*
 *  IPSR の ISR NUMBER マスク
 */
#define IPSR_ISR_NUMBER     0x1ff

/*
 *  例外・割込み発生時にLRに設定されるEXC_RETURNの値
 *
 *  ARMv8-M Cortex-M33: Thread mode, PSP使用, 標準フレーム (FType=1) を
 *  既定とする．ハンドラから疑似フレーム経由で例外復帰させる場合に bx する値．
 *
 *  TrustZone セキュリティ状態に応じて値が変わるため，ターゲット側で
 *  下記いずれか **必ず** 1 つ define する:
 *
 *    TOPPERS_TZ_NS : Non-Secure 状態で動作 (ES=0, S=0)
 *                    例: STM32H5 で OFS1.TZEN=0 (TrustZone 無効化) の場合
 *    TOPPERS_TZ_S  : Secure 状態で動作 (ES=1, S=1)
 *                    例: RA6M5 + FSP "Flat Non-TrustZone" Project
 *                    (実際は Full Secure 動作)，または
 *                    STM32H5 で OFS1.TZEN=1 + Secure ビルド
 *
 *  どちらも未定義だと #error．両方定義は禁止．
 *
 *  EXC_RETURN[7:0] ビット詳細:
 *    bit 0 (ES) : Exception Security state — 例外ハンドラ実行時の状態
 *    bit 2 (Mode): 1=Thread, 0=Handler — pre-exception mode
 *    bit 3 (SPSEL): 1=PSP, 0=MSP — pre-exception stack
 *    bit 4 (FType): 1=Basic frame (no FP), 0=Extended (FP)
 *    bit 5 (DCRS): 1=default callee register stacking
 *    bit 6 (S)  : Secure state of pre-exception context
 *    bit 7      : Reserved, must be 1
 *    bits 31:8  : 0xFFFFFF
 *
 *  既定値の選択 (Thread + PSP + No FP + DCRS):
 *    NS: 0b1011_1100 = 0xBC → 0xFFFFFFBC
 *    S : 0b1111_1101 = 0xFD → 0xFFFFFFFD
 */
#if !defined(TOPPERS_TZ_NS) && !defined(TOPPERS_TZ_S)
#error "Define TOPPERS_TZ_NS or TOPPERS_TZ_S in target Makefile (TrustZone state)."
#endif
#if defined(TOPPERS_TZ_NS) && defined(TOPPERS_TZ_S)
#error "TOPPERS_TZ_NS and TOPPERS_TZ_S are mutually exclusive."
#endif

#ifndef EXC_RETURN
#if defined(TOPPERS_TZ_S)
#define EXC_RETURN          0xfffffffd  /* Secure: ES=1, Thread, PSP, no FP, DCRS, S=1 */
#else /* TOPPERS_TZ_NS */
#define EXC_RETURN          0xffffffbc  /* Non-Secure: ES=0, Thread, PSP, no FP, DCRS, S=0 */
#endif
#endif
#define EXC_RETURN_PREFIX   0xff000000
#define EXC_RETURN_THREAD   0x8
#define EXC_RETURN_PSP      0x4
#define EXC_RETURN_FP       0x10    /* bit 4 = FType (0:拡張, 1:標準) */

/*
 *  CONTROLレジスタ
 */
#define CONTROL_PSP         0x02
#define CONTROL_MSP         0x00
#define CONTROL_FPCA        0x04
#define CONTROL_INIT        CONTROL_PSP

/*
 *  例外番号
 */
#define EXCNO_NMI           2
#define EXCNO_HARD          3
#define EXCNO_MPU           4
#define EXCNO_BUS           5
#define EXCNO_USAGE         6
#define EXCNO_SECURE        7
#define EXCNO_SVCALL        11
#define EXCNO_PENDSV        14

/*
 *  NVICレジスタ（割込み制御と状態）
 */
#define NVIC_ICSR           0xE000ED04
#define NVIC_PENDSVSET      (1U << 28)
#define NVIC_PENDSTSET      (1U << 26)
#define NVIC_PENDSTCLR      (1U << 25)

/*
 *  ベクタテーブルオフセットレジスタ
 */
#define NVIC_VECTTBL        0xE000ED08

/*
 *  システムハンドラ優先度レジスタ
 */
#define NVIC_SYS_PRI1       0xE000ED18
#define NVIC_SYS_PRI2       0xE000ED1C
#define NVIC_SYS_PRI3       0xE000ED20

/*
 *  割込み優先度レジスタ（IRQ0〜3 分）
 */
#define NVIC_PRI0           0xE000E400

/*
 *  割込み許可/禁止レジスタ（IRQ0〜31 分）
 */
#define NVIC_SETENA0        0xE000E100
#define NVIC_CLRENA0        0xE000E180

/*
 *  割込みセット/クリアペンディングレジスタ（IRQ0〜31 分）
 */
#define NVIC_ISPR0          0xE000E200
#define NVIC_ICPR0          0xE000E280

/*
 *  システムハンドラコントロールレジスタ
 */
#define NVIC_SYS_HND_CTRL   0xE000ED24
#define NVIC_SYS_HND_CTRL_USAGE  0x00040000
#define NVIC_SYS_HND_CTRL_BUS   0x00020000
#define NVIC_SYS_HND_CTRL_MEM   0x00010000

/*
 *  FPUレジスタ
 */
#define CPACR               0xE000ED88
#define FPCCR               0xE000EF34
#define CPACR_FPU_ENABLE    0x00f00000
#define FPCCR_NO_PRESERV       0x00000000
#define FPCCR_NO_LAZYSTACKING  0x80000000
#define FPCCR_LAZYSTACKING     0xC0000000
#define FPCCR_LSPACT           0x00000001

/*
 *  FPCCRの初期値
 *  Makefile.prc が FPU_USAGE に応じて TOPPERS_FPU_NO_PRESERV /
 *  TOPPERS_FPU_NO_LAZYSTACKING / TOPPERS_FPU_LAZYSTACKING のいずれかを
 *  -D で渡す．いずれも未定義の場合は FPU 無効 (soft float) と解釈する．
 */
#if defined(TOPPERS_FPU_NO_PRESERV)
#define FPCCR_INIT          FPCCR_NO_PRESERV
#elif defined(TOPPERS_FPU_NO_LAZYSTACKING)
#define FPCCR_INIT          FPCCR_NO_LAZYSTACKING
#elif defined(TOPPERS_FPU_LAZYSTACKING)
#define FPCCR_INIT          FPCCR_LAZYSTACKING
#endif

#endif /* TOPPERS_ARM_M_H */
