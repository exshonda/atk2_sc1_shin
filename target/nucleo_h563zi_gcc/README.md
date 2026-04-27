# NUCLEO-H563ZI ターゲット依存部 (`target/nucleo_h563zi_gcc`)

TOPPERS/ATK2 (SC1) の **STMicroelectronics NUCLEO-H563ZI** ボード向け
ターゲット依存部．

ターゲット略称: `nucleo_h563zi_gcc`  
ボード製品ページ: <https://www.st.com/ja/evaluation-tools/nucleo-h563zi.html>

## 1. 構成

このターゲット依存部は以下の階層上に成立する:

| 層 | パス | 役割 |
|---|---|---|
| **ターゲット (本層)** | `target/nucleo_h563zi_gcc/` | NUCLEO-H563ZI ボード固有の設定 |
| チップ依存部 | `arch/arm_m_gcc/stm32h5xx_stm32cube/` | STM32H5xx ファミリ + STM32Cube HAL |
| プロセッサ依存部 | `arch/arm_m_gcc/common/` | ARM Cortex-M (ARMv8-M) 共通 |

## 2. 開発環境と動作確認バージョン

| ツール | 動作確認バージョン |
|---|---|
| arm-none-eabi-gcc | 13.3.1 (msys2) / 14.3.1 (STM32CubeIDE 2.1.1 同梱) |
| arm-none-eabi-binutils | 2.42 系 / 14.3.1 系 |
| GNU Make | 4.4.1 |
| **STM32CubeIDE** | **2.1.1** |
| ATK2 cfg (C++ 版) | 同梱 `cfg/cfg/cfg.exe` |
| ATK2 cfg (Python 版) | 同梱 `cfg/cfg_py/cfg.py` (デフォルト，Python 3.7+) |
| ホスト OS | Windows 11 (msys2 もしくは STM32CubeIDE 2.1.1) |

## 3. メモリマップ

STM32H563ZI のメモリマップに従う:

| 領域 | アドレス | サイズ | 用途 |
|---|---|---|---|
| 内蔵 Flash | `0x08000000` 〜 `0x081FFFFF` | 2 MB | `.isr_vector` / `.text` / `.rodata` / `.data` (LMA) |
| 内蔵 SRAM | `0x20000000` 〜 `0x2009FFFF` | 655 KB | `.data` (VMA) / `.bss` / スタック |
| I/O 領域 | `0x40000000` 〜 `0x4FFFFFFF` | 256 MB | ペリフェラル |

リンカスクリプト: [`stm32h563zi.ld`](stm32h563zi.ld)．  
SRAM 末尾 (`_estack`) を初期 MSP として使用．

## 4. システムクロック

`stm32fcube/systemclock_config.c` で以下のクロックを構成:

| 項目 | 値 |
|---|---|
| クロックソース | HSE (8 MHz, NUCLEO の MCO 入力) |
| PLL1 | M=4, N=250, P=2 |
| SYSCLK | 250 MHz |
| AHB (HCLK) | 250 MHz |
| APB1/APB2 (PCLK) | 250 MHz (タイマ用に同一) |
| 電源モード | VOS0 (高性能), SMPS |

`nucleo_h563zi.h` の `CPU_CLOCK_HZ` で 250 MHz を定数化．

## 5. 使用するシステムリソース

### GPIO

| 信号 | ピン | 役割 | 代替機能 |
|---|---|---|---|
| USART3_TX | PD8 | シリアル送信 | AF7 |
| USART3_RX | PD9 | シリアル受信 | AF7 |
| LED1 (Green) | PB0 | (アプリ用予約) | GPIO Out |
| LED2 (Yellow) | PF4 | (アプリ用予約) | GPIO Out |
| LED3 (Red) | PG4 | (アプリ用予約) | GPIO Out |
| User Button | PC13 | (未使用) | GPIO In |

### ペリフェラル

| 用途 | ペリフェラル | 詳細 |
|---|---|---|
| シリアル (SIO) | **USART3** | 115200bps, 8N1, 割込み駆動 RX (`INTNO_SIO=76`, INTPRI=2) |
| ハードウェアカウンタ (フリーランニング) | **TIM2** | 32-bit, 1 MHz (= SYSCLK/250), 割込み未使用 |
| ハードウェアカウンタ (アラーム) | **TIM5** | 32-bit, 1 MHz, OPM=1, 割込み有効 (`TIM5_INTNO=64`, INTPRI=1) |

