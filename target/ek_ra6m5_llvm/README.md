# EK-RA6M5 ターゲット依存部 (`target/ek_ra6m5_llvm`)

TOPPERS/ATK2 (SC1) の **Renesas EK-RA6M5 Evaluation Kit** ボード向け
ターゲット依存部．

ターゲット略称: `ek_ra6m5_llvm`
ボード製品ページ: <https://www.renesas.com/jp/ja/products/microcontrollers-microprocessors/ra-cortex-m-mcus/ek-ra6m5-evaluation-kit-ra6m5-mcu-group>

> **ステータス: Phase 2-B 骨格**．Phase 2-A (Smart Configurator による
> baseline 生成) は **GUI 必須のためユーザ作業** として残しており，
> `fsp/configuration.xml` は本層に未配置．Phase 2-A で
> `target/ek_ra6m5_llvm/fsp/configuration.xml` をコミットした後，clone
> 後ユーザが `rascc --generate` を実行して `fsp/ra/` `fsp/ra_cfg/`
> `fsp/ra_gen/` をローカル生成する．Phase 3 (`obj/obj_ek_ra6m5/Makefile`)
> と組み合わせてビルド可能になる．現状ファイル中の `TODO[Phase 2-A]`
> コメント部は Smart Configurator 出力に依存する暫定値．

## 1. 構成

| 層 | パス | 役割 |
|---|---|---|
| **ターゲット (本層)** | `target/ek_ra6m5_llvm/` | EK-RA6M5 ボード固有 |
| チップ依存部 | `arch/arm_m_llvm/ra_fsp/` | RA ファミリ汎用 + Renesas FSP 6.4.0 |
| プロセッサ依存部 (LLVM 用 Makefile) | `arch/arm_m_llvm/common/` | ARM LLVM (ATfE) 用ビルド設定 |
| プロセッサ依存部 (ソース) | `arch/arm_m_gcc/common/` | start.S, prc_config.{c,h}, prc_support.S 等．LLVM ビルドからは vpath で参照 (untouched) |

## 2. メモリマップ

R7FA6M5BH のメモリマップ:

| 領域 | アドレス | サイズ | 用途 |
|---|---|---|---|
| 内蔵 Flash | `0x00000000` 〜 `0x001FFFFF` | 2 MB | `.vectors` / `.text` / `.rodata` / `.data` (LMA) |
| 内蔵 SRAM | `0x20000000` 〜 `0x2007FFFF` | 512 KB | `.data` (VMA) / `.bss` / スタック |
| Option Setting Memory | `0x0100A100` 〜 | 256 B | OFS0/OFS1/OSIS (Phase 3 で扱う) |
| I/O 領域 | `0x40000000` 〜 | 256 MB | ペリフェラル |

リンカスクリプト: [`r7fa6m5bh.ld`](r7fa6m5bh.ld)．SRAM 末尾 (`_estack`)
を初期 MSP として使用．

## 3. Smart Configurator による baseline 生成 (Phase 2-A 手順)

本層は Smart Configurator が生成する `ra_cfg/` `ra_gen/`
`configuration.xml` に依存する．以下の手順で生成し，本ディレクトリに
コピーすること．

### 3.1 e² studio で新規プロジェクト作成

1. e² studio (2025-07 以降) を起動．`File → New → C/C++ Project →
   Renesas RA C/C++ Project`．
2. **Project Name**: 任意 (例: `ek_ra6m5_baseline`)．生成元としてのみ使用．
3. **Board**: `EK-RA6M5`．
4. **Toolchain**: `ARM LLVM (ATfE)`．
5. **Device**: `R7FA6M5BH3CFC`．
6. **Project Type**: `Flat (Non-TrustZone) Project`．
7. **Build Artifact / RTOS**: `No RTOS`．

### 3.2 Smart Configurator で構成

`configuration.xml` を開いて以下を設定:

| タブ | 設定 |
|---|---|
| **Clocks** | HOCO 20MHz → PLL → ICLK 200MHz, PCLKD = ICLK/2 = 100MHz |
| **Stacks → New Stack → Driver → Connectivity → r_sci_uart** | SCI3 を選択 |
| **Stacks → New Stack → Driver → Timers → r_gpt** | GPT320 (32-bit) を選択．Mode=Free Run，1 MHz は target_hw_counter.c 側で対応 |
| **Stacks → New Stack → Driver → Timers → r_gpt** | GPT321 (32-bit) を選択．Mode=One-Shot |
| **Stacks → New Stack → Driver → Input → r_ioport** | デフォルトのまま (ボード設定の pin_data を使う) |
| **Pins** | P303=RXD3 (Arduino D0 = Pin 0), P302=TXD3 (Arduino D1 = Pin 1) が AF (SCI3) になっていることを確認 |
| **Properties** | (任意) 各モジュールの Interrupt Priority を確認 |

`Generate Project Content` をクリック．

### 3.3 生成物のコピー

生成プロジェクトのワークスペースから以下を本層にコピー:

| 元 | 先 |
|---|---|
| `<workspace>/ek_ra6m5_baseline/ra_cfg/` 全体 | `target/ek_ra6m5_llvm/fsp/ra_cfg/` |
| `<workspace>/ek_ra6m5_baseline/ra_gen/` 全体 | `target/ek_ra6m5_llvm/fsp/ra_gen/` |
| `<workspace>/ek_ra6m5_baseline/configuration.xml` | `target/ek_ra6m5_llvm/fsp/configuration.xml` |
| `<workspace>/ek_ra6m5_baseline/script/fsp.ld` | (参考のみ．`r7fa6m5bh.ld` のベースとして検討) |

### 3.4 確定すべき値

`ra_gen/vector_data.c` を開き，`g_interrupt_event_link_select[]` の
順序から下記スロット番号を読み取り，対応する INTNO (= スロット + 16)
を本層各ファイルに反映する:

| 用途 | 対応イベント | コード上の場所 | 確認後の値 |
|---|---|---|---|
| シリアル受信 | `BSP_PRV_VECTOR_EVENT_SCI3_RXI` | [`target_serial.h`](target_serial.h) `INTNO_SIO`, [`target_serial.arxml`](target_serial.arxml) | TODO |
| HW カウンタ Alarm | `BSP_PRV_VECTOR_EVENT_GPT321_OVF` 相当 (GTPR 周期割込) | [`target_hw_counter.h`](target_hw_counter.h) `GPT321_INTNO`, [`target_hw_counter.arxml`](target_hw_counter.arxml) | TODO |

## 4. システムクロック・ペリフェラル

| 項目 | 値 |
|---|---|
| クロックソース | HOCO 20MHz |
| PLL | M=2, N=40 (要 Smart Configurator 確認) → ICLK 200MHz |
| ICLK | 200 MHz |
| PCLKD | 100 MHz (タイマ用) |
| PCLKB | 50 MHz (SCI 用，要 Smart Configurator 確認) |
| 電源モード | High-speed |

`ek_ra6m5.h` の `CPU_CLOCK_HZ` で 200 MHz，`PCLKD_HZ` で 100 MHz を
定数化．Smart Configurator の `bsp_clock_cfg.h` と一致させること．

### GPIO

| 信号 | ピン | 役割 | 代替機能 |
|---|---|---|---|
| SCI3_RXD | P303 (Arduino J24-D0, Pin 0) | シリアル受信 | AF (SCI3) |
| SCI3_TXD | P302 (Arduino J24-D1, Pin 1) | シリアル送信 | AF (SCI3) |
| LED1 (Blue) | P006 | (アプリ用予約) | GPIO Out |
| LED2 (Green) | P004 | (アプリ用予約) | GPIO Out |
| LED3 (Red) | P008 | (アプリ用予約) | GPIO Out |
| User SW (S2) | P009 | (未使用) | GPIO In |

### ペリフェラル

| 用途 | ペリフェラル | 詳細 |
|---|---|---|
| シリアル (SIO) | **SCI3** | 115200bps, 8N1, 割込み駆動 RX (`INTNO_SIO=TODO`, INTPRI=2) |
| ハードウェアカウンタ (フリーランニング) | **GPT320** | 32-bit, PCLKD 直結 (1MHz 換算は target_hw_counter.h の TIMER_CLOCK_HZ で調整) |
| ハードウェアカウンタ (アラーム) | **GPT321** | 32-bit, ワンショット, 割込み有効 (`GPT321_INTNO=TODO`, INTPRI=1) |

