# RA6M5 FSP チップ依存部 (`arm_m_gcc/ra6m5_fsp`)

TOPPERS/ATK2 の **Renesas RA6M5** ファミリ向けチップ依存部．ARM-M 共通プロ
セッサ依存部 (`arm_m_gcc/common`) と組み合わせて使用する．

ベンダ提供の **Renesas FSP (Flexible Software Package) 6.1.0** を `fsp/`
配下に同梱しており，BSP / ペリフェラルドライバはこの FSP を経由する方針．

> **ステータス: Phase 1 (骨格のみ)**．本ディレクトリは Phase 1 として
> FSP 同梱とビルド配線（`Makefile.chip`，`chip_config.h`）の骨格までを
> 提供する．Smart Configurator が生成する `bsp_cfg.h` 等のチップ構成ヘッダ
> は **本層には置かず**，ターゲット依存部 (`target/ek_ra6m5_gcc/`) の
> Phase 1B 以降で `ra_cfg/` `ra_gen/` として整備する．現時点では本層単独
> ではコンパイルできない．

## 1. 対応するチップ

- **想定**: R7FA6M5BH (EK-RA6M5 搭載品: 2 MB Flash / 512 KB SRAM, 200 MHz,
  Cortex-M33 + FPU + TrustZone)
- 同シリーズ (R7FA6M5A_ など) でも条件によっては動作見込み．

## 2. 開発環境と動作確認バージョン

| ツール | バージョン |
|---|---|
| arm-none-eabi-gcc | 13.3.1 / 14.3.1 (動作確認は Phase 1B 以降) |
| GNU Make | 4.4.1 |
| Renesas FSP | 6.1.0 (本層に同梱) |
| e² studio (構成生成用) | 2025-07 |

## 3. ディレクトリ構成

```
arch/arm_m_gcc/ra6m5_fsp/
├── README.md                  このファイル
├── chip_config.h              ATK2 → FSP BSP API への接続点
├── Makefile.chip              チップ依存ビルド定義
└── fsp/                       Renesas FSP 6.1.0 を Smart Configurator
    │                          が出力する形に倣って配置 (`ra/fsp/...`
    │                          に対応)
    ├── inc/
    │   ├── fsp_common_api.h, fsp_features.h, fsp_version.h …
    │   ├── api/               FSP 抽象 API ヘッダ (r_*_api.h)
    │   └── instances/         FSP ドライバ実体ヘッダ (r_*.h)
    ├── src/
    │   ├── bsp/               Board Support Package
    │   │   ├── cmsis/         CMSIS (Cortex-M Core + Renesas デバイス)
    │   │   │   └── Device/RENESAS/Include/R7FA6M5BH.h, system.h …
    │   │   └── mcu/
    │   │       ├── all/       全デバイス共通 BSP (bsp_clocks.c 他)
    │   │       └── ra6m5/     RA6M5 ファミリ固有 (bsp_feature.h 他)
    │   ├── r_ioport/          GPIO ドライバ
    │   ├── r_cgc/             クロック生成ドライバ
    │   ├── r_icu/             割込制御 (ICU.IELSR) ドライバ
    │   ├── r_sci_uart/        SCI UART ドライバ (target 層で使用)
    │   └── r_gpt/             GPT タイマドライバ (target 層で使用)
    ├── board/
    │   └── ra6m5_ek/          EK-RA6M5 ボード支援 (board.h, board_leds.c)
    └── script/
        └── fsp.ld             FSP 既定リンカスクリプト (参考．ターゲット
                               依存部で派生スクリプトを作成する)
```

### 3.1 同梱範囲と除外範囲

FSP pack (`Renesas.RA.6.1.0.pack`, `Renesas.RA_mcu_ra6m5.6.1.0.pack`,
`Renesas.RA_board_ra6m5_ek.6.1.0.pack`) のうち，本リポジトリに同梱した
のは下記:

| 範囲 | 同梱 | 備考 |
|---|---|---|
| `inc/` 全体 (107 API + 212 instance ヘッダ) | ✓ | 約 4.5 MB．将来追加するドライバを見据えて全部入り |
| `src/bsp/` (cmsis + mcu/all + mcu/ra6m5) | ✓ | BSP 必須 |
| `src/r_ioport`, `r_cgc`, `r_icu`, `r_sci_uart`, `r_gpt` | ✓ | Phase 2 までで使用予定の最小セット |
| `board/ra6m5_ek/` | ✓ | EK-RA6M5 ボード固有 |
| `script/fsp.ld` (`fsp.icf` 等は除く) | ✓ | GCC 用リンカスクリプト雛形 |
| `src/r_*/` (上記以外の約 200 ドライバ) | × | 必要時に上流 pack から追加コピー |
| `lib/` (precompiled libraries) | × | BLE/Motor 等．本ポートでは未使用 |
| `*.template` (USB descriptor 雛形等) | × | 未使用 |

