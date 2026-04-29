# Phase 2: ターゲット依存部の作成

## 目的

EK-RA6M5 ボード固有のターゲット依存部 `target/ek_ra6m5_llvm/` を整備し，
Phase 1 のチップ依存部 (`arch/arm_m_llvm/ra_fsp/`) と組合せてビルド可能な
状態にする．Smart Configurator 出力 (`fsp/configuration.xml` + ローカル
生成 `fsp/ra/`/`ra_cfg/`/`ra_gen/`) の取り込みも本フェーズで完結．

## 前提

- Phase 1 完了．`arch/arm_m_llvm/ra_fsp/`, `arch/arm_m_llvm/common/`,
  `arch/llvm/` がコミット済．
- Phase 2-B 骨格 (`target/ek_ra6m5_llvm/` 一式) はコミット `9c7561e`
  時点で完成．以後は Phase 2-A の Smart Configurator 出力を取り込んで
  暫定値を実値に置換する作業．
- 開発環境:
  - Renesas FSP 6.4.0 (Smart Configurator sc_v2025-12)．
    `C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rasc.exe` または
    e² studio 同梱版．
  - ARM LLVM ATfE 21.1.1 (`C:/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/
    toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin/clang.exe`).

## 役割分担

| 担当 | 範囲 |
|---|---|
| **ユーザ (人間)** | §B のみ — rasc.exe / e² studio で `configuration.xml` を作成 → `Generate Project Content` で保存 → Claude に通知 |
| **Claude** | §C 以降全部 — git status 確認 / configuration.xml 内容確認 / commit / `rascc --generate` (必要時) / 生成物検証 / INTNO 抽出 / `target_serial.{h,arxml}` `target_hw_counter.{h,arxml}` の暫定値置換 + commit / Phase 3 (`obj/obj_ek_ra6m5/Makefile` 作成 + 初回ビルド) |

## 設計判断 (確定済)

| ID | 判断 |
|---|---|
| (A) | **FSP ソースは同梱しない**．`target/<TARGET>/fsp/configuration.xml` のみ commit．clone 後ユーザ/Claude が `rascc --generate` で `fsp/ra/` `fsp/ra_cfg/` `fsp/ra_gen/` 生成 (gitignore) |
| (B) | ベクタテーブルは ATK2 cfg pass2 生成 (`Os_Lcfg.c`) を使う．FSP 生成 `g_vector_table[]` は除外 |
| (C) | コンパイラは ARM LLVM (ATfE 21.1.1)．`--target=arm-none-eabi` |
| (D) | RA ファミリ汎用 chip 層．`MCU_GROUP` (`ra6m5` 等) と `CORE_CPU` (`cortex-m33`/`cortex-m85`) を `Makefile.target` で指定 |
| (E) | シリアル (ログ出力) は **SCI7 (Arduino D0/D1)**．EK-RA6M5 J24 ヘッダ Pin 0 = RX = P614 = RXD7，Pin 1 = TX = P613 = TXD7．115200bps．外付け USB-Serial 変換アダプタ前提．J-Link OB VCOM (SCI9) は使用しない |
| (F) | HW カウンタは GPT320 (Free Run, PCLKD/4) + GPT321 (One-Shot, PCLKD/4)．`TIMER_CLOCK_HZ = 25_000_000` (= 25 MHz tick)．OsSecondsPerTick = 4.0e-08 |
| (G) | 割込み優先度: `tmin_basepri=0x10`, GPT321 INTPRI=1, SCI7 RXI INTPRI=2, PendSV=0xFF, SVCall=0xE0 |
| (H) | `hardware_init_hook()` は空 (BSS 前)．FSP `SystemInit()` は BSS 領域変数を触るため `target_hardware_initialize()` (BSS 後; StartOS 経由) で呼ぶ |
| (I) | `target_initialize()` で `R_ICU->IELSR[i] = g_interrupt_event_link_select[i]` を転記．VTOR は `prc_initialize()` で ATK2 ベクタへ確定書込 |

### Phase 2 で確定すべき残課題

