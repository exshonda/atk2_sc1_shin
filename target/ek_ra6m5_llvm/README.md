# EK-RA6M5 ターゲット依存部 (`target/ek_ra6m5_llvm`)

TOPPERS/ATK2 (SC1) の **Renesas EK-RA6M5 Evaluation Kit** ボード向け
ターゲット依存部．

ターゲット略称: `ek_ra6m5_llvm`
ボード製品ページ: <https://www.renesas.com/ja/products/microcontrollers-microprocessors/ra-cortex-m-mcus/ek-ra6m5-evaluation-kit-ra6m5-mcu-group>

> **ステータス: Phase 4 完了 (実機動作確認済)**．Phase 5 で cfg_py 回帰
> テスト整備済 ([`cfg/cfg_py/tests/test_integration_ek_ra6m5.py`](../../cfg/cfg_py/tests/test_integration_ek_ra6m5.py))．

## 1. 構成

### 1.1 層構造

| 層 | パス | 役割 |
|---|---|---|
| **ターゲット (本層)** | `target/ek_ra6m5_llvm/` | EK-RA6M5 ボード固有 |
| チップ依存部 | `arch/arm_m_llvm/ra_fsp/` | Cortex-M33 + 96-slot ICU + Renesas FSP 6.4.0 |
| プロセッサ依存部 (LLVM 用 Makefile) | `arch/arm_m_llvm/common/` | ARM LLVM (ATfE) 用ビルド設定 |
| プロセッサ依存部 (ソース) | `arch/arm_m_gcc/common/` | start.S, prc_config.{c,h}, prc_support.S 等．LLVM ビルドからは vpath で参照 (untouched) |
| AUTOSAR Compiler 抽象 (LLVM ブリッジ) | `arch/llvm/` | Compiler.h, Compiler_Cfg.h．`arch/gcc/` を取込 (clang は GCC 互換属性を受け入れる) |

### 1.2 本層内のファイル区分 (committed vs Smart Configurator 生成)

`target/ek_ra6m5_llvm/` 直下は **ATK2 ターゲット依存ソース (committed)**，
`target/ek_ra6m5_llvm/fsp/` 配下は **Renesas FSP 関連 (大半が
gitignore)** という明確な境界がある．

| 範囲 | committed | gitignored | 備考 |
|---|---|---|---|
| `target/ek_ra6m5_llvm/{Makefile.target, target_*.{c,h}, *.arxml, *.tf, ek_ra6m5.h, r7fa6m5bh.ld, README.md}` | ✓ | | ATK2 開発者が手書きするコード．本層の主体． |
| `target/ek_ra6m5_llvm/fsp/configuration.xml` | ✓ | | Smart Configurator のソース (真値)．**fsp/ 配下で唯一の committed**．ユーザが GUI で編集→上書き保存． |
| `target/ek_ra6m5_llvm/fsp/ra/`, `ra_cfg/`, `ra_gen/` | | ✓ | rascc --generate が出力．configuration.xml から完全再生成可能なので commit 不要． |
| `target/ek_ra6m5_llvm/fsp/{CMakeLists.txt, Config.cmake, cmake/, *.lld, script/, src/, .secure_*, .theia/, *.code-workspace, ...}` | | ✓ | rasc.exe in-place 生成プロジェクトの IDE/CMake/LLD 副生成物．ATK2 ビルドは使わない． |
| `target/ek_ra6m5_llvm/e2studio/sample_debug/` | ✓ | | デバッグ専用 e² studio プロジェクト (`.project` + `*.launch`)．`.metadata/`, `.settings/` は gitignore． |

`git status target/ek_ra6m5_llvm/fsp/` は **`configuration.xml` 以外
何も表示されない** のが期待状態．

## 2. 開発環境と動作確認バージョン

