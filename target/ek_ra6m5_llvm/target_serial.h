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
 *      シリアルI/Oデバイス（SIO）ドライバ（EK_RA6M5用）
 *
 *  EK-RA6M5 の Arduino-UNO 互換ヘッダ J24 の D0 (Pin 0, RX) / D1 (Pin 1, TX)
 *  を使用．これは SCI7 (P614 = RXD7, P613 = TXD7) に接続される．
 *  ボーレート 115200 bps, 8N1, ISR 駆動 RX．
 *
 *    USB-UART 変換アダプタ (FTDI 等) を J24-D0/D1 に接続して使用．
 *    J-Link OB 経由の VCOM (= SCI9) は今回使用しない．
 *
 *  SCI7 を target_config.c で直接初期化しているため，ここでは
 *  sample1 が要求する INTNO_SIO / INTPRI_SIO のみを定義する．
 */

#ifndef TOPPERS_TARGET_SERIAL_H
#define TOPPERS_TARGET_SERIAL_H

#include "ek_ra6m5.h"

/*
 *  SCI7 受信割込みのベクタ番号 / 割込み優先度
 *
 *  ★★★ TODO[Phase 2-A 必須]: 暫定値 — Smart Configurator 出力受領後に
 *                              必ず実値に置き換えること ★★★
 *
 *  RA6M5 の NVIC スロット番号は Smart Configurator (vector_data.c) が
 *  決定する．Phase 2-A 完了後，target/ek_ra6m5_llvm/ra_gen/vector_data.c
 *  の `g_interrupt_event_link_select[]` 配列を開き，SCI7_RXI が割り当て
 *  られている配列インデックス N を確認．下記 `INTNO_SIO` を `N + 16`
 *  (= 例外番号) に修正．`target_serial.arxml` の `<VALUE>` も同値に
 *  合わせること．**INTNO 不一致のまま実機実行すると別ペリフェラルの
 *  ISR が呼ばれて HardFault になる**．
 *
 *  暫定値 16 (= IRQ0) は cfg ツールがビルドエラーを起こさないための
 *  ダミー．Phase 2-A を経ずに実機書込みするのは禁止．
 */
#define INTNO_SIO       UINT_C(16)   /* TODO[Phase 2-A]: 暫定 IRQ0．要修正 */
#define INTPRI_SIO      UINT_C(2)

#ifndef TOPPERS_MACRO_ONLY

/*
 *  H/W シリアルの初期化／終了処理
 *  target_config.c で定義．sysmod/serial.c の InitSerial / TermSerial
 *  から呼ばれる．
 */
extern void InitHwSerial(void);
extern void TermHwSerial(void);

#endif /* TOPPERS_MACRO_ONLY */

#endif /* TOPPERS_TARGET_SERIAL_H */
