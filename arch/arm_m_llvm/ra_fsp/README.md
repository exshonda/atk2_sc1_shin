# RA + FSP チップ依存部 (`arm_m_gcc/ra_fsp`)

TOPPERS/ATK2 の **Renesas RA ファミリ (Cortex-M33 + FSP)** 向けチップ依存部．
ARM-M 共通プロセッサ依存部 (`arm_m_gcc/common`) と組み合わせて使用する．

ベンダ提供の **Renesas FSP (Flexible Software Package)** を経由して BSP /
ペリフェラルドライバを利用する．**FSP ソースは本リポジトリには同梱せず**，
clone 後にユーザが Renesas Smart Configurator (`rascc.exe`) で各ターゲット
ディレクトリ直下に生成する設計．**手順は [`docs/fsp_setup.md`](docs/fsp_setup.md) 参照．**

## 1. 対応する RA チップ

| ファミリ | コア | 動作確認 / 想定 |
|---|---|---|
| **RA6M5** (R7FA6M5BH 等) | Cortex-M33 + FPU | EK-RA6M5 (動作確認予定) |
| RA6M4 | Cortex-M33 + FPU | 想定 (chip 層変更不要) |
| RA4M2 / RA4M3 | Cortex-M33 + FPU | 想定 (chip 層変更不要) |
| RA4E1 / RA4E2 | Cortex-M33 (No FPU) | 想定 (`FPU_USAGE` 未指定でビルド) |
| RA6T2 | Cortex-M33 + FPU | 想定 |
| RA8M1 / RA8D1 / RA8T1 | Cortex-M85 + FPU | `Makefile.target` で `CORE_CPU=cortex-m85` を指定 |

ファミリ非依存部は本層に集約し，**ターゲット固有の値はすべて
`Makefile.target` の変数で渡す**．具体的には:

| Makefile.target で設定する変数 | 例 |
|---|---|
| `CHIP` (本ディレクトリ名) | `ra_fsp` |
| `MCU_GROUP` (FSP の `bsp/mcu/<group>/` に対応) | `ra6m5` / `ra6m4` / `ra4m2` / `ra6t2` / `ra8m1` 等 |
| `CORE_CPU` (省略時は `cortex-m33`) | `cortex-m33` / `cortex-m85` |
| `FPU_ARCH_OPT` (省略時は `fpv5-sp-d16`) | M33+FPU: `fpv5-sp-d16` / M85+FPU: `fpv5-d16` |
| `FPU_ARCH_MACRO` (省略時は `__TARGET_FPU_FPV5_SP`) | 同上 |

## 2. 開発環境

| ツール | 動作確認バージョン | 備考 |
|---|---|---|
| arm-none-eabi-gcc | 13.3.1 / 14.3.1 |  |
| GNU Make | 4.4.1 (msys2) |  |
| **Renesas FSP + Smart Configurator** | **6.4.0** (2025-12 リリース) | `C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/` を想定インストール先． |
| `rascc.exe` (CLI 版 Smart Configurator) | FSP 6.4.0 同梱 | 通常は `<sc_install>/eclipse/rascc.exe` |

FSP のインストールは Renesas 公式の standalone Smart Configurator パッケージ
を推奨．e² studio 同梱の Smart Configurator でも可．

## 3. ディレクトリ構成

```
arch/arm_m_gcc/ra_fsp/
├── README.md                  このファイル
├── chip_config.h              ATK2 → FSP BSP API への接続点 (#include "bsp_api.h")
├── Makefile.chip              CPU/FSP コンパイルオプション + BSP COBJS リスト
└── docs/
    └── fsp_setup.md           clone 後にユーザが実施する FSP 取込手順
```

**重要**: 本ディレクトリには `fsp/` サブツリーは存在しない．FSP 関連
ファイルはターゲットごとに `target/<TARGET>/fsp/` 配下に集約する設計．

