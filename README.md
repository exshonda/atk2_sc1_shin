# TOPPERS/ATK2 NUCLEO-H563ZI 移植版

TOPPERS/ATK2 (AUTOSAR Kernel Version 2, SC1) を STMicroelectronics
**NUCLEO-H563ZI** ボード (ARM Cortex-M33) 上で動作させる実装一式．

オリジナル ATK2 SC1 (Nios2 用) に対し，ARM Cortex-M / STM32H5xx 用の
プロセッサ・チップ・ターゲット依存部 (`arch/arm_m_gcc/common`,
`arch/arm_m_gcc/stm32h5xx_stm32cube`, `target/nucleo_h563zi_gcc`) を
新規追加している．移植にあたっては TOPPERS/ASP3 の同ボード対応版を
参考にした．

## ディレクトリ構成

```
atk2_sc1_shin/
├── arch/
│   ├── arm_m_gcc/
│   │   ├── common/                 ARM Cortex-M 共通プロセッサ依存部
│   │   └── stm32h5xx_stm32cube/    STM32H5xx チップ依存部 (HAL 同梱)
│   ├── gcc/                        GCC 共通
│   └── logtrace/                   トレースログ
├── target/
│   └── nucleo_h563zi_gcc/          NUCLEO-H563ZI ターゲット依存部
├── kernel/                         OS カーネル (オリジナル)
├── sample/                         サンプル
├── sysmod/                         システムモジュール
├── library/                        ライブラリ
├── include/                        ATK2 公開ヘッダ
├── obj/
│   └── obj_nucleo_h563zi/          NUCLEO-H563ZI 用ビルドディレクトリ
├── cfg/
│   └── cfg_py/                     ATK2 cfg ツール Python 移植版 (デフォルト)
├── utils/                          ユーティリティスクリプト (Python)
│   └── abrex/                      YAML↔ARXML 変換ツール
├── doc/                            オリジナルドキュメント
├── configure.py                    構成スクリプト (Python 版)
└── README.md                       このファイル
```

各層の詳細は以下の README を参照:

- [`arch/arm_m_gcc/common/README.md`](arch/arm_m_gcc/common/README.md) — ARM-M 共通依存部
- [`arch/arm_m_gcc/stm32h5xx_stm32cube/README.md`](arch/arm_m_gcc/stm32h5xx_stm32cube/README.md) — STM32H5xx チップ依存部
- [`target/nucleo_h563zi_gcc/README.md`](target/nucleo_h563zi_gcc/README.md) — NUCLEO-H563ZI ボード依存部 (ビルド方法)

> **注**: 本リポジトリには **Nios2 ターゲット (`arch/nios2_gcc`,
> `target/nios2_dev_gcc`, `obj/obj_nios2`) は含まれていない**．Nios2 用
> の構成が必要な場合はオリジナル ATK2 SC1 (Nios2) の配布アーカイブを
> 参照のこと．

## セットアップ

### 1. クロスコンパイラ (必須)

Arm Cortex-M 用 GCC ツールチェーン．以下のいずれか:

| 入手元 | 動作確認バージョン |
|---|---|
| Arm GNU Toolchain (公式) | `arm-none-eabi-gcc` 13.3.1, binutils 2.42 |
| STM32CubeIDE 2.1.1 同梱 | `arm-none-eabi-gcc` 14.3.1, binutils 14.3.1 |

`arm-none-eabi-gcc` を `PATH` に通すか，環境変数 `GCC_TARGET_PREFIX` で
場所を指定する．

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

### 4. STM32CubeIDE (任意)

GUI ベースのデバッグ環境を使う場合のみ．動作確認済みバージョンは
**STM32CubeIDE 2.1.1**．インストール手順とプロジェクト取込み方法は
[`target/nucleo_h563zi_gcc/README.md`](target/nucleo_h563zi_gcc/README.md)
を参照．

## ビルド・実行

### Make (msys2 + arm-none-eabi-gcc)

```sh
cd obj/obj_nucleo_h563zi
make -j4
```

`atk2-sc1` (ELF) / `atk2-sc1.srec` / `atk2-sc1.dump` が生成される．

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

### STM32CubeIDE

[`target/nucleo_h563zi_gcc/README.md`](target/nucleo_h563zi_gcc/README.md)
を参照．動作確認済みバージョンは **STM32CubeIDE 2.1.1**．

### 開発環境動作確認

| ツール | バージョン | 入手元 |
|---|---|---|
| arm-none-eabi-gcc | 13.3.1 / 14.3.1 | Arm GNU Toolchain / STM32CubeIDE |
| arm-none-eabi-binutils | 2.42.0 / 14.3.1 | 同上 |
| GNU Make | 4.4.1 | msys2 |
| Python | 3.7 以降 (3.13 で動作確認) | <https://www.python.org/> |
| ATK2 cfg (Python 版) | 同梱 `cfg/cfg_py/cfg.py` | 本リポジトリ |
| ATK2 cfg (C++ 版, 任意) | cfg-mingw-static 1.9.6 | <https://www.toppers.jp/download.cgi/cfg-mingw-static-1_9_6.zip> |
| STM32CubeIDE | 2.1.1 | <https://www.st.com/en/development-tools/stm32cubeide.html> |
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
| `arch/arm_m_gcc/common/` | ARM Cortex-M 共通プロセッサ依存部一式 (start.S, prc_support.S, prc_config.c/h, arm_m.h, Makefile.prc, FPU 制御等)． |
| `arch/arm_m_gcc/stm32h5xx_stm32cube/` | STM32H5xx チップ依存部 (HAL Driver 同梱, Makefile.chip)． |
| `target/nucleo_h563zi_gcc/` | NUCLEO-H563ZI ボード依存部 (リンカスクリプト, ターゲット設定, シリアル/HW カウンタドライバ, STM32CubeIDE プロジェクト)． |
| `obj/obj_nucleo_h563zi/` | NUCLEO-H563ZI 用ビルドディレクトリ． |
| `cfg/cfg_py/` | ATK2 cfg ツールの Python 完全移植版 (pass1/2/3 + .tf テンプレートエンジン + ARXML 木 + macro_processor binding)．`USE_PY_CFG=1` (デフォルト) で本実装が選択される． |

## ライセンス

各ソースファイル先頭の TOPPERS ライセンスに従う．本リポジトリの追加分も
同ライセンスを継承する．

AUTOSAR (AUTomotive Open System ARchitecture) 仕様に基づくため，AUTOSAR
の知的財産権許諾は別途 AUTOSAR パートナーシップが必要となる場合がある．

## 参考資料

- TOPPERS/ATK2 公式: <https://www.toppers.jp/atk2.html>
- TOPPERS/ASP3 (移植参考): <https://www.toppers.jp/asp3-kernel.html>
- TOPPERS cfg ツール ダウンロード: <https://www.toppers.jp/cfg.html>
- NUCLEO-H563ZI: <https://www.st.com/ja/evaluation-tools/nucleo-h563zi.html>
- STM32H5xx HAL ドライバ (移植元): STMicroelectronics STM32CubeH5