不足ドライバは下記コマンドで上流 FSP pack から補える:

```sh
# 上流 pack から例えば r_dtc を追加
unzip -j '/c/Renesas/e2_studio_2025.07/internal/projectgen/ra/packs/Renesas.RA.6.1.0.pack' \
      'ra/fsp/src/r_dtc/*' -d arch/arm_m_gcc/ra6m5_fsp/fsp/src/r_dtc/
```

### 3.2 FSP 再生成 (アップグレード時の手順)

FSP のバージョンを更新したい場合:

1. e² studio Smart Configurator を新 FSP 版で起動．
2. 上の表で `✓` の範囲だけを `arch/arm_m_gcc/ra6m5_fsp/fsp/` に上書き．
3. `Makefile.chip` の `KERNEL_COBJS` 一覧を新版 BSP の差分に合わせて
   修正．
4. ターゲット依存部の `ra_cfg/` `ra_gen/` を再生成 (Phase 1B 以降の手順
   参照)．

## 4. コンパイルオプション

`Makefile.chip` で付与する CPU/FSP オプション:

| オプション | 内容 |
|---|---|
| `-mcpu=cortex-m33` | Cortex-M33 を指定 |
| `-mthumb` | Thumb 命令を使用 |
| `-mlittle-endian` | リトルエンディアン (RA6M5 標準) |
| `-D_RENESAS_RA_` | FSP が RA ファミリ判別に使う |
| `-D_RA_CORE=CM33` | FSP が CPU コア判別に使う |
| `-D_RA_ORDINAL=1` | RA6M5 はシングルコア．Primary core を 1 と宣言 |

`-mfloat-abi` / `-mfpu` は **Makefile.prc** が `FPU_USAGE` に応じて付与．
本層では指定しない．Cortex-M33 + FPU の場合の値は:

```
-mfpu=fpv5-sp-d16
-D__TARGET_FPU_FPV5_SP    (FPU 有効時のみ)
```

`R7FA6M5BH` は MCU 種別の指定で，`-D` で渡さず Smart Configurator 生成の
`bsp_cfg.h` 内で `#define BSP_MCU_R7FA6M5BH` の形で定義される (Phase 1B 以降)．

## 5. ヘッダ検索パス

`Makefile.chip` で `INCLUDES` に追加するパス:

```
$(CHIPDIR)
$(FSPDIR)/inc
$(FSPDIR)/inc/api
$(FSPDIR)/inc/instances
$(FSPDIR)/src/bsp/cmsis/Device/RENESAS/Include
$(FSPDIR)/src/bsp/mcu/all
$(FSPDIR)/src/bsp/mcu/ra6m5
```

ここで `$(CHIPDIR) = $(SRCDIR)/arch/arm_m_gcc/ra6m5_fsp`, `$(FSPDIR) =
$(CHIPDIR)/fsp`.

ターゲット依存部 (Phase 1B 以降) はさらに以下を `INCLUDES` に追加する:

```
$(TARGETDIR)/ra_cfg/fsp_cfg
$(TARGETDIR)/ra_cfg/fsp_cfg/bsp
$(TARGETDIR)/ra_gen
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
(BSS 後)** に配置される．H5 では `hardware_init_hook` 内で `SystemInit()` を呼ん
でいる (H5 の `SystemInit` は BSS 非依存の極小実装のため)．

**FSP `SystemInit()` は BSS 後に呼ぶ必要がある**．FSP 6.1.0 の
`bsp/cmsis/Device/RENESAS/Source/system.c` の `SystemInit()` は H5 の
それと違って大きく，下記を順次実行する (line numbers は同梱版):
- L212 `SCB->CPACR = CP_MASK` (FPU 有効化)
- L236 `SCB->VTOR = (uint32_t) &__VECTOR_TABLE` (VTOR を FSP のベクタへ)
- L270 `bsp_init_uninitialized_vars()` (BSS 領域変数の初期化)
- L274 `R_BSP_WarmStart(BSP_WARM_START_RESET)`
- (内部で `bsp_clock_init` 等が呼ばれる)
- L307 `R_BSP_WarmStart(BSP_WARM_START_POST_CLOCK)`
- L450 `R_BSP_WarmStart(BSP_WARM_START_POST_C)`
- L494 `__init_array_start[i]()` (C++ 静的コンストラクタ)

L270/L274 以降は **BSS が 0 化されている前提** で動くため，
`hardware_init_hook` から呼ぶと未定義動作になる．したがって RA6M5 では
**`SystemInit()` の呼出を `target_hardware_initialize()` に移す**か，
あるいは **FSP `SystemInit()` を採用せず target 専用の薄い `SystemInit`
相当を `hardware_init_hook` に書く**かのいずれかを Phase 2 で選択する．

### 6.2 責務分担マトリクス (Phase 2 で確定)

| 機能 | 担当 | 備考 |
|---|---|---|
| **リセットベクタ** | ATK2 (`arch/arm_m_gcc/common/start.S`) | FSP 同梱の `startup.c` は使わない |
| **早期 FPU/CPACR 設定** | target 層の `hardware_init_hook` (Phase 2) | BSS 前に動くため最小限 |
| **VTOR 設定 (ATK2 ベクタテーブルへ)** | ATK2 `prc_initialize()` (`prc_config.c`) | FSP `SystemInit()` の VTOR 書込みを ATK2 が後で上書きする方針 |
| **クロック初期化 (PLL 200 MHz)** | FSP `bsp_clocks.c` + `R_BSP_WarmStart` | `target_hardware_initialize` から `R_BSP_WarmStart(BSP_WARM_START_POST_CLOCK)` 等を駆動，もしくは FSP `SystemInit()` を BSS 後に呼ぶ．設定値は `bsp_clock_cfg.h` (Smart Configurator 生成) |
| **C++ 静的コンストラクタ呼出** | FSP `SystemInit()` 内 (使うか未確定) | ATK2 sample は C++ 不使用なので無くて良い |
| **ベクタテーブル本体** | ATK2 cfg pass2 出力 (`Os_Lcfg.c` 内) | FSP 生成 `vector_data.c` の `g_vector_table[]` は使わない (重複定義になる) |
| **ICU.IELSR テーブル** | FSP 生成の `g_interrupt_event_link_select`(`vector_data.c` 内) | **同シンボルだけ生かしておく必要あり**．Phase 2 で抽出方法を確定 (§6.3) |
| **個々の ISR 関数** | ATK2 (cfg.arxml で登録された C2ISR) | FSP の `*_isr` 関数は呼び出さない |
| **GPIO 初期化** | FSP `r_ioport` + `R_IOPORT_Open` | Phase 2 で `target_hardware_initialize` から呼出 |
| **UART 送受信 (シリアル)** | レジスタ直叩き (第一候補) ／ FSP `r_sci_uart` (代替) | H5 ではレジスタ直叩き．RA6M5 も同方針で素直に書ける |
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

## 7. 既知の制限・課題 (Phase 1 時点)

- **本層単独ではコンパイルできない**．`bsp_cfg.h` `bsp_clock_cfg.h`
  `fsp_cfg.h` `vector_data.h` などが Smart Configurator 出力前提のため．
  Phase 2 でターゲット依存部の `ra_cfg/` `ra_gen/` を整備した時点で
  全体ビルド可能になる．関連:
  - `BSP_MCU_GROUP_RA6M5` `BSP_MCU_R7FA6M5BH` などの MCU 識別マクロは
    `Makefile.chip` の `-D` ではなく，**Smart Configurator 生成の
    `bsp_cfg.h` 内で定義される** (target 層配下)．本 README で当初
    `Makefile.chip` 配下と書いていたのは誤り．
  - `Makefile.chip` の `CDEFS` (`-D_RENESAS_RA_ -D_RA_CORE=CM33
    -D_RA_ORDINAL=1`) は FSP 6.1.0 の chip 層単独コンパイルに必要な最小
    セット．残りの `BSP_CFG_*` 系マクロは `bsp_cfg.h` で供給する設計．
- **`bsp_linker.c` の Option Setting Memory (OFS0/OFS1/OSIS 等)** は
  `KERNEL_COBJS` に**含めていない**．Phase 3 でリンカスクリプトに
  `.option_setting_*` セクションを設置し，本ファイルを `KERNEL_COBJS`
  に追加する判断を行う (FSP 既定値の OFS が必要ならリンクすべし)．
- **FSP `SystemInit()` を `hardware_init_hook` から呼べない**点も Phase 2
  で扱う (§6.1 参照)．BSS 後に呼ぶ設計に切替．
- TrustZone (Cortex-M33 Secure 側) は未対応．Non-Secure 単一ビルド前提．
- Multi-core は未対応 (RA6M5 はシングルコアなので問題なし)．
- DTC / DMAC は同梱していない．必要時に上流 pack からコピー．

## 8. ライセンス

同梱 FSP 6.1.0 のソースは **BSD 3-Clause License** (各 `.c`/`.h` 先頭の
`SPDX-License-Identifier: BSD-3-Clause` を参照)．Renesas Electronics
Corporation 著作権表示を保つこと．

ATK2 本体および本層の薄い結合コード (`chip_config.h`, `Makefile.chip`) は
TOPPERS ライセンスに従う．

## 9. バージョン履歴

- 2026-04: Phase 1 (骨格) 作成．FSP 6.1.0 を `fsp/` 配下に取り込み，
  `Makefile.chip` `chip_config.h` を整備．コンパイル検証は Phase 1B
  以降に持ち越し．
