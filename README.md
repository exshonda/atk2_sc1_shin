# TOPPERS/ATK2 ARM Cortex-M33 移植版 (NUCLEO-H563ZI / EK-RA6M5)

TOPPERS/ATK2 (AUTOSAR Kernel Version 2, SC1) を **ARM Cortex-M33** 系
評価ボード上で動作させる実装一式．現在 2 つのボードに対応:

| 略称 | ボード | MCU | ツールチェイン | チップ依存部 / ターゲット |
|---|---|---|---|---|
| `nucleo_h563zi_gcc` | STMicroelectronics NUCLEO-H563ZI | STM32H563ZI (Cortex-M33 + FPU) | arm-none-eabi-gcc 13/14 | `arch/arm_m_gcc/stm32h5xx_stm32cube/` (STM32Cube HAL 同梱) / `target/nucleo_h563zi_gcc/` |
| `ek_ra6m5_llvm` | Renesas EK-RA6M5 | R7FA6M5BH (Cortex-M33 + FPU) | ATfE clang 21.1.1 | `arch/arm_m_llvm/ra_fsp/` (Renesas FSP 6.4.0 ベース; **FSP 非同梱**) / `target/ek_ra6m5_llvm/` |

オリジナル ATK2 SC1 (Nios2 用) に対し，ARM Cortex-M 共通プロセッサ依存部
(`arch/arm_m_gcc/common`) と上記の各チップ・ターゲット依存部を新規追加
している．移植にあたっては TOPPERS/ASP3 の Cortex-M ポートを参考にした．

## ディレクトリ構成

```
atk2_sc1_shin/
├── arch/
│   ├── arm_m_gcc/
│   │   ├── common/                 ARM Cortex-M 共通プロセッサ依存部 (両ターゲット共有)
│   │   └── stm32h5xx_stm32cube/    STM32H5xx チップ依存部 (HAL 同梱)
│   ├── arm_m_llvm/
│   │   ├── common/                 ARM LLVM (ATfE) 用 Makefile.prc のみ
│   │   └── ra_fsp/                 Renesas RA + FSP チップ依存部 (FSP 非同梱)
│   ├── gcc/ / llvm/                AUTOSAR Compiler 抽象 (clang は gcc を再利用)
│   └── logtrace/                   トレースログ
├── target/
│   ├── nucleo_h563zi_gcc/          NUCLEO-H563ZI ターゲット依存部 + STM32CubeIDE プロジェクト
│   └── ek_ra6m5_llvm/              EK-RA6M5 ターゲット依存部 + e² studio デバッグ専用プロジェクト
├── kernel/                         OS カーネル (オリジナル)
├── sample/                         サンプル
├── sysmod/                         システムモジュール
├── library/                        ライブラリ
├── include/                        ATK2 公開ヘッダ
├── obj/
│   ├── obj_nucleo_h563zi/          NUCLEO-H563ZI 用ビルドディレクトリ
│   └── obj_ek_ra6m5/               EK-RA6M5 用ビルドディレクトリ
├── cfg/
│   └── cfg_py/                     ATK2 cfg ツール Python 移植版 (デフォルト)
├── utils/                          ユーティリティスクリプト (Python)
│   └── abrex/                      YAML↔ARXML 変換ツール
├── doc/                            オリジナルドキュメント
├── configure.py                    構成スクリプト (Python 版)
└── README.md                       このファイル
```

各層の詳細は以下の README を参照:

| 層 | NUCLEO-H563ZI | EK-RA6M5 |
|---|---|---|
| プロセッサ (CPU 共通) | [`arch/arm_m_gcc/common/README.md`](arch/arm_m_gcc/common/README.md) | (同左; ソースを vpath で再利用) |
| チップ | [`arch/arm_m_gcc/stm32h5xx_stm32cube/README.md`](arch/arm_m_gcc/stm32h5xx_stm32cube/README.md) | [`arch/arm_m_llvm/ra_fsp/README.md`](arch/arm_m_llvm/ra_fsp/README.md) |
| ターゲット (ボード) | [`target/nucleo_h563zi_gcc/README.md`](target/nucleo_h563zi_gcc/README.md) | [`target/ek_ra6m5_llvm/README.md`](target/ek_ra6m5_llvm/README.md) |

> **注**: 本リポジトリには **Nios2 ターゲット (`arch/nios2_gcc`,
> `target/nios2_dev_gcc`, `obj/obj_nios2`) は含まれていない**．Nios2 用
> の構成が必要な場合はオリジナル ATK2 SC1 (Nios2) の配布アーカイブを
> 参照のこと．

## セットアップ

### 1. クロスコンパイラ (必須; ターゲットごとに別)

ターゲットごとに別のツールチェインを使う:

#### NUCLEO-H563ZI 用: arm-none-eabi-gcc

| 入手元 | 動作確認バージョン |
|---|---|
| Arm GNU Toolchain (公式) | `arm-none-eabi-gcc` 13.3.1, binutils 2.42 |
| STM32CubeIDE / STM32CubeCLT 同梱 | `arm-none-eabi-gcc` 14.3.1, binutils 14.3.1 |

`arm-none-eabi-gcc` を `PATH` に通すか，環境変数 `GCC_TARGET_PREFIX` で
場所を指定する．

#### EK-RA6M5 用: ARM LLVM (ATfE) 21.1.1

Renesas e² studio v2025-12 同梱の **Arm Toolchain for Embedded (ATfE)
21.1.1** を使用．`clang --target=arm-none-eabi` で ARM ELF を生成．
標準パス:

```
C:/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin/
```

このディレクトリを `PATH` に通せば `clang`, `llvm-ar`, `llvm-nm`,
`llvm-objcopy`, `llvm-objdump` がそのまま見える．

### 2. Python ランタイム (必須)

ATK2 のコンフィギュレータ (cfg) は本リポジトリでは **Python 3 移植版を
デフォルト** で使用する．Python 3.7 以降が必要．

#### 必須パッケージ

| パッケージ | 用途 | インストール |
|---|---|---|
| (なし) | `cfg_py/cfg.py` 本体 | 標準ライブラリのみで動作 |

#### オプションパッケージ

| パッケージ | 用途 | インストール |
|---|---|---|
| `pyyaml` | `utils/abrex/abrex.py` (YAML ↔ ARXML 変換) | `pip install pyyaml` |
| `pytest` | `cfg/cfg_py/tests/` の単体テスト実行 | `pip install pytest` |

#### まとめてインストール

```sh
pip install pyyaml pytest
# あるいは仮想環境を切る場合
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows (PowerShell)
pip install pyyaml pytest
```

### 3. cfg バイナリ版 (任意 — フォールバック用)

**本リポジトリには ATK2 cfg ツールの C++ ビルド済バイナリ
(`cfg/cfg/cfg.exe` 等) は同梱していない**．通常はデフォルトの Python 版
(`cfg/cfg_py/cfg.py`) で動作するため不要．

ビルド出力差分の切り分け等で C++ 版バイナリが必要になった場合は，
TOPPERS プロジェクトの公式ページから取得する:

- mingw 静的ビルド版 (Windows 向け):
  <https://www.toppers.jp/download.cgi/cfg-mingw-static-1_9_6.zip>

ダウンロードした zip を展開し，`cfg.exe` を本リポジトリの
`cfg/cfg/cfg.exe` に配置する:

```
atk2_sc1_shin/
└── cfg/
    └── cfg/
        ├── cfg.exe                            ← ここに置く
        ├── AUTOSAR_4-0-3_STRICT.xsd           ← 同 zip 内に同梱されている
        └── xml.xsd
```

その後 `make USE_PY_CFG=0` でバイナリ版に切替できる (詳細は次節参照)．

### 4. IDE (任意; ターゲットごと)

#### NUCLEO-H563ZI: STM32CubeIDE 2.1.1

GUI ベースのビルド・デバッグ環境．インストール手順とプロジェクト取込み
方法は [`target/nucleo_h563zi_gcc/README.md`](target/nucleo_h563zi_gcc/README.md)
を参照．

#### EK-RA6M5: e² studio v2025-12 (デバッグ専用)

本ターゲットでは **e² studio はデバッグのみに使用**．ビルドはコマンド
ラインの make で行い，e² studio は ELF をロードして J-Link 経由で実機
デバッグするだけ．取込み手順は
[`target/ek_ra6m5_llvm/README.md`](target/ek_ra6m5_llvm/README.md) §9
参照．

### 5. Renesas Smart Configurator + FSP (EK-RA6M5 のみ)

EK-RA6M5 ターゲットは Renesas FSP 6.4.0 を使うが，**FSP ソースは本
リポジトリに同梱しない**．clone 後に 1 回だけ `rascc.exe --generate` で
`target/ek_ra6m5_llvm/fsp/{ra,ra_cfg,ra_gen}/` を生成する必要がある．

| ツール | 動作確認バージョン | 備考 |
|---|---|---|
| Smart Configurator (standalone) | `sc_v2025-12_fsp_v6.4.0` | `C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rascc.exe` |
| e² studio 同梱 Smart Configurator | v2025-12 (FSP 6.4.0) | rasc.exe / rascc.exe いずれも可 |

セットアップ手順の詳細:
[`arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md`](arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md)．

## ビルド・実行

### NUCLEO-H563ZI (Make + arm-none-eabi-gcc)

```sh
cd obj/obj_nucleo_h563zi
make -j4
```