ATK2 の `MAIN_HW_COUNTER` (1us/tick) は TIM2 (現在値読出) と TIM5
(ワンショットアラーム) の組合せで実装．サンプルは 10ms 周期でタスクを
起こす `MainCycArm` アラームを `MAIN_HW_COUNTER` 上に構成している．

### 例外ハンドラ優先度

ARM Cortex-M33 の優先度ビット幅は 4bit (0x00 〜 0xF0):

| 用途 | 優先度 (raw) | 備考 |
|---|---|---|
| C2ISR の最高優先度 (`tmin_basepri`) | 0x10 | OS 割込み禁止の閾値 |
| TIM5 (HW カウンタアラーム) | 0x10 | INTPRI=1 |
| USART3 RX | 0x20 | INTPRI=2 |
| SVCall | 0xE0 | OS 割込み禁止より低 |
| PendSV | 0xFF | 最低 (tail-chain で動く) |

## 6. ターゲット定義事項

`target_kernel.h` で以下を定義:

| マクロ | 値 |
|---|---|
| `TARGET_MIN_STKSZ` | 256 (タスク最小スタック) |
| `MINIMUM_OSTKSZ` | 512 (OS スタック最小) |
| `DEFAULT_TASKSTKSZ` | 1024 |
| `DEFAULT_ISRSTKSZ` | 1024 |
| `DEFAULT_HOOKSTKSZ` | 1024 |
| `DEFAULT_OSSTKSZ` | 8192 |
| `TBITW_IPRI` | 4 (STM32H5xx の優先度ビット幅) |
| `TMIN_INTNO` | 16 (IRQ0 = 例外番号 16) |
| `TMAX_INTNO` | 147 (IRQ131) |

`Makefile.target` で `FPU_USAGE = FPU_LAZYSTACKING` をデフォルトに設定．
変更可能な値は `arch/arm_m_gcc/common/README.md` の「FPU の利用方法」を
参照．

## 7. ファイル構成

```
target/nucleo_h563zi_gcc/
├── README.md                       このファイル
├── Makefile.target                 Makefile のターゲット依存部
├── stm32h563zi.ld                  リンカスクリプト
├── nucleo_h563zi.h                 ボード資源定義 (ピン, クロック, 割込み番号)
├── target_kernel.h                 カーネル設定 (スタックサイズ等)
├── target_config.c / .h            初期化・USART3 ドライバ・LED・ISR テーブル
├── target_serial.h                 sysmod/serial.c 用ヘッダ (INTNO_SIO 等)
├── target_serial.arxml             シリアル ISR の ATK2 cfg 定義
├── target_hw_counter.c / .h        HW カウンタ (TIM2/TIM5) ドライバ
├── target_hw_counter.arxml         HW カウンタの ATK2 cfg 定義
├── target_sysmod.h                 システムモジュール用ヘッダ
├── target_test.h                   テスト用ヘッダ
├── target_cfg1_out.h               cfg1_out.exe リンク用スタブ
├── target_rename.h / target_unrename.h  内部識別名のリネーム
├── target.tf                       pass2 ターゲット依存テンプレート
├── target_check.tf                 pass3 チェック用テンプレート
├── target_offset.tf                offset.h 生成用テンプレート
├── stm32fcube/
│   ├── stm32h5xx_hal_conf.h        HAL モジュール選択
│   ├── system_stm32h5xx.c          CMSIS SystemInit
│   └── systemclock_config.c        PLL 構成 (250MHz)
└── STM32CubeIDE/                   STM32CubeIDE 2.1.1 用プロジェクト
    ├── .project / .cproject
    └── sample/
        ├── Makefile                IDE 内ビルド用 Makefile (configure 不要)
        └── (生成物が出るディレクトリ)
```

## 8. ビルド方法 (1) - Make + msys2

最小工数のコマンドラインビルド．msys2 環境で動作確認済み．

### 必要なもの

- arm-none-eabi-gcc 13.3.1 以降 (PATH に通す)
- GNU Make 4.x
- ATK2 cfg ツール: 以下のいずれか
  - **Python 移植版** (デフォルト): 同梱 `atk2-sc1_nios2/cfg/cfg_py/cfg.py` ＋ Python 3.7 以降
  - C++ 版バイナリ: 同梱 `atk2-sc1_nios2/cfg/cfg/cfg.exe`

### ビルド手順

```sh
cd atk2-sc1_nios2/obj/obj_nucleo_h563zi
make -j4               # デフォルト: Python 版 cfg を使用
# または
make USE_PY_CFG=0 -j4  # C++ 版 cfg.exe を使用
```