| ツール | 動作確認バージョン | 備考 |
|---|---|---|
| **ARM LLVM (Arm Toolchain for Embedded; ATfE)** | **21.1.1** | Renesas e² studio v2025-12 同梱．`clang --target=arm-none-eabi` |
| llvm-ar / llvm-nm / llvm-objcopy / llvm-objdump | ATfE 21.1.1 同梱 | ATfE bin/ ディレクトリ内 |
| GNU Make | 4.4 (msys2 / e² studio 同梱) | e² studio 同梱版でも可 |
| **Renesas FSP** | **6.4.0** (Smart Configurator sc_v2025-12) | `configuration.xml` 編集に必須 |
| **rascc.exe** | FSP 6.4.0 同梱 | `<sc_install>/eclipse/rascc.exe`．`fsp/ra/` `ra_cfg/` `ra_gen/` の生成に使用 |
| ATK2 cfg (Python 版) | 同梱 `cfg/cfg_py/cfg.py` (デフォルト) | Python 3.7+ |
| **e² studio** (デバッグ用) | **v2025-12 (FSP 6.4.0)** | デバッグ専用．ビルドには使わない |
| **J-Link Software** | **V9.20** 以降 | `JLink.exe` フラッシュ書込 + `JLinkGDBServer` (e² studio 経由) |
| ホスト OS | Windows 11 | msys2 bash (`make`) + e² studio (デバッグ) |

## 3. メモリマップ

R7FA6M5BH のメモリマップ:

| 領域 | アドレス | サイズ | 用途 |
|---|---|---|---|
| 内蔵 Flash | `0x00000000` 〜 `0x001FFFFF` | 2 MB | `.vectors` / `.text` / `.rodata` / `.data` (LMA) |
| 内蔵 SRAM | `0x20000000` 〜 `0x2007FFFF` | 512 KB | `.data` (VMA) / `.bss` / スタック |
| Option Setting Memory | `0x0100A100` 〜 | 256 B | OFS0 / OFS1 / OSIS (リンカスクリプトで配置) |
| I/O 領域 | `0x40000000` 〜 | 256 MB | ペリフェラル |

リンカスクリプト: [`r7fa6m5bh.ld`](r7fa6m5bh.ld)．SRAM 末尾 (`_estack`)
を初期 MSP として使用．Option Setting Memory は `bsp_linker.c`
(FSP 提供) を `.option_setting_*` セクションへ配置．

## 4. システムクロック

`fsp/configuration.xml` (Smart Configurator → Clocks タブ) で構成:

| 項目 | 値 |
|---|---|
| クロックソース | HOCO 20MHz (内蔵高速発振) |
| PLL | M=2, N=40, P=2 → 200 MHz |
| ICLK (CPU) | 200 MHz |
| PCLKA (バス) | 100 MHz |
| PCLKB (SCI) | 50 MHz |
| PCLKD (タイマ) | 100 MHz |
| 電源モード | High-speed |

`ek_ra6m5.h` の `CPU_CLOCK_HZ` で 200 MHz，`PCLKD_HZ` で 100 MHz を
定数化．Smart Configurator 生成 `bsp_clock_cfg.h` と一致させること．

## 5. 使用するシステムリソース

### GPIO

| 信号 | ピン | 役割 | 代替機能 |
|---|---|---|---|
| SCI7_RXD | P614 (Arduino J24-D0) | シリアル受信 | AF (SCI7) |
| SCI7_TXD | P613 (Arduino J24-D1) | シリアル送信 | AF (SCI7) |
| LED1 (Blue) | P006 | (アプリ用予約) | GPIO Out |
| LED2 (Green) | P004 | (アプリ用予約) | GPIO Out |
| LED3 (Red) | P008 | (アプリ用予約) | GPIO Out |
| User SW (S2) | P009 | (未使用) | GPIO In |

### ペリフェラル

| 用途 | ペリフェラル | 詳細 |
|---|---|---|
| シリアル (SIO) | **SCI7** | 115200 bps, 8N1, 割込み駆動 RX (`INTNO_SIO=17`, INTPRI=2) |
| ハードウェアカウンタ (フリーランニング) | **GPT320** | 32-bit, PCLKD/4 = 25 MHz tick．割込み未使用 |
| ハードウェアカウンタ (アラーム) | **GPT321** | 32-bit, ワンショット, PCLKD/4 = 25 MHz tick．割込み有効 (`GPT321_INTNO=16`, INTPRI=1) |

ATK2 の `MAIN_HW_COUNTER` は **`TIMER_CLOCK_HZ = 25 MHz`** (PCLKD/4)
基準で動作．`target_hw_counter.h` で `TICK_FOR_1MS = 25000`,
`TICK_FOR_1S = 25000000` を定数化．サンプルは 10 ms 周期でタスクを
起こす `MainCycArm` アラームを `MAIN_HW_COUNTER` 上に構成している．

> **注**: NUCLEO-H563ZI は 1 MHz tick (1 us 単位) だが，本ターゲットは
> 25 MHz tick (40 ns 単位)．`OsSecondsPerTick` は ARXML 側で揃えている．

