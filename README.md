# TOPPERS/ATK2 NUCLEO-H563ZI 移植版

TOPPERS/ATK2 (AUTOSAR Kernel Version 2, SC1) を STMicroelectronics
**NUCLEO-H563ZI** ボード (ARM Cortex-M33) 上で動作させる実装一式．

オリジナル ATK2 SC1 (Nios2 用) に対し，ARM Cortex-M / STM32H5xx 用の
プロセッサ・チップ・ターゲット依存部 (`arm_m_gcc/common`,
`arm_m_gcc/stm32h5xx_stm32cube`, `target/nucleo_h563zi_gcc`) を新規追加
している．移植にあたっては TOPPERS/ASP3 の同ボード対応版を参考にした．

## ディレクトリ構成

```
atk2-sc1_nios2/
├── arch/
│   ├── arm_m_gcc/
│   │   ├── common/                 ARM Cortex-M 共通プロセッサ依存部 (新規)
│   │   └── stm32h5xx_stm32cube/    STM32H5xx チップ依存部 (新規, HAL 同梱)
│   ├── nios2_gcc/                  Nios2 プロセッサ依存部 (オリジナル)
│   ├── gcc/                        GCC 共通
│   └── logtrace/                   トレースログ
├── target/
│   ├── nucleo_h563zi_gcc/          NUCLEO-H563ZI ターゲット依存部 (新規)
│   └── nios2_dev_gcc/              Nios2 ボード依存部 (オリジナル)
├── kernel/                         OS カーネル (オリジナル)
├── sample/                         サンプル (一部修正)
├── sysmod/                         システムモジュール (オリジナル)
├── library/                        ライブラリ (オリジナル)
├── include/                        ATK2 公開ヘッダ (オリジナル)
├── obj/
│   ├── obj_nios2/                  Nios2 用 obj (オリジナル)
│   └── obj_nucleo_h563zi/          NUCLEO-H563ZI 用 obj (新規)
├── cfg/
│   ├── cfg/cfg.exe                 ATK2 cfg ツール (オリジナル C++ 版)
│   └── cfg_py/                     ATK2 cfg ツール Python 移植版 (新規, デフォルト)
├── utils/abrex/                    YAML↔ARXML 変換ツール (Python 化)
└── doc/                            オリジナルドキュメント
```

各層の詳細は以下の README を参照:

- [`arch/arm_m_gcc/common/README.md`](arch/arm_m_gcc/common/README.md) — ARM-M 共通依存部
- [`arch/arm_m_gcc/stm32h5xx_stm32cube/README.md`](arch/arm_m_gcc/stm32h5xx_stm32cube/README.md) — STM32H5xx チップ依存部
- [`target/nucleo_h563zi_gcc/README.md`](target/nucleo_h563zi_gcc/README.md) — NUCLEO-H563ZI ボード依存部 (ビルド方法)

## オリジナル ATK2 (Nios2 版) からの変更点

このパッケージは新規ターゲット追加にあたり、共通部にも以下の変更を加えて
いる。これらの変更は Nios2 ターゲットを破壊しないことを目標としているが、
ターゲットを切り替えてビルドする際は内容を確認すること。

### 共通部の変更

| 対象 | 内容 |
|---|---|
| `sample/Makefile` (configure 雛形) | gcc の `-MD -MP` で依存ファイル `.d` を自動生成する方式に変更．`make depend` および `Perl/utils/makedep` ベースの依存生成を廃止．中間生成物 (`.o`/`.d`) を `objs/` 配下に集約．`touch -r` を廃止し，スタンプファイルは `: > $@` で更新．並列 make (`-j`) 対応の order-only 依存を整備． |
| `sample/sample1.c` | MainTask に `case '6'` を追加 (HW カウンタ動作確認用に 5 秒×4 回ログを出すコマンド)． |
| `utils/abrex/abrex.rb` | Python 版 `abrex.py` に置換．動作要件は Python 3 + PyYAML． |
| `utils/abrex/MANIFEST` / `readme.txt` | Python 版に合わせて記述更新． |
| `target/nios2_dev_gcc/com_port.rb` | Python 版 `com_port.py` に置換．動作要件は Python 3 + pyserial． |
| `target/nios2_dev_gcc/Makefile.target` | `urun` / `ucppt` ターゲットの呼出しを `ruby ... .rb` から `python ... .py` に変更． |
| `target/nios2_dev_gcc/MANIFEST` | `com_port.rb` → `com_port.py`． |

### 新規追加