生成物:

- `atk2-sc1` (ELF)
- `atk2-sc1.srec` (S-record, 書き込み用)
- `atk2-sc1.dump` (逆アセンブル)
- `atk2-sc1.map` (リンクマップ)

### フラッシュ書き込み (OpenOCD 等)

```sh
make flash    # OpenOCD で書き込み (OpenOCD インストール済み環境)
```

`Makefile` の `flash` ターゲット参照．

## 9. ビルド方法 (2) - STM32CubeIDE 2.1.1

GUI ベースの統合開発環境．動作確認済みバージョンは **STM32CubeIDE 2.1.1**．

### プロジェクトの取込

1. STM32CubeIDE を起動し、ワークスペースを **任意の場所** に設定 (本リポジトリ内である必要は無い)．
2. メニュー: `File → Import → General → Existing Projects into Workspace`
3. `Select root directory:` に
   `atk2-sc1_nios2/target/nucleo_h563zi_gcc/STM32CubeIDE`
   を指定．
4. `sample` プロジェクトにチェックが入っていることを確認し，
   `Finish` をクリック．プロジェクトがワークスペースにインポートされる．

> **注意**: `Copy projects into workspace` には **チェックを入れない**．
> プロジェクトは元の場所から参照する形が想定されている．

### 初回ビルド

1. プロジェクトツリーの `sample` を右クリック → `Build Project`．
2. 内部で以下が実行される:
   - `cfg.exe` による pass1 (cfg1_out.c 生成)
   - `cfg1_out.exe` のリンク
   - `cfg.exe` による pass2 (Os_Lcfg.c/h, Os_Cfg.h 生成)
   - 全 `.c`/`.S` のコンパイル
   - リンクして `atk2-sc1.exe` 生成
   - `cfg.exe` による pass3 (生成物検証)
   - `arm-none-eabi-objdump -d` で `atk2-sc1.dump` 出力

ビルド成功時に `Console` ビューに `Build Finished. 0 errors, ...` が表示される．

### デバッグ・書き込み

ST-Link 経由で NUCLEO-H563ZI を接続:

1. プロジェクトツリーの `sample` を右クリック → `Debug As → STM32 C/C++ Application`．
2. 初回はデバッグ構成画面で `Apply and Debug` を実行．
3. ボードへのプログラム書込み後，自動で `main()` の先頭で停止．
4. `Run`, `Step Over`, ブレークポイント等を IDE 上から操作可能．

シリアル出力 (USART3, 115200bps) を見るには:

- IDE の `Window → Show View → Other → Terminal → Terminal` を開き，
  `Open Terminal` で `Serial Terminal` を選択．
- ポートはホスト PC の OS で `STMicroelectronics STLink Virtual COM Port`
  として認識されるものを指定．設定: `115200, 8, N, 1`，`No Flow Control`．

### Microsoft Store 版 Python が STM32CubeIDE で動作しない件

STM32CubeIDE のビルドでは `make: *** [Makefile:NNN: cfg1_out.c] Error -1`
で停止することがある．これは **Microsoft Store 版 Python の AppX
サンドボックス制約** が原因で，PATH 設定では回避できない．

**現象** (実機で再現):

| python.exe のパス | 種別 | msys2 から | STM32CubeIDE から |
|---|---|---|---|
| `C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\python.exe` | App Execution Alias (0 byte reparse point) | ○ 動作 | × `Error -1` |
| `C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_…\python.exe` | MS Store 実体 (`sys.executable`) | ○ 動作 | × `Error -1` |
| `C:\sw\ST\STEdgeAI\<ver>\Utilities\windows\python.exe` 等 通常の実行ファイル | ○ 動作 | ○ 動作 |

**理由**: Microsoft Store 版 Python は AppX パッケージとしてインストール
され，実体の `python.exe` も AppX activation context が必要なリパース
ポイントになっている．msys2 の bash は AppX 対応のプロセストークンを
継承するため動作するが，STM32CubeIDE 同梱の busybox `sh.exe` /
`make.exe` は AppX 非対応のため `CreateProcess` が `Error -1` で失敗する．
**PATH への追加では解決しない**．

**対処** (いずれか):

1. **python.org からインストーラ版を導入** (推奨．恒久解決)
   - <https://www.python.org/downloads/> からインストール
   - 既定パス: `C:\Users\<user>\AppData\Local\Programs\Python\Python313\python.exe`
   - インストール時 "Add to PATH" にチェックを入れれば PATH 経由でも動く