### EK-RA6M5 (Make + ATfE clang)

ATfE bin を `PATH` に通してから:

```sh
export PATH="/c/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin:$PATH"
cd obj/obj_ek_ra6m5
make -j4
```

(初回は事前に `rascc --generate target/ek_ra6m5_llvm/fsp/configuration.xml`
を 1 回実行する必要がある．§5 参照．)

いずれのターゲットでも `atk2-sc1` (ELF) / `atk2-sc1.srec` /
`atk2-sc1.dump` がビルドディレクトリに生成される．

### cfg ツールの選択 (`USE_PY_CFG`)

ATK2 のコンフィギュレータ (cfg) は **Python 移植版 (同梱)** と
**C++ ビルド済バイナリ (要ダウンロード)** の 2 種類を切替可能．Makefile
変数 `USE_PY_CFG` で選択する．

| 設定 | cfg の実体 | 同梱 | 備考 |
|---|---|---|---|
| `USE_PY_CFG=1` (デフォルト) | `$(SRCDIR)/cfg/cfg_py/cfg.py` | ✓ | Python 3.7+ ．依存は標準ライブラリのみ |
| `USE_PY_CFG=0` | `$(SRCDIR)/cfg/cfg/cfg.exe` | ✗ | 公式から別途ダウンロードして配置する (本書「セットアップ」の 3. 参照) |

```sh
# デフォルト (Python 版を使う)
make -j4

# C++ 版バイナリを明示的に使う (cfg.exe を配置済の場合)
make USE_PY_CFG=0 -j4
```

Python 実行可能ファイル名は `PYTHON` 変数で上書き可能 (例:
`make PYTHON=python3`)．

#### Python 版の動作確認状況

- pass1 / pass2 / pass3 すべて C++ 版と同等の出力 (`cfg1_out.c`,
  `Os_Lcfg.c/h`, `Os_Cfg.h`, `offset.h`, `cfg2_out.tf`) を生成．
- 最終リンク後の `atk2-sc1.exe` の `objdump -d` 結果は C++ 版と完全一致．
- 単体テストは `cfg/cfg_py/tests/` 配下に整備済 (`pytest` で実行可能):

  ```sh
  pip install pytest
  cd cfg/cfg_py
  pytest -v
  ```

### IDE 経由のビルド・デバッグ

詳細はターゲットごとの README:

- [`target/nucleo_h563zi_gcc/README.md`](target/nucleo_h563zi_gcc/README.md) (STM32CubeIDE 2.1.1)
- [`target/ek_ra6m5_llvm/README.md`](target/ek_ra6m5_llvm/README.md) (e² studio v2025-12; デバッグ専用)

### 開発環境動作確認

| ツール | バージョン | 用途 / 入手元 |
|---|---|---|
| arm-none-eabi-gcc | 13.3.1 / 14.3.1 | NUCLEO-H563ZI ビルド (Arm GNU Toolchain / STM32CubeIDE) |
| arm-none-eabi-binutils | 2.42.0 / 14.3.1 | 同上 |
| **ARM LLVM (ATfE)** | **21.1.1** | EK-RA6M5 ビルド (Renesas e² studio v2025-12 同梱) |
| GNU Make | 4.4 (msys2 / e² studio 同梱) | 両ターゲット |
| Python | 3.7 以降 (3.13 / 3.14 で動作確認) | cfg_py 実行用．<https://www.python.org/> |
| ATK2 cfg (Python 版) | 同梱 `cfg/cfg_py/cfg.py` | 本リポジトリ |
| ATK2 cfg (C++ 版, 任意) | cfg-mingw-static 1.9.6 | <https://www.toppers.jp/download.cgi/cfg-mingw-static-1_9_6.zip> |
| **Renesas FSP** | **6.4.0** (sc_v2025-12) | EK-RA6M5 のみ．`rascc.exe --generate` 用 |
| STM32CubeIDE | 2.1.1 | NUCLEO-H563ZI 用 IDE．<https://www.st.com/en/development-tools/stm32cubeide.html> |
| e² studio | v2025-12 (FSP 6.4.0) | EK-RA6M5 デバッグ用．Renesas 公式 |
| **SEGGER J-Link** | V9.20 以降 | EK-RA6M5 フラッシュ書込み |
| PyYAML (任意) | 6.x 系 | `pip install pyyaml` |
| pytest (任意) | 9.x 系 | `pip install pytest` |

## オリジナル ATK2 (Nios2 版) からの変更点

このパッケージは新規ターゲット追加にあたり，共通部にも以下の変更を加えて
いる．本リポジトリには Nios2 関連ファイルは含めていないが，これらの変更は
オリジナル ATK2/SC1 (Nios2) との差分として記録する．

