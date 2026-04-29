# RA + FSP チップ依存部 (`arm_m_gcc/ra_fsp`)

TOPPERS/ATK2 の **Renesas RA ファミリ (Cortex-M33 + FSP)** 向けチップ依存部．
ARM-M 共通プロセッサ依存部 (`arm_m_gcc/common`) と組み合わせて使用する．

ベンダ提供の **Renesas FSP (Flexible Software Package)** を経由して BSP /
ペリフェラルドライバを利用する．**FSP ソースは本リポジトリには同梱せず**，
clone 後にユーザが Renesas Smart Configurator (`rascc.exe`) で各ターゲット
ディレクトリ直下に生成する設計．**手順は [`docs/fsp_setup.md`](docs/fsp_setup.md) 参照．**

## 1. 対応する RA チップ

本層は **Cortex-M33 + 96-slot ICU** 構成の RA を対象とする．以下は同形
ハードウェアを持つことから流用想定だが，動作確認は RA6M5 のみ．

| ファミリ | コア | 動作確認 / 想定 |
|---|---|---|
| **RA6M5** (R7FA6M5BH 等) | Cortex-M33 + FPU | EK-RA6M5 (Phase 4 で実機確認済) |
| RA6M4 | Cortex-M33 + FPU | 流用想定 (未確認; chip 層変更不要) |
| RA4M2 / RA4M3 | Cortex-M33 + FPU | 流用想定 (未確認; chip 層変更不要) |
| RA4E1 / RA4E2 | Cortex-M33 (No FPU) | 流用想定 (未確認; `FPU_USAGE` 未指定) |
| RA6T2 | Cortex-M33 + FPU | 流用想定 (未確認) |

**対象外** (本 chip 層では扱わない):

| ファミリ | コア | 理由 |
|---|---|---|
| RA8M1 / RA8D1 / RA8T1 | Cortex-M85 + FPU | ICU 128 スロット．`chip_config.h` / `chip.tf` の `TMAX_INTNO=111` / `TNUM_INT=96` および `INTNO_VALID={16..111}` が合わない．chip 層をフォークするか，`MCU_GROUP` 分岐を導入する必要がある |
| RA2 系 | Cortex-M23 | `BASEPRI` 非搭載のため OS 割込み禁止が動作しない (PRC 層が要求) |

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
| **ARM LLVM (ATfE) clang** | **21.1.1** (Renesas e² studio v2025-12 同梱) | `C:/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin/clang.exe`．`--target=arm-none-eabi` で ARM ELF を生成． |
| GNU Make | 4.4.1 (msys2) |  |
| **Renesas FSP + Smart Configurator** | **6.4.0** (2025-12 リリース) | `C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/` を想定インストール先． |
| `rascc.exe` (CLI 版 Smart Configurator) | FSP 6.4.0 同梱 | 通常は `<sc_install>/eclipse/rascc.exe` |

FSP のインストールは Renesas 公式の standalone Smart Configurator パッケージ
を推奨．e² studio 同梱の Smart Configurator でも可．

## 3. ディレクトリ構成