- **`vector_data.c` の取扱方式**: FSP 生成 `vector_data.c` は
  `g_vector_table[]` (ATK2 と衝突) と `g_interrupt_event_link_select[]`
  (必須) が同居．以下を試行順で確定:
  - **(a) 抽出**: `g_interrupt_event_link_select[]` だけ
    `target_irq_data.c` に転記してビルド対象に追加，`vector_data.c` は除外．
  - **(b) リネーム**: `vector_data.o` ビルド後に `llvm-objcopy
    --redefine-sym g_vector_table=fsp_g_vector_table_unused` で衝突回避．
  - **(c) リンカ廃棄**: リンカスクリプトの `/DISCARD/` で破棄．

  `target/ek_ra6m5_llvm/Makefile.target` の現状は (a) 仮定で
  `vector_data.o` を `KERNEL_COBJS` から除外．Phase 3 ビルド試行で確定．

---

## Phase 2-A: configuration.xml の取得 + FSP ローカル生成

### A. 前提状態の確認

- [ ] ブランチ `feat/ek_ra6m5_phase1` 上にいる
- [ ] `target/ek_ra6m5_llvm/` 一式が存在 (commit `9c7561e`)
- [ ] Smart Configurator (rasc.exe または e² studio) インストール済み

### B. ユーザ手作業: Smart Configurator GUI で `configuration.xml` 作成

> **方針: in-place 作成** — Project location を `target/ek_ra6m5_llvm/`
> に直接指定する．configuration.xml は最初から正しい位置に出力される．
> 後日のドライバ追加修正も同じプロジェクトを開けば良い．

#### B-1. 新規プロジェクト作成 (in-place)

`rasc.exe` (`C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rasc.exe`) または
e² studio v2025-12 の新規プロジェクトウィザードを起動．

| 設定項目 | 値 |
|---|---|
| **Project location** | `target/ek_ra6m5_llvm/` (Use default location チェック外し → Browse) |
| **Project name** | `fsp` (= `target/ek_ra6m5_llvm/fsp/` が新規作成される) |
| **Board** | EK-RA6M5 |
| **Toolchain** | LLVM Embedded Toolchain for Arm (ATfE) |
| **Device** | R7FA6M5BH3CFC |
| **Project Type** | Flat (Non-TrustZone) Project |
| **RTOS** | No RTOS |

#### B-2. configuration.xml の構成

`target/ek_ra6m5_llvm/fsp/configuration.xml` を開いて設定:

- **Clocks タブ**: HOCO 20MHz → PLL → ICLK 200MHz, PCLKD = ICLK/2 = 100MHz
- **Stacks タブ** (各ドライバの "Name" を下表のとおり指定．既定の
  `g_uart0`/`g_timer0`/... ではなく **用途を表す名前**):

  | カテゴリ | ドライバ | チャネル / モード | **Name** | 用途 |
  |---|---|---|---|---|
  | Connectivity | `r_sci_uart` | **SCI7** | **`g_uart_log`** | ログ出力．115200bps, 8N1 |
  | Timers | `r_gpt` (1) | GPT320, 32-bit, Free Run, PCLKD/4 | **`g_timer_freerun`** | フリーランニング (`MAIN_HW_COUNTER` 現在値) |
  | Timers | `r_gpt` (2) | GPT321, 32-bit, One-Shot, PCLKD/4 | **`g_timer_alarm`** | ワンショットアラーム |
  | Input | `r_ioport` | デフォルト | **`g_ioport`** | GPIO/PFS．`g_ioport_ctrl` を `R_IOPORT_Open` に渡す |

  > Name は画面右ペインの "Properties" タブ「Common → Name」で設定．
  > これにより `ra_gen/hal_data.{c,h}` のシンボル (`g_uart_log_ctrl`,
  > `g_timer_freerun_ctrl` …) と target ソースの参照が一貫する．

- **Pins タブ**: P614=RXD7 (Arduino D0 / Pin 0), P613=TXD7 (Arduino D1 /
  Pin 1) を AF (SCI7) に設定．他は既定のまま．

設定が完了したら **`File → Save` (Ctrl+S)** で `configuration.xml` を
保存．`Generate Project Content` を **クリックする必要は無い** —
`ra/` `ra_cfg/` `ra_gen/` の生成は Claude が §C-4 で `rascc --generate`
で実行する．**ユーザの GUI 作業はここまで**．rasc/e² studio を閉じて
Claude に **「Phase 2-A §B 完了．§C 以降を引き継いで」** と通知．
git 操作・CLI 操作は不要．