2. **同梱されている別の Python を使う**
   - STMicroelectronics 製品 (STEdgeAI 等) を入れていれば
     `C:\sw\ST\STEdgeAI\<ver>\Utilities\windows\python.exe` が使える
     (動作確認: Python 3.9.13)
   - インストーラ版でなく zip 展開した portable python でも可

3. **`make USE_PY_CFG=0` で C++ 版 cfg.exe にフォールバック**
   - 別途 [cfg-mingw-static-1_9_6.zip](https://www.toppers.jp/download.cgi/cfg-mingw-static-1_9_6.zip)
     を取得して `cfg/cfg/cfg.exe` に配置 (Project README の
     セットアップ 3. 参照)

**STM32CubeIDE での PYTHON 変数設定**:

`sample` プロジェクトを右クリック → `Properties` → `C/C++ Build` →
`Environment` → `Add...`:

- Name: `PYTHON`
- Value: `C:\Users\<user>\AppData\Local\Programs\Python\Python313\python.exe`
  (上記対処 1 の場合) または `C:\sw\ST\STEdgeAI\<ver>\Utilities\windows\python.exe`
  (対処 2 の場合)

OK → `Project` → `Clean...` → `Build`．

### よくある問題 (その他)

| 症状 | 対処 |
|---|---|
| `cfg.py` 実行時に `python: command not found` (msys make) | `make PYTHON=python3 ...` を指定．もしくは `make USE_PY_CFG=0` で C++ 版 `cfg.exe` にフォールバック |
| `Python interpreter not found` (Makefile が make 開始直後にエラーで停止) | Makefile が `python` / `python3` / `py -3` のいずれも検出できなかった．`make PYTHON=<絶対パス>` で明示指定するか，Python 3.7+ をインストールして PATH に追加 |
| `cfg.exe` が見つからない | デフォルトは Python 版なので通常発生しない．`USE_PY_CFG=0` を指定したのに発生する場合は `cfg/cfg/cfg.exe` の存在確認 (本リポジトリには非同梱．README.md セットアップ参照) |
| `Cannot create temporary file in C:\WINDOWS\` | (msys make でのみ発生) `make TMP="C:/Users/<user>/AppData/Local/Temp" TEMP=...` で TMP を明示．STM32CubeIDE では発生しない |
| 並列ビルドで `Os_Cfg.h: No such file or directory` | 並列依存設定に問題が無いか確認 (ATK2 では Makefile に order-only 依存を入れて対応済み) |
| シリアルに何も出ない | ST-Link Virtual COM Port のドライバ最新版を入れる．[ST 公式](https://www.st.com/en/development-tools/stsw-link009.html) |

## 10. サンプルアプリケーション

`sample/sample1.c` を流用 (ATK2 オリジナルの汎用テストプログラム)．

USART3 にプロンプト `Input Command:` が出るので，下記コマンドを 1 文字
入力すると対応する処理が走る．

主要コマンド (本ボードでよく使うもの):

| キー | 内容 |
|---|---|
| `1` 〜 `5` | 操作対象タスクの選択 |
| `a` | 選択中タスクを `ActivateTask` |
| `e` | 選択中タスクに `SetEvent(MainEvt)` |
| `s` | `Schedule()` 呼出 |
| `b` | アラームベース情報の表示 |
| `B` | アラームの残ティック数表示 |
| `T` | HW カウンタ (`MAIN_HW_COUNTER`) 値の表示 |
| `6` | **HW カウンタ動作確認** (5 秒×4 回ログ出力) ※本移植版で追加 |
| `Z` | 選択中タスクの状態表示 |
| `x` | CPU 例外を起こす (`RAISE_CPU_EXCEPTION`) |

## 11. 既知の制限

- 書き込み実行 (ROM 実行) のみサポート．RAM 実行は非対応．
- TrustZone (Cortex-M33 Secure 側) は未対応．Non-Secure ビルドのみ．
- USART3 以外のシリアル I/F は未対応．
- DMA / 高度な電源制御は未使用．

## 12. バージョン履歴

- 2026-04: NUCLEO-H563ZI への ATK2/SC1 ポートを新規作成．
  - ARMv8-M Cortex-M33 + FPU (LAZYSTACKING デフォルト)
  - HW カウンタ (TIM2/TIM5)，シリアル (USART3) 実装
  - STM32CubeIDE 2.1.1 用プロジェクト同梱