### 共通部の変更

| 対象 | 内容 |
|---|---|
| `sample/Makefile` (configure 雛形) | gcc の `-MD -MP` で依存ファイル `.d` を自動生成する方式に変更．`make depend` および `Perl/utils/makedep` ベースの依存生成を廃止．中間生成物 (`.o`/`.d`) を `objs/` 配下に集約．`touch -r` を廃止し，スタンプファイルは `: > $@` で更新．並列 make (`-j`) 対応の order-only 依存を整備． |
| `sample/sample1.c` | MainTask に `case '6'` を追加 (HW カウンタ動作確認用に 5 秒×4 回ログを出すコマンド)． |
| `utils/applyrename`, `genrename`, `gentest`, `makerelease` | Perl から Python 3 に書換え．拡張子は `.py`． |
| `utils/abrex/abrex.rb` | Python 版 `abrex.py` に置換．動作要件は Python 3 + PyYAML． |
| `utils/abrex/MANIFEST` / `readme.txt` | Python 版に合わせて記述更新． |
| `configure` (Perl) | Python 版 `configure.py` に置換． |

### 新規追加

| 対象 | 内容 |
|---|---|
| `arch/arm_m_gcc/common/` | ARM Cortex-M 共通プロセッサ依存部一式 (start.S, prc_support.S, prc_config.c/h, arm_m.h, Makefile.prc, FPU 制御等)．両ターゲット共有． |
| `arch/arm_m_gcc/stm32h5xx_stm32cube/` | STM32H5xx チップ依存部 (HAL Driver 同梱, Makefile.chip)． |
| `arch/arm_m_llvm/common/` | ARM LLVM (ATfE) 用 Makefile.prc．ソース本体は `arch/arm_m_gcc/common/` を vpath で参照． |
| `arch/arm_m_llvm/ra_fsp/` | Renesas RA + FSP 6.4.0 用チップ依存部 (Cortex-M33 + 96-slot ICU)．**FSP は同梱せず**，clone 後 `rascc --generate` で生成． |
| `arch/llvm/` | AUTOSAR Compiler 抽象 (clang 用ブリッジ)．`arch/gcc/` を再利用． |
| `target/nucleo_h563zi_gcc/` | NUCLEO-H563ZI ボード依存部 (リンカスクリプト, USART3, TIM2/TIM5 HW カウンタ, STM32CubeIDE プロジェクト)． |
| `target/ek_ra6m5_llvm/` | EK-RA6M5 ボード依存部 (リンカスクリプト, SCI7, GPT320/GPT321 HW カウンタ, e² studio デバッグ専用プロジェクト, FSP `configuration.xml`)． |
| `obj/obj_nucleo_h563zi/`, `obj/obj_ek_ra6m5/` | 各ターゲットのビルドディレクトリ． |
| `cfg/cfg_py/` | ATK2 cfg ツールの Python 完全移植版 (pass1/2/3 + .tf テンプレートエンジン + ARXML 木 + macro_processor binding)．`USE_PY_CFG=1` (デフォルト) で本実装が選択される．EK-RA6M5 用回帰テスト (`tests/test_integration_ek_ra6m5.py`) も整備． |

## ライセンス

各ソースファイル先頭の TOPPERS ライセンスに従う．本リポジトリの追加分も
同ライセンスを継承する．

EK-RA6M5 ターゲットでは `rascc --generate` で生成される **Renesas FSP**
ソース (`target/ek_ra6m5_llvm/fsp/ra/fsp/`) は **BSD 3-Clause License**
(`SPDX-License-Identifier: BSD-3-Clause`)．Renesas Electronics
Corporation 著作権表示を保つこと．ただし FSP ソースは本リポジトリに
**同梱せず**，clone 後にユーザがローカル生成する設計．

AUTOSAR (AUTomotive Open System ARchitecture) 仕様に基づくため，AUTOSAR
の知的財産権許諾は別途 AUTOSAR パートナーシップが必要となる場合がある．

## 参考資料

- TOPPERS/ATK2 公式: <https://www.toppers.jp/atk2.html>
- TOPPERS/ASP3 (移植参考): <https://www.toppers.jp/asp3-kernel.html>
- TOPPERS cfg ツール ダウンロード: <https://www.toppers.jp/cfg.html>
- NUCLEO-H563ZI: <https://www.st.com/ja/evaluation-tools/nucleo-h563zi.html>
- EK-RA6M5: <https://www.renesas.com/ja/products/microcontrollers-microprocessors/ra-cortex-m-mcus/ek-ra6m5-evaluation-kit-ra6m5-mcu-group>
- STM32H5xx HAL ドライバ (移植元): STMicroelectronics STM32CubeH5
- Renesas FSP: <https://github.com/renesas/fsp>