```
arch/arm_m_llvm/ra_fsp/
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

### 6.3 vector_data.c の取扱 (重要; EK-RA6M5 では方式 (a) を採用)

#### なぜこの仕組みが必要か

RA ファミリの NVIC スロット 0..95 には **固定配線がない**．スロット n
にどの RA ペリフェラルイベント (`SCI7_RXI`, `GPT0_OVERFLOW`, ...) が
入るかは ICU.IELSR[n] レジスタで実行時に決まる．Smart Configurator が
ユーザの選択を `g_interrupt_event_link_select[]` 配列に焼き，FSP の
`bsp_irq_cfg()` が起動時にその配列を `R_ICU->IELSR[]` に書込むことで
NVIC スロットと RA イベントが繋がる．

一方 FSP の `vector_data.c` には **2 つのシンボルが同居** している:

| シンボル | 用途 | ATK2 との関係 |
|---|---|---|
| `g_vector_table[]` | ARM Cortex-M ベクタテーブル本体 | **衝突する**．ATK2 cfg pass2 が `Os_Lcfg.c` に同じ機能のテーブルを生成しており，どちらか一方しかリンクできない |
| `g_interrupt_event_link_select[]` | ICU.IELSR への書込み元データ | **必須**．無いと `bsp_irq.c` の弱定義 `__weak ... = {0}` にフォールバックし，全スロットが未配線になる結果，どの割込みも届かない |

つまり「`vector_data.c` をビルド対象から外す」だけでは衝突は回避できても
肝心の IELSR テーブルも失う．何らかの形で
`g_interrupt_event_link_select[]` 部分だけを救出しなければならない．

#### 採用方式: (a) 抽出方式 (EK-RA6M5)

EK-RA6M5 では **方式 (a)** を採用している．Smart Configurator 生成の
`vector_data.c` から `g_interrupt_event_link_select[]` 部分だけを切り出して
`target/ek_ra6m5_llvm/target_irq_data.c` に転記し，元の `vector_data.c`
は `Makefile.target` の `KERNEL_COBJS` から外す．

##### 割込みの追加・INTNO 変更時の手順

1. Smart Configurator (e² studio または rasc.exe) で
   `target/ek_ra6m5_llvm/fsp/configuration.xml` を開く．
2. **Stacks** タブで対象モジュール (例: `g_uart_log`) の Properties →
   **Interrupts** で必要な割込み (RXI, TXI, TEI, ERI 等) を Enable / Priority
   設定．Pin 設定が必要なら **Pins** タブ も合わせて編集．
3. `File → Save` で `configuration.xml` を上書き保存．
4. シェルから:
   ```sh
   "$RASCC" --generate target/ek_ra6m5_llvm/fsp/configuration.xml
   ```
   これで `target/ek_ra6m5_llvm/fsp/ra_gen/vector_data.c` が再生成される．
5. **新しい `vector_data.c` を開いて `g_interrupt_event_link_select[]` の
   配列リテラル部分をそのままコピーし**，
   `target/ek_ra6m5_llvm/target_irq_data.c` の同名配列に貼り付ける．
   配列要素のイベント名 (`BSP_PRV_VECTOR_EVENT_*`) はそのまま使える．
6. 新たに割当てられた **NVIC スロット番号 = 配列インデックス**を確認し，
   対応する **INTNO = スロット番号 + 16** を以下に反映:
   - `target/ek_ra6m5_llvm/target_serial.h` の `INTNO_SIO`
     (シリアル割込みを変えた場合)
   - `target/ek_ra6m5_llvm/target_hw_counter.h` の `GPT321_INTNO`
     (HW カウンタ割込みを変えた場合)
   - 新規割込みの場合は対応する `target_*.{h,arxml}` を新設し，
     ARXML 側でも INTNO を一致させる．
7. `obj/obj_ek_ra6m5/` で `make clean && make -j4` してリビルド．pass3
   が ARXML の INTNO と実 INTNO の一致を検証する．

##### 設計上のトレードオフ

| 方式 | 利点 | 欠点 |
|---|---|---|
| **(a) 抽出方式 (採用)** | リンカスクリプトとビルドルールに手を入れない最小変更．動作中の挙動が分かりやすい | Smart Configurator 再生成時に手動コピーが必要 |
| (b) リネーム方式 | Smart Configurator 再生成に強い．`objcopy --redefine-sym g_vector_table=fsp_g_vector_table_unused vector_data.o` でビルド時に潰す | ビルドルールが煩雑になる．clang/lld でも `objcopy` 同等の機能が必要 |
| (c) リンカ廃棄方式 | Smart Configurator 出力を一切触らない | `__VECTOR_TABLE` 弱シンボル等 FSP が他から `g_vector_table` を参照している箇所と整合させる必要．`/DISCARD/` 後に間接参照のリンクエラーが出やすい |

EK-RA6M5 では (a) で十分動作している．Smart Configurator を頻繁に再生成
する開発フェーズで (a) のコピー作業が頻発する場合は (b) への移行を検討．

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
  target 層の `Makefile.target` で `KERNEL_COBJS` に追加し，リンカ
  スクリプト (`r7fa6m5bh.ld`) の `.option_setting_*` セクションへ
  配置する設計 (EK-RA6M5 では実装済)．他 RA で OFS の再配置が必要なら
  同様に対応する．
- **FSP `SystemInit()` は `hardware_init_hook` (BSS 前) から呼べない**．
  内部で `bsp_init_uninitialized_vars()` 等が BSS 領域の変数を触るため．
  EK-RA6M5 の target 層では `target_hardware_initialize()` (BSS 後，
  StartOS 経由) で `SystemInit()` を呼び，その後 `prc_initialize()` で
  VTOR を ATK2 ベクタテーブルへ書換える順序を厳守している．
- **TrustZone (Cortex-M33 + ARMv8-M Security Extension) のうち本層が
  サポートするのは TZEN=0 の Full Secure 動作のみ**．RA + FSP "Flat
  (Non-TrustZone) Project" がこのモードで，OFS1.TZEN=0 だがデバイス
  実装上は Secure 単一．本層が想定する `EXC_RETURN` も Secure 値
  (`0xFFFFFFFD`)．対応するには target 層 `Makefile.target` で
  `-DTOPPERS_TZ_S` を **必ず** 指定する (定義漏れは `arm_m.h` で
  `#error`)．**TZEN=1 (Secure / Non-Secure 分割)** は未対応．
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
  ベースのオンデマンド生成方式に切替．FSP 6.4.0 (sc_v2025-12) を採用．
  当初は MCU_GROUP/CORE_CPU 変数化で RA ファミリ汎用を謳っていた．
- 2026-04 (Phase 4 完了): EK-RA6M5 + ATfE clang 21.1.1 で **実機動作確認**．
  起動時 HardFault 5 件 (Thumb-bit 二重加算 / MSPLIM > MSP / FSP BSS 再消去 /
  SCI7&GPT MSTP / IELSR.IR クリア) を解消．`vector_data.c` の取扱は (a)
  抽出方式に確定 (§6.3 参照)．`EXC_RETURN = 0xFFFFFFFD` (Full Secure: ES=1,
  S=1) を `TOPPERS_TZ_S` で選択する設計を確立．
- 2026-04 (Phase 5 完了): cfg_py 回帰テスト
  ([`cfg/cfg_py/tests/test_integration_ek_ra6m5.py`](../../../cfg/cfg_py/tests/test_integration_ek_ra6m5.py))
  整備．
- 2026-04 (Phase 6): 本層のスコープを **「Cortex-M33 + 96-slot ICU」明示**
  に降格 (TMAX_INTNO/TNUM_INT が 96 スロット前提でハードコード．RA8 は
  対象外)．関連: チップ依存定義 (`TMIN_INTNO` / `TMAX_INTNO` / `TNUM_INT` /
  `TBITW_IPRI` および `INTNO_VALID` / `INTNO_CONTROLLABLE` / `TNUM_INTPRI`)
  を PRC 層 (`arch/arm_m_gcc/common/`) からチップ層 (`chip_config.h` および
  `chip.tf`) へ移動．