> Generate Project Content をクリックしても害はない (= IDE/CMake 副
> 生成物も全て gitignore 済) が，余計な処理時間がかかるだけ．Save 一発
> で十分．

#### B-3. 後日のドライバ追加・構成変更

configuration.xml と (Claude 生成済の) `fsp/ra/` 等が揃った状態で，
rasc.exe / e² studio の `Open Project` で `target/ek_ra6m5_llvm/fsp/` を
開けば，Stacks/Pins 編集 → Generate Project Content で in-place 再生成
できる．以後の commit / `rascc --generate` も Claude に引き継げる．

### C. configuration.xml の commit + `rascc --generate` 実行 〔Claude〕

§B 完了通知を受けたら，Claude が下記を順次実行．

#### C-1. `target/ek_ra6m5_llvm/fsp/` の状態確認

```sh
git status target/ek_ra6m5_llvm/fsp/
```

期待: `configuration.xml` のみが untracked / modified．他のファイル
(`CMakeLists.txt`, `ra/`, `ra_cfg/`, `ra_gen/`, `.secure_*`, ...) は
`.gitignore` で除外されているため何も表示されない．

副生成物が untracked として現れる場合は `.gitignore` のパターン不足．
そのまま add せず，パターンを追加する commit を別途作ってからユーザに
確認する．

#### C-2. configuration.xml の内容確認

`target/ek_ra6m5_llvm/fsp/configuration.xml` を Read / Grep で確認．

| 項目 | 期待値 |
|---|---|
| `<option key="#Board#" .../>` | `board.ra6m5ek` |
| `<option key="#TargetName#" .../>` | `R7FA6M5BH3CFC` |
| `<option key="#FSPVersion#" .../>` | `6.4.0` |
| `<option key="#SELECTED_TOOLCHAIN#" .../>` | `com.renesas.cdt.managedbuild.llvm.arm.` |
| `<configSetting altId="p613.sci7.txd" .../>` | あり (Arduino D1 / TX) |
| `<configSetting altId="p614.sci7.rxd" .../>` | あり (Arduino D0 / RX) |
| `<configSetting altId="sci7.mode.asynchronous.free" .../>` | あり |

期待値と異なる場合はユーザに確認．

#### C-3. configuration.xml の commit

```sh
git add target/ek_ra6m5_llvm/fsp/configuration.xml
git commit -m "target/ek_ra6m5_llvm: configuration.xml 追加 (Smart Configurator baseline)

FSP 6.4.0 (sc_v2025-12) 用．Board=EK-RA6M5, R7FA6M5BH3CFC,
ICLK=200MHz, SCI7 (g_uart_log), GPT320 (g_timer_freerun),
GPT321 (g_timer_alarm), IOPORT (g_ioport), Flat Non-TrustZone．"
```

#### C-4. `rascc --generate` 実行

`fsp/ra/` `fsp/ra_cfg/` `fsp/ra_gen/` を生成．ユーザは `File → Save` だけ
で configuration.xml を保存している前提なので，Claude は **必ず本コマンド
を実行**する．

```sh
"C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rascc.exe" \
    --generate \
    --device R7FA6M5BH3CFC \
    --compiler LLVMARM \
    target/ek_ra6m5_llvm/fsp/configuration.xml
```

成功条件:
- exit code = 0
- `target/ek_ra6m5_llvm/fsp/ra/fsp/inc/fsp_version.h` が生成される
- `target/ek_ra6m5_llvm/fsp/ra_cfg/fsp_cfg/bsp/bsp_cfg.h` が生成される
- `target/ek_ra6m5_llvm/fsp/ra_gen/vector_data.c` が生成される

> GUI の `Generate Project Content` ボタンと CLI `rascc --generate` は
> 機能等価．入力は同じ configuration.xml，出力は同じ
> `fsp/{ra,ra_cfg,ra_gen,IDE副生成物}`．本フローでは GUI 側は Save の
> みに留め，生成は CLI で Claude がまとめて実行する．

詳細は [`arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md`](arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md)．

### D. 検証 〔Claude〕

Read / Grep / Bash で確認:

- [ ] `target/ek_ra6m5_llvm/fsp/configuration.xml` が commit されている
- [ ] `target/ek_ra6m5_llvm/fsp/ra_cfg/fsp_cfg/bsp/bsp_cfg.h` に
      `BSP_MCU_GROUP_RA6M5` `BSP_MCU_R7FA6M5BH` の `#define` がある