```
target/ek_ra6m5_llvm/
├── README.md, Makefile.target, target_*.{c,h}, *.arxml, r7fa6m5bh.ld …
│                              ATK2 ターゲット依存ソース (committed)
└── fsp/                       Renesas FSP 関連 (本サブツリーに集約)
    ├── configuration.xml      Smart Configurator のソース (committed; 真値)
    ├── ra/                    rascc --generate で生成 (gitignored)
    │   └── fsp/               FSP 本体 (inc/, src/bsp/, src/r_*/)
    ├── ra_cfg/                Smart Configurator 生成 (gitignored)
    │   └── fsp_cfg/           bsp_cfg.h, bsp_clock_cfg.h ほか
    └── ra_gen/                Smart Configurator 生成 (gitignored)
        ├── common_data.{c,h}
        ├── hal_data.{c,h}
        ├── pin_data.c
        └── vector_data.{c,h}
```

`configuration.xml` を真値とし，clone 後の作業者が
`rascc --generate target/<TARGET>/fsp/configuration.xml` を 1 回実行
すれば `ra/`, `ra_cfg/`, `ra_gen/` がすべて再現される．

## 4. コンパイルオプション

`Makefile.chip` で付与する CPU/FSP オプション:

| オプション | 内容 |
|---|---|
| `-mcpu=$(CORE_CPU)` (既定 `cortex-m33`) | コア種別 |
| `-mthumb` | Thumb 命令を使用 |
| `-mlittle-endian` | リトルエンディアン (RA 標準) |
| `-D_RENESAS_RA_` | FSP が RA ファミリ判別に使う |

`-mfloat-abi` / `-mfpu` は **Makefile.prc** が `FPU_USAGE` に応じて付与．
本層では指定しない．Cortex-M33 + FPU の場合の値:

```
-mfpu=fpv5-sp-d16
-D__TARGET_FPU_FPV5_SP    (FPU 有効時のみ)
```

`R7FA6M5BH` `BSP_MCU_GROUP_RA6M5` などの **MCU 識別マクロは Smart
Configurator 生成の `bsp_cfg.h` で定義される**．`Makefile.chip` の `-D` には
書かない．

## 5. ヘッダ検索パス

`Makefile.chip` で `INCLUDES` に追加するパス:

```
$(CHIPDIR)
$(FSPDIR)/inc
$(FSPDIR)/inc/api
$(FSPDIR)/inc/instances
$(FSPDIR)/src/bsp/cmsis/Device/RENESAS/Include
$(FSPDIR)/src/bsp/mcu/all
$(FSPDIR)/src/bsp/mcu/$(MCU_GROUP)
```

ここで `$(CHIPDIR) = $(SRCDIR)/arch/arm_m_llvm/ra_fsp`,
`$(FSPDIR) = $(TARGETDIR)/fsp/ra/fsp`.

ターゲット依存部 `Makefile.target` はさらに以下を追加する:

```
$(TARGETDIR)/fsp/ra_cfg/fsp_cfg
$(TARGETDIR)/fsp/ra_cfg/fsp_cfg/bsp
$(TARGETDIR)/fsp/ra_gen
```

## 6. ATK2 と FSP の責務分担

> **本節は Phase 2 で Smart Configurator 出力を取り込み，実装を確定した
> 後に最終決定する**．以下は現時点の設計方針メモであり，ソース実装は未．

### 6.1 起動経路 (start.S 実装と整合する正確な記述)

`arch/arm_m_gcc/common/start.S` の `_kernel_start` の実体は次の流れ:

```
_kernel_start:
    cpsid i                          ; 全割込み禁止
    [INIT_MSP] msr msp, kernel_ostkpt ; (オプション) MSP 再設定
    bl  hardware_init_hook            ; ← 弱定義．BSS 初期化「前」に呼ばれる
    BSS clear
    DATA copy (ROM → RAM)
    bl  software_init_hook            ; ← 弱定義．BSS 初期化「後」に呼ばれる
    bl  main                          ; ATK2 main → StartOS → target_initialize
                                      ;             → target_hardware_initialize
                                      ;             → prc_initialize
```

**重要**: `start.S` 自体は `SystemInit()` を呼ばない．`SystemInit` を含むあらゆる
チップ初期化は **`hardware_init_hook` (BSS 前) または `target_hardware_initialize`
(BSS 後)** に配置される．