| 対象 | 内容 |
|---|---|
| `arch/arm_m_gcc/common/` | ARM Cortex-M 共通プロセッサ依存部一式 (start.S, prc_support.S, prc_config.c/h, arm_m.h, Makefile.prc, FPU 制御等)． |
| `arch/arm_m_gcc/stm32h5xx_stm32cube/` | STM32H5xx チップ依存部 (HAL Driver 同梱, Makefile.chip)． |
| `target/nucleo_h563zi_gcc/` | NUCLEO-H563ZI ボード依存部 (リンカスクリプト, ターゲット設定, シリアル/HW カウンタドライバ, STM32CubeIDE プロジェクト)． |
| `obj/obj_nucleo_h563zi/` | NUCLEO-H563ZI 用ビルドディレクトリ． |
| `cfg/cfg_py/` | ATK2 cfg ツールの Python 完全移植版 (pass1/2/3 + .tf テンプレートエンジン + ARXML 木 + macro_processor binding)．`USE_PY_CFG=1` (デフォルト) で本実装が選択される． |

## ビルド・実行

### Make (msys2 + arm-none-eabi-gcc)

```sh
cd atk2-sc1_nios2/obj/obj_nucleo_h563zi
make -j4
```

`atk2-sc1` (ELF) / `atk2-sc1.srec` / `atk2-sc1.dump` が生成される．

### cfg ツールの選択 (`USE_PY_CFG`)

ATK2 のコンフィギュレータ (cfg) は **C++ 版バイナリ** と **Python 移植版**
の 2 種類を同梱している．Makefile 変数 `USE_PY_CFG` で切替える．

| 設定 | cfg の実体 | 備考 |
|---|---|---|
| `USE_PY_CFG=1` (デフォルト) | `$(SRCDIR)/cfg/cfg_py/cfg.py` | Python 3 を使用．依存は標準ライブラリのみ |
| `USE_PY_CFG=0` | `$(SRCDIR)/cfg/cfg/cfg.exe` | 同梱の C++ ビルド済バイナリ |

```sh
# デフォルト (Python 版を使う場合)
make -j4

# C++ 版バイナリを明示的に使う場合
make USE_PY_CFG=0 -j4
```

Python 実行可能ファイル名は `PYTHON` 変数で上書き可能 (例: `make PYTHON=python3`)．

#### Python 版の動作確認状況

- pass1 / pass2 / pass3 すべて C++ 版と同等の出力 (`cfg1_out.c`, `Os_Lcfg.c/h`,
  `Os_Cfg.h`, `offset.h`, `cfg2_out.tf`) を生成．
- 最終リンク後の `atk2-sc1.exe` の `objdump -d` 結果は C++ 版と完全一致．
- 単体テストは `cfg/cfg_py/tests/` 配下に整備済 (`pytest` で実行可能)．

#### C++ 版バイナリへフォールバックすべきケース

- `cfg.py` が動作する Python 環境が用意できないとき (Python 3.7+ を想定)．
- 出力差分の切り分けが必要なとき (`USE_PY_CFG=0` で取った参照と比較する)．

### STM32CubeIDE

[`target/nucleo_h563zi_gcc/README.md`](target/nucleo_h563zi_gcc/README.md)
を参照．動作確認済みバージョンは **STM32CubeIDE 2.1.1**．

### 開発環境動作確認

| ツール | バージョン |
|---|---|
| arm-none-eabi-gcc | 13.3.1 / 14.3.1 |
| arm-none-eabi-binutils | 2.42.0 / 14.3.1 |
| GNU Make | 4.4.1 |
| ATK2 cfg (C++ 版) | 同梱 `cfg/cfg/cfg.exe` (バージョン 1.9.4 ベース) |
| ATK2 cfg (Python 版) | 同梱 `cfg/cfg_py/cfg.py` (Python 3.7 以降) |
| STM32CubeIDE | 2.1.1 |

## ライセンス

各ソースファイル先頭の TOPPERS ライセンスに従う．本リポジトリの追加分も
同ライセンスを継承する．

AUTOSAR (AUTomotive Open System ARchitecture) 仕様に基づくため，AUTOSAR
の知的財産権許諾は別途 AUTOSAR パートナーシップが必要となる場合がある．

## 参考資料

- TOPPERS/ATK2 公式: <https://www.toppers.jp/atk2.html>
- TOPPERS/ASP3 (移植参考): <https://www.toppers.jp/asp3-kernel.html>
- NUCLEO-H563ZI: <https://www.st.com/ja/evaluation-tools/nucleo-h563zi.html>
- STM32H5xx HAL ドライバ (移植元): STMicroelectronics STM32CubeH5