### シリアル経路

EK-RA6M5 の **J24 Arduino 互換ヘッダ** 経由で外付け USB-Serial 変換
アダプタを接続して使う想定．**J-Link OB Virtual COM Port (SCI9) は
使用しない**．

```
EK-RA6M5 J24 (Arduino D0/D1)
   Pin 0 (D0, RX) = P614  ←─ Tx of USB-Serial adapter
   Pin 1 (D1, TX) = P613  ─→ Rx of USB-Serial adapter
                  ↓
              SCI7 (RXI on slot 1, TXI/TEI/ERI disabled at INTPRI=15)
```

### ICU IELSR (Interrupt Event Link Select)

RA6M5 は NVIC スロット 0..95 に **任意の RA イベント** を ICU.IELSR で
動的に割付ける構造．Smart Configurator が `ra_gen/vector_data.c` に
`g_interrupt_event_link_select[]` として配列を生成し，`target_irq_data.c`
(本層) で抽出して `target_initialize()` 中に `R_ICU->IELSR[]` へ転記する．

| NVIC スロット | INTNO | RA イベント | 用途 |
|---|---|---|---|
| 0 | 16 | `BSP_PRV_VECTOR_EVENT_GPT0_COUNTER_OVERFLOW` (GPT321 OVF) | HW カウンタアラーム |
| 1 | 17 | `BSP_PRV_VECTOR_EVENT_SCI7_RXI` | シリアル受信 |
| 2 | 18 | (TXI; 本ポートでは無効) | — |
| 3 | 19 | (TEI; 本ポートでは無効) | — |
| 4 | 20 | (ERI; 本ポートでは無効) | — |

> Smart Configurator の **Properties → Interrupts → Priority** で
> `g_timer_alarm` を 13, `g_uart_log` RXI を 14, TXI/TEI/ERI を 15 に
> 設定済．これは ATK2 の INTPRI (1〜15) ではなく FSP の NVIC 物理優先度
> (0〜15) なので注意．

### 例外ハンドラ優先度

ARM Cortex-M33 の優先度ビット幅は 4 bit (0x00 〜 0xF0):

| 用途 | 優先度 (raw) | 備考 |
|---|---|---|
| C2ISR の最高優先度 (`tmin_basepri`) | 0x10 | OS 割込み禁止の閾値 |
| GPT321 (HW カウンタアラーム) | 0x10 | INTPRI=1 |
| SCI7 RXI | 0x20 | INTPRI=2 |
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

割込み番号の範囲と優先度ビット幅 (`TMIN_INTNO=16`, `TMAX_INTNO=111`,
`TNUM_INT=96`, `TBITW_IPRI=4`) はチップ層
[`arch/arm_m_llvm/ra_fsp/chip_config.h`](../../arch/arm_m_llvm/ra_fsp/chip_config.h)
で定義される．RA6M5 の ICU イベントリンクスロット数
(`BSP_ICU_VECTOR_NUM_ENTRIES = 96`) と一致．

`Makefile.target` では:

| 変数 | 値 | 内容 |
|---|---|---|
| `FPU_USAGE` | `FPU_LAZYSTACKING` | デフォルト．他の値は `arch/arm_m_gcc/common/README.md` 参照 |
| `MCU_GROUP` | `ra6m5` | FSP `bsp/mcu/<group>/` の選択．`Makefile.chip` の `INCLUDES` に渡る |
| `TOPPERS_TZ_S` | (define) | `arm_m.h` の `EXC_RETURN` を Secure (`0xFFFFFFFD`) に切替．RA6M5 + FSP "Flat Non-TrustZone Project" は実装上 Full Secure 動作のため必須 |

## 7. ファイル構成

