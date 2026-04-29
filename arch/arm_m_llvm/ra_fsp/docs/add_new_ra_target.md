# 新規 RA ターゲットの追加手順

本ドキュメントは TOPPERS/ATK2 を **EK-RA6M5 以外の RA ボード** (例:
EK-RA6M4, EK-RA4M2, FPB-RA6T2 等) に展開する手順を説明する．chip 層
`arch/arm_m_llvm/ra_fsp/` は RA ファミリ汎用に設計されているため，
target 層と obj/ ビルドディレクトリだけを新設すれば良い．

## 1. 前提

- 既に EK-RA6M5 ポート (`target/ek_ra6m5_llvm/`, `obj/obj_ek_ra6m5/`) が
  存在し，動作している (Phase 4 完了相当)．
- 追加するチップが **Cortex-M33 + Renesas FSP 6.4.0** 対応であること．
  - Cortex-M85 (RA8 系) は別途 `CORE_CPU=cortex-m85` で対応可だが
    `-mfpu=fpv5-d16` 等の差異があるため動作確認が必要．
  - Cortex-M4 系 (RA6M1/M2/M3 等) は本 chip 層では未対応．`arch/arm_m_llvm/`
    系を流用しつつ別の chip ディレクトリを作るか，本 Makefile.chip を
    M4 対応に拡張する必要．

## 2. 例: EK-RA6M4 を追加する手順

以下，命名は仮 (`ek_ra6m4_llvm` とする)．

### 2.1 target 層を複製

```sh
cp -r target/ek_ra6m5_llvm target/ek_ra6m4_llvm
```

### 2.2 `Makefile.target` を更新

| 変数 | EK-RA6M5 | EK-RA6M4 |
|---|---|---|
| `TARGET` | `ek_ra6m5_llvm` | `ek_ra6m4_llvm` |
| `BOARD` | `ek_ra6m5` | `ek_ra6m4` |
| `MCU_GROUP` | `ra6m5` | `ra6m4` |
| `LDSCRIPT` | `r7fa6m5bh.ld` | `r7fa6m4af.ld` (新規作成) |

`CHIP=ra_fsp`, `PRC=arm_m`, `TOOL=llvm`, `FPU_USAGE=FPU_LAZYSTACKING` は同じ．

### 2.3 リンカスクリプトを新規作成

`r7fa6m5bh.ld` を `r7fa6m4af.ld` 等にリネームしてメモリマップを書換:

| MCU | Flash | SRAM |
|---|---|---|
| R7FA6M5BH | 2 MB @ `0x00000000` | 512 KB @ `0x20000000` |
| R7FA6M4AF | 1 MB @ `0x00000000` | 256 KB @ `0x20000000` |
| R7FA4M2AD | 1 MB @ `0x00000000` | 128 KB @ `0x20000000` |
| R7FA6T2BB | 256 KB @ `0x00000000` | 64 KB @ `0x20000000` |

(具体値は各 MCU データシートを参照)

### 2.4 ボード資源ヘッダを更新

`ek_ra6m5.h` → `ek_ra6m4.h` にリネーム，`#include` 参照箇所
(`target_serial.h`, `target_hw_counter.h`, `target_config.c`) も合わせる．

ピン定義 (LED, シリアル, User Switch) はボードごとに違うのでデータシートで
確認．

| 信号 | EK-RA6M5 | 確認すべき項目 |
|---|---|---|
| LED1/LED2/LED3 | P006/P004/P008 | ボード回路図 |
| シリアル (Arduino D0/D1) | P614/P613 (SCI7) | Arduino UNO 互換ヘッダの位置と SCI 番号 |
| User Switch | P009 | 同上 |

### 2.5 シリアル設定の確認

EK ボードシリーズは Arduino UNO 互換ヘッダの D0/D1 を共通に持つが，接続
される SCI チャンネルはボードによって異なる．User's Manual で確認．

| ボード | SCI | RX (D0) | TX (D1) |
|---|---|---|---|
| EK-RA6M5 | SCI7 | P614 | P613 |
| EK-RA6M4 | (要確認) | (要確認) | (要確認) |
| EK-RA4M2 | (要確認) | (要確認) | (要確認) |

`target_config.c` の `R_SCI7` レジスタ参照と `target_serial.h` `INTNO_SIO` を
合わせる．

### 2.6 `target/ek_ra6m4_llvm/fsp/configuration.xml` を新規生成

`phase2.md` §B の手順を新ターゲットに対して実施 (生涯一度):

1. rasc.exe を起動，新規プロジェクト
   - **Project location**: `target/ek_ra6m4_llvm/`
   - **Project name**: `fsp`
   - **Board**: 該当ボード (EK-RA6M4 / EK-RA4M2 / FPB-RA6T2 ...)
   - **Toolchain**: LLVM Embedded Toolchain for Arm (ATfE)
   - **Device**: 該当部品番号 (R7FA6M4AF3CFB / R7FA4M2AD3CFP / ...)