- [ ] `target/ek_ra6m5_llvm/fsp/ra_gen/vector_data.c` に
      `g_interrupt_event_link_select[]` がある
- [ ] `target/ek_ra6m5_llvm/fsp/ra/fsp/inc/fsp_version.h` が
      `FSP_VERSION_MAJOR (6U)` `FSP_VERSION_MINOR (4U)` を定義
- [ ] `git status target/ek_ra6m5_llvm/fsp/` で `ra/` `ra_cfg/` `ra_gen/`
      が untracked にもならない (gitignore 効果)

### E. INTNO スロット番号の読取り 〔Claude〕

`target/ek_ra6m5_llvm/fsp/ra_gen/vector_data.c` の
`g_interrupt_event_link_select[]` 配列のインデックスから INTNO を導出:

| FSP イベント名 | 配列インデックス N | 対応 INTNO (= N + 16) |
|---|---|---|
| `BSP_PRV_VECTOR_EVENT_SCI7_RXI` | (要確認) | (要確認) |
| `BSP_PRV_VECTOR_EVENT_GPT321_OVF` (または相当) | (要確認) | (要確認) |

### F. ターゲット依存ソースへの INTNO 反映 〔Claude〕

§E で確定した値を Edit で反映:

1. `target/ek_ra6m5_llvm/target_serial.h` `INTNO_SIO` 暫定値 → 実値
2. `target/ek_ra6m5_llvm/target_serial.arxml` `OsIsrInterruptNumber` → 実値
3. `target/ek_ra6m5_llvm/target_hw_counter.h` `GPT321_INTNO` → 実値
4. `target/ek_ra6m5_llvm/target_hw_counter.arxml` `OsIsrInterruptNumber` → 実値
5. `vector_data.c` 取扱方式 (a)/(b)/(c) を Phase 3 のビルド試行で確定．
   それに応じて `Makefile.target` `KERNEL_COBJS` を修正．

修正をコミット (`target/ek_ra6m5_llvm: INTNO 反映 + vector_data.c 取扱
方式確定` 等)．

### G. リスクと事前回避