```
target/ek_ra6m5_llvm/
├── README.md                       このファイル
├── Makefile.target                 Makefile のターゲット依存部 (TOPPERS_TZ_S 等)
├── r7fa6m5bh.ld                    リンカスクリプト (Flash/SRAM/Option Setting Memory)
├── ek_ra6m5.h                      ボード資源定義 (ピン, クロック, LED)
├── target_kernel.h                 カーネル設定 (スタックサイズ等)
├── target_config.c / .h            初期化・SCI7 ドライバ・ISR テーブル
│                                   (SystemInit + R_IOPORT_Open + IELSR セットアップ)
├── target_irq_data.c               g_interrupt_event_link_select[] を vector_data.c
│                                   から抽出した IELSR 元データ
├── target_serial.h                 sysmod/serial.c 用 (INTNO_SIO=17 等)
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
├── e2studio/                       e² studio デバッグ専用プロジェクト (§9)
│   └── sample_debug/
│       ├── .project
│       └── sample_debug DebugOnly.launch
└── fsp/                            Renesas FSP 関連 (本サブツリーに集約)
    ├── configuration.xml           Smart Configurator 真値 (committed)
    ├── ra/                         rascc --generate 生成 (gitignored)
    │   └── fsp/                    FSP 本体 (inc/, src/bsp/, src/r_*/)
    ├── ra_cfg/                     rascc --generate 生成 (gitignored)
    │   └── fsp_cfg/                bsp_cfg.h, bsp_clock_cfg.h ほか
    └── ra_gen/                     rascc --generate 生成 (gitignored)
        ├── common_data.{c,h}, hal_data.{c,h}, pin_data.c, vector_data.{c,h}
```

## 8. ビルド方法 (1) - Make + msys2 + ATfE

最小工数のコマンドラインビルド．Windows + msys2 環境で動作確認済み．

### 必要なもの

- **ARM LLVM (ATfE) 21.1.1**．Renesas e² studio v2025-12 同梱．
  - 標準パス: `C:/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin/`
- **GNU Make 4.x** (msys2 もしくは Renesas e² studio 同梱版)
- **Python 3.7+** (cfg_py 用)
- **Renesas FSP + Smart Configurator 6.4.0** (clone 後の初回セットアップ用)

### 8.1 初回セットアップ (clone 後 1 回のみ)

FSP ソースは本リポジトリに **同梱しない**．`rascc.exe --generate` で
`target/ek_ra6m5_llvm/fsp/` 配下に展開する:

```sh
# rascc.exe の標準パス (Windows; bash の場合は forward-slash)
RASCC='/c/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rascc.exe'
"$RASCC" --generate target/ek_ra6m5_llvm/fsp/configuration.xml
```

これで `target/ek_ra6m5_llvm/fsp/{ra,ra_cfg,ra_gen}/` が生成される．
詳細手順は
[`arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md`](../../arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md)
参照．

### 8.2 ビルド手順

ATfE clang を `PATH` に通してから make:

```sh
# bash 1 行で (Windows / msys2)
export PATH="/c/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin:$PATH"
cd obj/obj_ek_ra6m5
make -j4
```

生成物 (build directory):

- `atk2-sc1` (ELF)
- `atk2-sc1.srec` (S-record, 書込み用)
- `atk2-sc1.dump` (`llvm-objdump -d`)
- `atk2-sc1.map` (リンクマップ)

### 8.3 フラッシュ書き込み (J-Link)

`make flash` で SEGGER J-Link 経由でボードへ書込み．`R7FA6M5BH` を
固定で渡している:

```sh
make flash
```

内部実行コマンド:

```
JLink.exe -device R7FA6M5BH -if SWD -speed 4000 -CommandFile flash.jlink
```

`flash.jlink` は `Makefile` 内で動的生成 (loadbin + reset + go)．
`-device` を引数で渡すことでターゲットプロセッサ選択 GUI を抑止している．

## 9. ビルド方法 (2) - e² studio (デバッグ専用)

### 9.1 e² studio でビルドできない理由

**e² studio v2025-12 は Make ベースの外部ビルドをサポートしていない**．
RA 系プロジェクトの CDT 構成は CMake バックエンド (`com.renesas.cdt.build.cmake.*`
プラグイン) が前提で，本リポジトリのように `obj/obj_ek_ra6m5/Makefile`
+ ATfE clang を直接駆動する構成は IDE 内で再現できない．したがって
**ビルドは §8 のコマンドライン (`make -j4`) を必ず使う**．

e² studio は本ターゲットでは **デバッグ目的のみ** に使用する．make で
出力した `obj/obj_ek_ra6m5/atk2-sc1` (ELF) を IDE が J-Link 経由でフラッシュ
書込み・GDB ステップ実行に流すだけ．`target/ek_ra6m5_llvm/e2studio/sample_debug/`
は CDT のソースインデックスもビルド構成も持たない最小プロジェクトで，
立ち上げに `.project` と `*.launch` だけがあれば足りる作りになっている．

### 9.2 デバッグセッションを開始する手順