ATK2 の `MAIN_HW_COUNTER` (1us/tick) は GPT320 (現在値読出) と GPT321
(ワンショットアラーム) の組合せで実装．サンプルは 10ms 周期でタスクを
起こす `MainCycArm` アラームを構成する．

### 例外ハンドラ優先度

ARM Cortex-M33 の優先度ビット幅は 4bit (0x00 〜 0xF0):

| 用途 | 優先度 (raw) | 備考 |
|---|---|---|
| C2ISR の最高優先度 (`tmin_basepri`) | 0x10 | OS 割込み禁止の閾値 |
| GPT321 (HW カウンタアラーム) | 0x10 | INTPRI=1 |
| SCI3 RXI | 0x20 | INTPRI=2 |
| SVCall | 0xE0 | OS 割込み禁止より低 |
| PendSV | 0xFF | 最低 (tail-chain で動く) |

## 5. ターゲット定義事項

`target_kernel.h` で以下を定義:

| マクロ | 値 |
|---|---|
| `TARGET_MIN_STKSZ` | 256 (タスク最小スタック) |
| `MINIMUM_OSTKSZ` | 512 (OS スタック最小) |
| `DEFAULT_TASKSTKSZ` | 1024 |
| `DEFAULT_ISRSTKSZ` | 1024 |
| `DEFAULT_HOOKSTKSZ` | 1024 |
| `DEFAULT_OSSTKSZ` | 8192 |

`TMIN_INTNO` / `TMAX_INTNO` / `TBITW_IPRI` は
`arch/arm_m_gcc/common/prc_config.h` の値 (16 / 147 / 4) をそのまま
使用．RA6M5 は IRQ0..95 (= INTNO 16..111) しか持たないが，これは H5
の上限 147 に包含されるため `VALID_INTNO` で誤検出は起きない．

`Makefile.target` で `FPU_USAGE = FPU_LAZYSTACKING` をデフォルトに設定．

## 6. 起動経路と FSP `SystemInit()` の取扱

ATK2 の `arch/arm_m_gcc/common/start.S` は次のフローでカーネルを起動する:

```
_kernel_start:
    cpsid i
    [INIT_MSP]
    bl  hardware_init_hook    ← BSS 初期化「前」
    BSS clear
    DATA copy
    bl  software_init_hook    ← BSS 初期化「後」 (default weak)
    bl  main → StartOS → target_initialize
                          → target_hardware_initialize
                          → prc_initialize
```

FSP `SystemInit()` は内部で `bsp_init_uninitialized_vars()` 等
**BSS 領域の変数を触る**ため，**`hardware_init_hook` (BSS 前) から
呼んではならない**．本層では下記の方針 (Phase 2-B 設計判断 α):

- `hardware_init_hook()` は **空** (FPU 設定も FSP に委ねる)．
- `target_hardware_initialize()` (BSS 後，StartOS 経由) で `SystemInit()`
  を呼ぶ．これにより FSP の `bsp_init_uninitialized_vars` /
  `R_BSP_WarmStart` チェインが安全に走る．
- `prc_initialize()` で VTOR を ATK2 ベクタテーブルへ書換える．FSP
  `SystemInit()` 内の VTOR 書込みは後で上書きされるため順序を厳守:
  必ず `target_hardware_initialize` → `prc_initialize` の順．

### IELSR テーブルの設定

`target_initialize()` で Smart Configurator 生成
`g_interrupt_event_link_select[]` を `R_ICU->IELSR[]` に転記する．これが
無いと NVIC スロットに紐づくイベントが決まらず，どの割込みも入らない．

ただし FSP 生成 `vector_data.c` は `g_vector_table[]` (ATK2 と衝突) と
`g_interrupt_event_link_select[]` (必須) が同居する．本層では Phase 2-B
で下記いずれかを Phase 2-A 完了後に確定:

- **(a) 抽出方式**: `g_interrupt_event_link_select[]` だけ
  `target_irq_data.c` に転記してビルド対象に追加，`vector_data.c` は除外．
- **(b) リネーム方式**: ビルド時に `arm-none-eabi-objcopy --redefine-sym
  g_vector_table=fsp_g_vector_table_unused vector_data.o` で衝突回避．
- **(c) リンカ廃棄**: リンカスクリプトの `/DISCARD/` で FSP
  `g_vector_table[]` を破棄．

