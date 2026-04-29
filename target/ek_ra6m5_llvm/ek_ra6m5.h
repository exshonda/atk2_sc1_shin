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
 *  EK-RA6M5 ボードサポートヘッダ（TOPPERS ATK2用）
 *
 *  Renesas EK-RA6M5 Evaluation Kit (R7FA6M5BH 搭載)
 *  Cortex-M33 + FPU, ICLK 200MHz, PCLKD 100MHz
 */

#ifndef TOPPERS_EK_RA6M5_H
#define TOPPERS_EK_RA6M5_H

/*
 *  ターゲット名（バナーで表示）
 */
#define TARGET_NAME     "EK-RA6M5(Renesas RA6M5 Cortex-M33)"

/*
 *  コアのクロック周波数
 *    HOCO 20MHz → PLL → ICLK 200MHz が EK-RA6M5 の Smart Configurator 既定．
 *    Phase 2-A の baseline で必ずこの値になっていることを確認すること．
 */
#define CPU_CLOCK_HZ    200000000U

/*
 *  ペリフェラルクロック PCLKD (GPT320/GPT321 のクロック源)
 *    Smart Configurator 既定: ICLK/2 = 100MHz．
 *    1MHz timer tick を作るための分周比は target_hw_counter.h を参照．
 */
#define PCLKD_HZ        100000000U

/*
 *  SCI9 関連定義 (P602=TXD9, P603=RXD9, AF6 = SCI9 PSEL=00100)
 *  EK-RA6M5 の J-Link OB VCOM が SCI9 に接続．
 *  レジスタアクセスは bsp_api.h 経由で取り込む R7FA6M5BH.h の R_SCI9 を
 *  使うため，本ヘッダではベースアドレスは定義しない．
 */
#define BPS_SETTING     115200U

/*
 *  LED 定義 (EK-RA6M5 ボード仕様より)
 *    LED1 (Blue)  : P006
 *    LED2 (Green) : P004
 *    LED3 (Red)   : P008
 *  IOPORT は R_PORT0..R_PORT11．Pmnの { ポート番号 m, ピン番号 n } で表現．
 */
#define LED1_PORT       0U
#define LED1_PIN        6U

#define LED2_PORT       0U
#define LED2_PIN        4U

#define LED3_PORT       0U
#define LED3_PIN        8U

/*
 *  User Switch (S2) : P009 (アクティブ Low)
 */
#define USER_BTN_PORT   0U
#define USER_BTN_PIN    9U

#endif /* TOPPERS_EK_RA6M5_H */