**FSP `SystemInit()` は BSS 後に呼ぶ必要がある**．FSP 6.4.0 の
`bsp/cmsis/Device/RENESAS/Source/system.c` の `SystemInit()` は H5 のような
極小実装と違って大きく，下記を順次実行する:
- `SCB->CPACR = CP_MASK` (FPU 有効化)
- `SCB->VTOR = (uint32_t) &__VECTOR_TABLE` (VTOR を FSP のベクタへ)
- `bsp_init_uninitialized_vars()` (BSS 領域変数の初期化)
- `R_BSP_WarmStart(BSP_WARM_START_RESET)`
- (内部で `bsp_clock_init` 等が呼ばれる)
- `R_BSP_WarmStart(BSP_WARM_START_POST_CLOCK)`
- `R_BSP_WarmStart(BSP_WARM_START_POST_C)`
- `__init_array_start[i]()` (C++ 静的コンストラクタ)

`bsp_init_uninitialized_vars` 以降は **BSS が 0 化されている前提** で動くため，
`hardware_init_hook` から呼ぶと未定義動作になる．したがって RA では
**`SystemInit()` の呼出を `target_hardware_initialize()` に移す**設計を採る．

### 6.2 責務分担マトリクス (Phase 2 で確定)

| 機能 | 担当 | 備考 |
|---|---|---|
| **リセットベクタ** | ATK2 (`arch/arm_m_gcc/common/start.S`) | FSP 同梱の `startup.c` は使わない |
| **早期 FPU/CPACR 設定** | target 層の `hardware_init_hook` (Phase 2) | BSS 前に動くため最小限 |
| **VTOR 設定 (ATK2 ベクタテーブルへ)** | ATK2 `prc_initialize()` (`prc_config.c`) | FSP `SystemInit()` の VTOR 書込みを ATK2 が後で上書きする方針 |
| **クロック初期化 (PLL 200 MHz 等)** | FSP `bsp_clocks.c` + `R_BSP_WarmStart` | `target_hardware_initialize` から `SystemInit()` を呼ぶ．設定値は `bsp_clock_cfg.h` (Smart Configurator 生成) |
| **C++ 静的コンストラクタ呼出** | FSP `SystemInit()` 内 (使うか未確定) | ATK2 sample は C++ 不使用なので無くて良い |
| **ベクタテーブル本体** | ATK2 cfg pass2 出力 (`Os_Lcfg.c` 内) | FSP 生成 `vector_data.c` の `g_vector_table[]` は使わない (重複定義になる) |
| **ICU.IELSR テーブル** | FSP 生成の `g_interrupt_event_link_select`(`vector_data.c` 内) | **同シンボルだけ生かしておく必要あり**．Phase 2 で抽出方法を確定 (§6.3) |
| **個々の ISR 関数** | ATK2 (cfg.arxml で登録された C2ISR) | FSP の `*_isr` 関数は呼び出さない |
| **GPIO 初期化** | FSP `r_ioport` + `R_IOPORT_Open` | Phase 2 で `target_hardware_initialize` から呼出 |
| **UART 送受信 (シリアル)** | レジスタ直叩き (第一候補) ／ FSP `r_sci_uart` (代替) | H5 ではレジスタ直叩き．RA も同方針で素直に書ける |
| **HW カウンタ (TIM2/TIM5 相当)** | レジスタ直叩き (GPT320/GPT321) | H5 流儀．`target_hw_counter.c` で実装 |

### 6.3 vector_data.c の取扱 (Phase 2 確定事項; 重要)

FSP 生成 `vector_data.c` には **2 つのシンボル**が同居する:

- `g_vector_table[]` (ARM Cortex-M ベクタテーブル) — **ATK2 と衝突するので使えない**
- `g_interrupt_event_link_select[]` (ICU.IELSR の値の配列) — **必須**．これが
  無いと `bsp_irq.c` の弱定義で全 0 にフォールバックし，IELSR が設定されない