TODO[Phase 2-A]: 上記方式を確定し，`Makefile.target` を更新．現状の
`Makefile.target` は方式 (a) を仮置きしている (vector_data.o を
KERNEL_COBJS から外している)．

## 7. ファイル構成

```
target/ek_ra6m5_llvm/
├── README.md                       このファイル
├── Makefile.target                 Makefile のターゲット依存部
├── r7fa6m5bh.ld                    リンカスクリプト
├── ek_ra6m5.h                      ボード資源定義 (ピン, クロック, SCI3 ベース)
├── target_kernel.h                 カーネル設定 (スタックサイズ等)
├── target_config.c / .h            初期化・SCI3 ドライバ・ISR テーブル
├── target_serial.h                 sysmod/serial.c 用ヘッダ (INTNO_SIO 等)
├── target_serial.arxml             シリアル ISR の ATK2 cfg 定義
├── target_hw_counter.c / .h        HW カウンタ (GPT320/GPT321) ドライバ
├── target_hw_counter.arxml         HW カウンタの ATK2 cfg 定義
├── target_sysmod.h                 システムモジュール用ヘッダ
├── target_test.h                   テスト用ヘッダ
├── target_cfg1_out.h               cfg1_out.exe リンク用スタブ
├── target_rename.h / target_unrename.h  内部識別名のリネーム
├── target.tf                       pass2 ターゲット依存テンプレート
├── target_check.tf                 pass3 チェック用テンプレート
├── target_offset.tf                offset.h 生成用テンプレート
└── fsp/                            Renesas FSP 関連 (本サブツリーに集約)
    ├── configuration.xml           Smart Configurator 真値 (Phase 2-A で commit)
    ├── ra/                         rascc --generate 生成 (gitignored)
    │   └── fsp/                    FSP 本体 (inc/, src/bsp/, src/r_*/)
    ├── ra_cfg/                     rascc --generate 生成 (gitignored)
    │   └── fsp_cfg/                bsp_cfg.h, bsp_clock_cfg.h ほか
    └── ra_gen/                     rascc --generate 生成 (gitignored)
        ├── common_data.{c,h}, hal_data.{c,h}, pin_data.c, vector_data.{c,h}
```

## 8. 既知の制限・課題 (Phase 2-B 時点)

- **本層単独ではビルドできない**．`fsp/ra_cfg/fsp_cfg/bsp/bsp_cfg.h`
  `fsp/ra_gen/hal_data.c` 等が Smart Configurator 出力前提のため．
  Phase 2-A 完了後に Phase 3 (`obj/obj_ek_ra6m5/Makefile`) と組み合わせて
  ビルド可能になる．
- **`vector_data.c` の取扱方式**は Phase 2-A 完了後に (a)/(b)/(c) から
  確定．現状 `Makefile.target` の `KERNEL_COBJS` は方式 (a) を仮定．
- **INTNO 値**は暫定値．`target_serial.{h,arxml}` の `INTNO_SIO`，
  `target_hw_counter.{h,arxml}` の `GPT321_INTNO` を Smart Configurator
  生成 `vector_data.c` の実値で確定すること．
- **GPT のクロック源**は PCLKD 直結 (`TPCS=DIV1`) 固定．1MHz tick への
  分周は `TIMER_CLOCK_HZ` の最終値確定に伴って再検討．
- **`bsp_linker.c` (Option Setting Memory)** は Phase 3 で `KERNEL_COBJS`
  に追加判断．Phase 2 では未対応．
- **TrustZone (Cortex-M33 Secure 側)** は未対応．Non-Secure 単一ビルド前提．
- **R_BSP_IrqStatusClear** を ISR 側で呼ぶラッパは Phase 3 で整備．現状
  `target_config.c` の SCI3 ISR は SSR フラグクリアのみで IELSR.IR は
  クリアしていない (FSP の動作と相性確認が必要)．

## 9. バージョン履歴

- 2026-04: Phase 2-B 骨格作成．SCI3 / GPT320/321 ドライバ，リンカ
  スクリプト，cfg テンプレート一式を NUCLEO-H563ZI 版から派生．
  Smart Configurator 出力 (`ra_cfg/`, `ra_gen/`) は未取込．