2. Stacks 構成:
   - `r_sci_uart`: 該当 SCI 番号 (Name = `g_uart_log`)
   - `r_gpt` (1): 32-bit Free-run, PCLKD/4 (Name = `g_timer_freerun`)
   - `r_gpt` (2): 32-bit One-Shot, PCLKD/4 (Name = `g_timer_alarm`)
   - `r_ioport` (Name = `g_ioport`)
3. Pins: ボード固有のシリアル TX/RX を AF (SCI) に
4. Generate Project Content
5. `git add target/ek_ra6m4_llvm/fsp/configuration.xml` してコミット

### 2.7 cfg テンプレートを必要に応じて調整

`target.tf`, `target_check.tf`, `target_offset.tf` は H5/RA6M5 共通でほぼ
そのまま使える．**target 固有の ISR 検証ロジック**だけ新規追加が必要なら
編集．

### 2.8 obj/ ビルドディレクトリを作成

```sh
cp -r obj/obj_ek_ra6m5 obj/obj_ek_ra6m4
sed -i 's|TARGET = ek_ra6m5_llvm|TARGET = ek_ra6m4_llvm|g' obj/obj_ek_ra6m4/Makefile
# flash, debug ターゲットの J-Link --device 値も更新
sed -i 's|R7FA6M5BH|R7FA6M4AF|g' obj/obj_ek_ra6m4/Makefile
```

### 2.9 ビルド試行

```sh
cd target/ek_ra6m4_llvm
"<RASCC>" --generate --device R7FA6M4AF3CFB --compiler LLVMARM \
    fsp/configuration.xml
cd ../../obj/obj_ek_ra6m4
make -j4
```

ビルドエラーが出たら下記の典型的問題を疑う:

| 症状 | 対処 |
|---|---|
| `bsp_cfg.h` not found | configuration.xml 取込・rascc 実行を確認．`Makefile.target` の `RA_CFG_DIR` パスが正しいか |
| `R7FA6M4AF.h` not found | rasc がデバイス指定通りに `bsp/cmsis/Device/RENESAS/Include/R7FA6M4AF.h` を生成しているか確認 |
| `bsp/mcu/ra6m4/bsp_feature.h` not found | `Makefile.target` の `MCU_GROUP=ra6m4` が正しいか，FSP がそのグループを持っているか確認 |
| INTNO 不一致 (HardFault) | `target/<T>/fsp/ra_gen/vector_data.c` の `g_interrupt_event_link_select[]` 順序を読取り，`target_serial.h` `INTNO_SIO` と `target_hw_counter.h` `GPT*_INTNO` を実値に修正 (phase2.md §E/F) |

### 2.10 README 整備

`target/ek_ra6m4_llvm/README.md` を `target/ek_ra6m5_llvm/README.md` から複製し，ボード固有値 (CPU_CLOCK_HZ, ピン割当, メモリマップ) を更新．

## 3. 同チップで複数ボード対応する場合

例えば RA6M5 でも EK-RA6M5 と CK-RA6M5 (Cloud Kit) は LED ピンや搭載セン
サが異なる．この場合は `target/ek_ra6m5_llvm/`, `target/ck_ra6m5_llvm/` の
2 つを並列に持つ．chip 層は両方から `arch/arm_m_llvm/ra_fsp/` を共有．

## 4. Cortex-M85 (RA8 系) を追加する場合の追加考慮点

`Makefile.target` で `CORE_CPU = cortex-m85` を上書き．`FPU_ARCH_OPT` は
`fpv5-d16` (M85 は double 精度 FPU) に，`FPU_ARCH_MACRO` は別マクロが
必要かもしれない．Cortex-M85 では D-Cache / I-Cache の有無で `SystemInit()`
内の処理が分岐するため，FSP の `SystemInit()` をそのまま呼べば済むはず
だが，初回は実機で動作確認が必要．

## 5. Cortex-M4 系 (RA6M1/M2/M3, RA4M1 等) を追加する場合

本 chip 層 (`arch/arm_m_llvm/ra_fsp/Makefile.chip`) は既定で `cortex-m33`
を想定している．`CORE_CPU=cortex-m4` の上書きで動作する可能性は高いが，
ARMv7-M (M4) と ARMv8-M (M33) でアセンブラ命令の差異がある．特に
`arch/arm_m_gcc/common/start.S` `prc_support.S` の中で M33 固有命令
(`bxns`, TT 命令等) を使っていれば動作しない．

確認方法:

```sh
grep -nE "armv8m|stm-m33|bxns|^\s+tt\s|^\s+sg\s" arch/arm_m_gcc/common/*.S
```

問題があれば共通プロセッサ依存部の修正 (CLAUDE.md の方針に従い，必ず
H5 副作用を確認) または別の chip 層 (`arch/arm_m_llvm/ra_fsp_cm4/`) を
新設する判断．