「`vector_data.c` をビルド対象から外す」だけでは `g_interrupt_event_link_select`
も失う．Phase 2 では下記いずれかを選択:

- **(a) 抽出方式**: Smart Configurator 生成の `vector_data.c` から
  `g_interrupt_event_link_select[]` 部分だけを抽出し，`target_irq_data.c`
  という別ファイルに転記してビルド対象に追加．生成元の `vector_data.c` は
  ビルド除外．Smart Configurator 再生成時は手動で再抽出．
- **(b) リネーム方式**: `vector_data.c` は丸ごとビルドし，リンカで
  `g_vector_table` をローカル/破棄に降格させ，ATK2 側の同名シンボルを残す．
  例: `objcopy --redefine-sym g_vector_table=fsp_g_vector_table_unused vector_data.o`
  をビルドルールに挟む．Smart Configurator 再生成に強い．
- **(c) 専用セクション方式**: リンカスクリプトで FSP `g_vector_table[]` を
  `/DISCARD/` セクションに送り，ATK2 のベクタを `.isr_vector` に配置．
  Smart Configurator 出力に手を入れない最も clean な方式だが，FSP が
  `__VECTOR_TABLE` シンボルを使ってアクセスしている箇所と整合させる必要．

Phase 2 検証で (a)→(b)→(c) の順に試し，最初に通ったものを採用する．

## 7. 既知の制限・課題

- **本層単独ではコンパイルできない**．`bsp_cfg.h` `bsp_clock_cfg.h`
  `fsp_cfg.h` `vector_data.h` などが Smart Configurator 出力前提のため．
  各ターゲットで `rascc --generate` を実行した時点で全体ビルド可能になる．
  関連:
  - `BSP_MCU_GROUP_*` `BSP_MCU_R7FA*` などの MCU 識別マクロは
    `Makefile.chip` の `-D` ではなく，**Smart Configurator 生成の
    `bsp_cfg.h` 内で定義される** (target 層配下)．
  - `Makefile.chip` の `CDEFS` (`-D_RENESAS_RA_`) は FSP の chip 層単独
    コンパイルに必要な最小セット．残りの `BSP_CFG_*` 系マクロは
    `bsp_cfg.h` で供給する設計．
- **`bsp_linker.c` の Option Setting Memory (OFS0/OFS1/OSIS 等)** は
  `KERNEL_COBJS` に**含めていない**．Phase 3 でリンカスクリプトに
  `.option_setting_*` セクションを設置し，本ファイルを `KERNEL_COBJS`
  に追加する判断を行う (FSP 既定値の OFS が必要ならリンクすべし)．
- **FSP `SystemInit()` を `hardware_init_hook` から呼べない**点も Phase 2
  で扱う (§6.1 参照)．BSS 後に呼ぶ設計に切替．
- TrustZone (Cortex-M33 Secure 側) は未対応．Non-Secure 単一ビルド前提．
- Multi-core は未対応．
- DTC / DMAC など追加ドライバが必要な場合は，`configuration.xml` に Stack
  追加 → `rascc --generate` 再実行で取り込む．

## 8. ライセンス

`rascc --generate` で生成される FSP 6.4.0 のソース (`target/<T>/fsp/ra/fsp/`) は
**BSD 3-Clause License** (各 `.c`/`.h` 先頭の `SPDX-License-Identifier:
BSD-3-Clause` を参照)．Renesas Electronics Corporation 著作権表示を保つこと．

ATK2 本体および本層の薄い結合コード (`chip_config.h`, `Makefile.chip`,
`docs/`) は TOPPERS ライセンスに従う．

## 9. バージョン履歴

- 2026-04: 初版 (`ra6m5_fsp` として作成)．FSP 6.1.0 を chip 層に同梱する
  方式で Phase 1 を完了．
- 2026-04 (revised): **`ra_fsp` に rename し，FSP 同梱方式を撤回**．`rascc`
  ベースのオンデマンド生成方式に切替．FSP 6.4.0 (sc_v2025-12) を採用．RA
  ファミリ汎用構成 (MCU_GROUP/CORE_CPU 変数化)．