1. e² studio v2025-12 を起動し，ワークスペースを **任意の場所** に設定．
   本リポジトリ内である必要は無い．
2. メニュー: `File → Import → General → Existing Projects into Workspace`
3. `Select root directory:` に
   `target/ek_ra6m5_llvm/e2studio` を指定．
4. `sample_debug` プロジェクトにチェックが入っていることを確認し，
   `Finish`．
5. プロジェクトツリーから `sample_debug` を右クリック →
   `Debug As → Renesas GDB Hardware Debugging` (初回は
   `sample_debug DebugOnly` 構成を選択)．
6. 自動で J-Link が atk2-sc1 (ELF) をフラッシュへ書込み，`main()` 先頭
   で停止する．

> **注意**: `Copy projects into workspace` には **チェックを入れない**．
> プロジェクトは元の場所から参照する形が想定．

### 9.3 ELF パスの設定

デバッグ構成で参照する ELF パスは launch ファイル内で
`${workspace_loc:/${ProjName}}/atk2-sc1` 等の Eclipse 変数を使うのではなく，
本リポジトリでは **`obj/obj_ek_ra6m5/atk2-sc1`** (絶対パス) を直接指定して
いる．launch ファイルを開いて `Main` タブの `C/C++ Application` フィールド
を環境に合わせて編集する必要がある．

### 9.4 シリアル出力の確認

EK-RA6M5 の **J24 Arduino ヘッダ** に外付け USB-Serial 変換アダプタを
接続:

- ホスト PC でアダプタが認識される COM ポートを開く．
- 設定: 115200 bps, 8 N 1, フロー制御無し．
- Tera Term / PuTTY / serial-mcp-server (`https://github.com/adancurusul/serial-mcp-server`) 等．

## 10. 既知の制限

- **TZEN=1 (TrustZone Secure / Non-Secure 分割) は未対応**．本ポートは
  RA + FSP "Flat (Non-TrustZone) Project" 前提で，デバイスは OFS1.TZEN=0
  の **Full Secure 単一** で動作する (`Makefile.target` の `-DTOPPERS_TZ_S`
  はこの動作に対応する `EXC_RETURN` 値を選ぶための指定．§6 を参照)．
  Secure / Non-Secure 分割を行う場合は別途 NSC 表や Veneer 配置等の
  対応が必要．
- **ROM 実行のみサポート**．RAM 実行は非対応．
- **SCI7 以外のシリアル I/F は未対応**．他 SCI / USB-CDC は配線変更で
  追加可能だが本層では未実装．
- **DMA / DTC / DAC / ADC** 等は未使用．`configuration.xml` に Stack
  追加 → `rascc --generate` 再実行で取込めるが本サンプル動作には不要．
- **Backup Domain / RTC** は未使用．
- **`vector_data.c` (FSP 生成)** は ATK2 ベクタテーブルと衝突するため，
  `Makefile.target` の `KERNEL_COBJS` から除外している．代わりに
  `target_irq_data.c` に `g_interrupt_event_link_select[]` のみを切り出して
  ビルド対象としている．**割込みの追加や INTNO 変更を行うときは
  Smart Configurator → `rascc --generate` → `target_irq_data.c` への手動
  反映 → ARXML/ヘッダの INTNO 更新の順で作業する．背景と詳細手順は
  [`arch/arm_m_llvm/ra_fsp/README.md` §6.3](../../arch/arm_m_llvm/ra_fsp/README.md#63-vector_datac-の取扱-重要ek-ra6m5-では方式-a-を採用)
  を参照．**

## 11. バージョン履歴

- 2026-04: Phase 1〜4 完了．EK-RA6M5 への ATK2/SC1 ポートを新規作成．
  - ARMv8-M Cortex-M33 + FPU (LAZYSTACKING デフォルト)
  - Cortex-M33 + 96-slot ICU + FSP 6.4.0
  - HW カウンタ (GPT320/GPT321 @ 25MHz tick)，シリアル (SCI7 @ 115200)
  - `EXC_RETURN = 0xFFFFFFFD` (Full Secure: ES=1, S=1)．`-DTOPPERS_TZ_S`
    で指定．
  - e² studio デバッグ専用プロジェクト (`sample_debug/`) 同梱
  - Phase 5 で cfg_py 回帰テスト整備 (`cfg/cfg_py/tests/test_integration_ek_ra6m5.py`)