| 症状 | 原因 | 回避策 |
|---|---|---|
| `rascc --generate` が `Cannot invoke "...IPath.append..."` で失敗 | configuration.xml メタデータ不足 | GUI で 1 回開き直して再保存 |
| EK-RA6M5 で Arduino D0/D1 (P614/P613) が SCI7 でない | ボード Rev 違い | [EK-RA6M5 v1 User's Manual](https://www.renesas.com/ja/document/man/ek-ra6m5-v1-users-manual) で配線確認 |
| `BSP_MCU_GROUP_RA6M5` が定義されない | Board 選択漏れ | プロジェクト再生成 |
| `BSP_TZ_NONSECURE_BUILD` が定義されている | TrustZone を選んだ | Flat (Non-TrustZone) で再生成 |
| `g_interrupt_event_link_select[]` が `bsp_irq.c` の弱定義 (全 0) にフォールバック | `vector_data.c` 全除外で IELSR テーブルが消失 | 上記「設計判断 残課題」(a)/(b)/(c) を必ず確定 |

### H. ユーザが §B 完了時に Claude に渡すブリーフ (テンプレート)

```
Phase 2-A §B (Smart Configurator GUI) 完了．
target/ek_ra6m5_llvm/fsp/configuration.xml がローカルに作成済 (未 commit)．
構成: Board=EK-RA6M5, Device=R7FA6M5BH3CFC, FSP 6.4.0, LLVM,
      Flat Non-TrustZone, SCI7 (g_uart_log) + GPT320 (g_timer_freerun)
      + GPT321 (g_timer_alarm) + IOPORT (g_ioport)．
§C 以降 (commit / rascc / 検証 / INTNO 抽出 / target ソース反映) と
Phase 3 (obj/obj_ek_ra6m5/Makefile 作成 + 初回ビルド) を引き継いで．
```

---

## Phase 2-B: ターゲット依存部一式 (commit `9c7561e` で骨格完成)

### 構成

```
target/ek_ra6m5_llvm/
├── README.md, Makefile.target, target_*.{c,h}, *.arxml, *.tf,
│   ek_ra6m5.h, target_kernel.h, r7fa6m5bh.ld     ATK2 ターゲット依存ソース (committed)
└── fsp/
    ├── configuration.xml                          Smart Configurator 真値 (committed)
    ├── ra/, ra_cfg/, ra_gen/                      rascc --generate で生成 (gitignored)
    └── (rasc IDE/CMake 副生成物 — 全 gitignored)
```

### 主要ファイル

| ファイル | 内容 |
|---|---|
| `Makefile.target` | TARGET=ek_ra6m5_llvm, CHIP=ra_fsp, MCU_GROUP=ra6m5, FPU_USAGE=FPU_LAZYSTACKING, INCLUDES に `fsp/ra_cfg/` `fsp/ra_gen/` 追加, `KERNEL_COBJS` から `vector_data.o` 除外 (方式 (a) 仮置き), `EK_RA6M5_HAVE_VECTOR_DATA` `EK_RA6M5_USE_FSP_PINCFG` 定義 |
| `r7fa6m5bh.ld` | Flash 2MB @ 0x00000000, SRAM 512KB @ 0x20000000．`/DISCARD/ : *(.fixed_vectors)` で FSP `__VECTOR_TABLE` を保険破棄 |
| `ek_ra6m5.h` | `CPU_CLOCK_HZ=200_000_000`, `PCLKD_HZ=100_000_000`, LED1=P006/LED2=P004/LED3=P008, BPS_SETTING=115200 |
| `target_kernel.h` | スタックサイズ等．TMIN_INTNO/TMAX_INTNO/TBITW_IPRI は `arch/arm_m_gcc/common/prc_config.h` の値 (16/147/4) を流用 (TMAX_INTNO=147 は H5 由来；Phase 4 で 111 への絞り込み TODO) |
| `target_config.c` | 設計判断 (H): `hardware_init_hook` 空，`target_hardware_initialize` で `SystemInit()` + `R_IOPORT_Open` + SCI7 low-level init + `prc_hardware_initialize`．`target_initialize` で IELSR 設定 + `prc_initialize` |
| `target_serial.{c,h,arxml}` | SCI7 RX 割込み．INTNO 暫定 16 (★ TODO[Phase 2-A]) |
| `target_hw_counter.{c,h,arxml}` | GPT320 (Free Run) + GPT321 (One-Shot)．TPCS=DIV4 (= PCLKD/4 = 25 MHz)．INTNO 暫定 18 (★ TODO[Phase 2-A]) |
| `target_{sysmod,test,cfg1_out,rename,unrename}.h` | 標準セット |
| `target.tf`, `target_check.tf`, `target_offset.tf` | H5 同様 prc.tf を include する薄い派生 |

### Phase 2-A 完了後に Claude が反映する 5 項目 (= §F)

1. `target_serial.h` `INTNO_SIO` の実値
2. `target_serial.arxml` `OsIsrInterruptNumber` の実値
3. `target_hw_counter.h` `GPT321_INTNO` の実値
4. `target_hw_counter.arxml` `OsIsrInterruptNumber` の実値
5. `vector_data.c` 取扱方式 (a)/(b)/(c) の確定 (Phase 3 ビルド試行で)

### 既知の Phase 3 持ち越し事項

- `bsp_linker.c` (Option Setting Memory) を `KERNEL_COBJS` に追加するか
  判断．現状リンカスクリプトに `.option_setting_*` セクション無し．
- IDE (clangd) は `kernel_impl.h` `bsp_api.h` を解決できないため
  `target_config.c` `target_hw_counter.c` に多数のエラーマーカが出る．
  これは IDE の INCLUDE 設定問題で実ビルドには影響しない．

---

## 終了条件

- [ ] Phase 2-A §C-§F 完了 (configuration.xml commit + 生成物検証 +
      INTNO 反映 + commit)
- [ ] Phase 3 (`obj/obj_ek_ra6m5/Makefile` 作成) で `make -j4` が
      最後 (= pass3) まで通る
- [ ] BSP/FSP コードがエラーなくコンパイルされる (`bsp_clocks.o` 等)

実機書込みは Phase 4 に持ち越し．

## 後続フェーズへの引継

Phase 3 で `obj/obj_ek_ra6m5/Makefile` を `obj/obj_nucleo_h563zi/Makefile`
ベースに作成し，本層 + チップ層 + ATK2 共通カーネルを統合してリンク
可能な状態にする．configuration.xml は不変な真値として保持される．
