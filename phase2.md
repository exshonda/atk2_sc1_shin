# Phase 2: ターゲット依存部の作成

## 新セッション着手手順 (Handoff)

> 本節は **後続セッション (別の Claude / 開発者) が Phase 2 を引き継ぐ際**
> の起点情報．Phase 1 までの全コンテキストをここに集約してある．以下を
> 上から順に確認すれば cold start でも進められる．

### 0-1. ブランチと commit 履歴

リポジトリ: `c:/home/proj/edge-ai/embcode/atk2_ra6m5/work/atk2_sc1_shin`
ブランチ: `feat/ek_ra6m5_phase1` (Phase 2 もこのブランチで継続．Phase 完了時に PR 化を検討)

main からの差分 commit (新しい順):

| Commit | 内容 |
|---|---|
| (今後) | ARM LLVM への移行: `arm_m_gcc` → `arm_m_llvm`，`ek_ra6m5_gcc` → `ek_ra6m5_llvm`．FSP 同梱撤回．SCI7 (Arduino D0/D1) 採用 |
| `de6603c` | phase2.md: rascc/rasc CLI 関連の記述追加 (歴史的．新方針で再整理) |
| `022c0b5` | phase2.md: ユーザー作業 Phase 2-A 説明 (歴史的) |
| `9c7561e` | `target/ek_ra6m5_llvm`: Phase 2-B 骨格 (ターゲット依存部一式) |
| `8028ff3` | phase2.md: Handoff セクション追加 |
| `d3bd62b` | docs: codex Phase 1 レビュー指摘を反映 |
| `75dcc0a` | phase1.md〜phase6.md 追加 |
| `650f82e` | (旧) `arch/arm_m_gcc/ra6m5_fsp/` Phase 1 骨格．**現在は arch/arm_m_llvm/ra_fsp/ に rename，FSP ソースは git rm 済**．最新 commit を参照． |
| `f0dfb10` | CLAUDE.md 初期化 |

### 0-2. 必読ファイル (この順)

1. `CLAUDE.md` — プロジェクト全体像・3-pass cfg ビルドフロー・層構造・H5 移植時の落とし穴．特に **「開発項目」** 節 (末尾) が本タスクのブリーフ．
2. `phase1.md` — Phase 1 の成果物と codex レビュー反映後のリスク表．
3. `arch/arm_m_llvm/ra_fsp/README.md` — **`§6.1` 起動経路と `§6.3` `vector_data.c` 取扱を必ず読む**．Phase 2 の実装方針はここに集約済．
4. 本ファイル (`phase2.md`) 残りの節．
5. `arch/arm_m_gcc/stm32h5xx_stm32cube/{Makefile.chip,chip_config.h,README.md}` および `target/nucleo_h563zi_gcc/{Makefile.target,target_config.c,target_hw_counter.c,nucleo_h563zi.h,stm32h563zi.ld,README.md}` — H5 版を **そのまま踏襲する** ターゲット層の見本．
6. `arch/arm_m_gcc/common/{start.S,Makefile.prc,prc_config.{c,h},prc_support.S}` — **絶対に変更しない** 共通プロセッサ依存部．
7. `obj/obj_nucleo_h563zi/Makefile` — Phase 3 で複製する Makefile の見本．

### 0-3. 確定した設計判断 (再議論不要)

| ID | 判断 | 根拠 |
|---|---|---|
| (A) | **FSP ソースはリポジトリに同梱しない**．`configuration.xml` のみコミットし，clone 後にユーザが `rascc.exe --generate` で `target/<TARGET>/fsp/ra/` `ra_cfg/` `ra_gen/` を生成．生成物は `.gitignore` で除外． | ユーザ確認済 (新方針) |
| (B) | ベクタテーブルは ATK2 cfg pass2 生成 (`Os_Lcfg.c`) を使う．FSP 生成 `g_vector_table[]` は除外 | ユーザ確認済 |
| (C) | `arch/arm_m_gcc/common/` は変更しない (LLVM ビルドでも同ディレクトリのソースを vpath 経由で再利用) | CLAUDE.md 開発項目 |
| (D) | **コンパイラは ARM LLVM (Arm Toolchain for Embedded; ATfE) 21.1.1** (`C:/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin/clang.exe`)．`--target=arm-none-eabi` でビルド | ユーザ指定 |
| (E) | RA ファミリ汎用 chip 層 (`arch/arm_m_llvm/ra_fsp/`)．`MCU_GROUP` (`ra6m5` 等) と `CORE_CPU` (`cortex-m33`/`cortex-m85`) を `Makefile.target` で指定．EK-RA6M5 以外のボードを将来追加する場合，target 層を新設するだけで chip 層は再利用可 | ユーザ指定 |
| (F) | **シリアル (ログ出力) は SCI7 (Arduino D0/D1)**．EK-RA6M5 J24 ヘッダ Pin 0 = RX = P614，Pin 1 = TX = P613．115200bps．外付け USB-Serial 変換アダプタを使う想定．J-Link OB VCOM (SCI9) は使わない | ユーザ指定 |
| (G) | FSP は `target/<TARGET>/fsp/ra/fsp/` (rascc 生成; gitignore)．Smart Configurator 生成 (`ra_cfg/` / `ra_gen/`) も target 層配下 (gitignore) | (A) の帰結 |

### 0-4. Phase 2 で **確定すべき** 未決事項 (本ファイル§設計判断 を参照)

- **vector_data.c 取扱**: (a) 抽出 → (b) リネーム → (c) リンカ廃棄 の順に試し，最初に通った方式を採用．
- **`hardware_init_hook` 実装**: (α) FSP SystemInit を BSS 後に呼ぶ — を第一候補．(β) は最後の手段．

### 0-5. codex Phase 1 レビュー結果

`d3bd62b` で全文書反映済．特に重要な指摘 (Phase 2 実装で踏まないよう):

1. **`start.S` は `SystemInit()` を直接呼ばない**．`hardware_init_hook` (BSS 前) と `software_init_hook` (BSS 後) の弱定義シンボルを呼ぶ．target 層が override する．
2. **FSP `SystemInit()` は BSS 領域変数を触る** (`bsp_init_uninitialized_vars()` 等)．`hardware_init_hook` から呼ぶと未定義動作．`target_hardware_initialize()` (BSS 後) から呼ぶこと．
3. **`vector_data.c` を全除外すると `g_interrupt_event_link_select[]` (IELSR テーブル) も失う**．`bsp_irq.c:39` の弱定義 (全 0) にフォールバックして実 IELSR が設定されない．
4. **`BSP_MCU_GROUP_RA6M5` `BSP_MCU_R7FA6M5BH` は `bsp_cfg.h` (target 層) で定義**．`Makefile.chip` の `-D` には書かない．
5. **`bsp_linker.c` (Option Setting Memory) は Phase 3 で `KERNEL_COBJS` に追加**．Phase 2 では未対応で良い．

### 0-6. Phase 2 の最初に取るアクション

1. **(ユーザ手作業必須・初回のみ)** Smart Configurator GUI で `configuration.xml`
   を作成し `target/ek_ra6m5_llvm/fsp/configuration.xml` にコミット．
   詳細は §B 参照．Renesas は CLI でのプロジェクト初期化を提供して
   おらず，このステップだけは Claude が代行できない．
2. **(以後 Claude 実行可)** `configuration.xml` がコミット済になったら，
   Claude に「Phase 2-A §B 完了，§C 以降を引き継いで」と依頼．Claude は
   Bash で `rascc.exe --generate ... target/ek_ra6m5_llvm/fsp/configuration.xml`
   を実行し `fsp/ra/` `fsp/ra_cfg/` `fsp/ra_gen/` を生成 (gitignore 済) →
   Read で `vector_data.c` から INTNO を抽出 → Edit で
   `target_serial.{h,arxml}` `target_hw_counter.{h,arxml}` の暫定値を
   実値に置換 → そのまま Phase 3 (`obj/obj_ek_ra6m5/Makefile` 作成 +
   初回ビルド) に進む．

### 0-7. 制約・運用ルール

- **共通プロセッサ依存部 `arch/arm_m_gcc/common/` は変更禁止** (CLAUDE.md 開発項目)．LLVM ビルドでも同じソースを vpath で再利用．
- **コンパイラは ARM LLVM (ATfE 21.1.1)** だけを使う．GCC は H5 移植用にのみ残す．
- 再度 codex レビューを依頼する場合は `Agent` (subagent_type=`codex:codex-rescue`) を使う．本セッションのレビュー結果は本ブランチ commit `d3bd62b` のメッセージにサマリあり．
- **`configuration.xml` の初回作成は Smart Configurator GUI 必須** (人間しかできない)．**ただし `rascc --generate` (= `ra/`/`ra_cfg/`/`ra_gen/` 生成) は Claude も Bash で実行可**．Phase 2-A §B (GUI) のみがユーザ手作業必須で，§C 以降は Claude に引き継げる．`docs/fsp_setup.md` 参照．
- Windows make の高並列度問題があるため `-j` は `4` 以下を推奨．
- コミットメッセージは日本語．`<area>: <要約>` 形式 (例: `target/ek_ra6m5_llvm: r7fa6m5bh.ld 追加`)．
- 共著者末尾は `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`．

---

## Phase 2-A — `configuration.xml` 取得 + FSP ローカル生成

> **本節は §B のみがユーザ手作業必須．§C 以降は Claude Code が
> Bash/Read/Edit で自動実行できる**．以下が役割分担:
>
> - **§B (ユーザ手作業必須)**: Smart Configurator GUI で `configuration.xml`
>   を 1 回作成し `target/ek_ra6m5_llvm/fsp/configuration.xml` にコミット．
>   Renesas は CLI でのプロジェクト初期化を提供しておらず，不完全な
>   `configuration.xml` を `rascc --generate` に渡しても
>   `Cannot invoke "...IPath.append(String)"` エラーで失敗する．
>   **生涯一度のみの作業**．
> - **§C 以降 (Claude が実行可能)**: `rascc --generate` は単なる CLI なので
>   Bash 経由で起動可能．生成物の検証・INTNO 抽出・暫定値置換・
>   `Makefile.target` 修正・vector_data.c 取扱方式の確定 (ビルド試行) も
>   全て Claude が完結できる．`configuration.xml` がコミット済になったら
>   Claude にブリーフして引き継がせること．
>
> 現状 `target/ek_ra6m5_llvm/fsp/configuration.xml` は **未コミット**．
> Phase 2-A の最初の作業 (§B) はユーザがこれを作成・取得すること．

### A. 前提状態の確認

実施前に以下を確認:

- [ ] ブランチ `feat/ek_ra6m5_phase1` 上にいる
- [ ] `target/ek_ra6m5_llvm/` 一式が存在 (Phase 2-B 骨格 commit `9c7561e`)
- [ ] FSP 6.4.0 (Smart Configurator sc_v2025-12) が
      `C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/` にインストール済み，もしくは
      e² studio v2025-12 (`C:/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/`)
      がインストール済み

### B. Smart Configurator GUI で `configuration.xml` 作成 〔ユーザ手作業必須・初回のみ〕

GUI を **どちらか好きな方** で起動する:

- **B-1 (推奨・軽量)**: `rasc.exe` standalone
  - 実行ファイル: `C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rasc.exe`
- **B-2**: e² studio v2025-12 経由
  - メニュー: `File → New → C/C++ Project → Renesas RA C/C++ Project`

設定値:

1. **新規プロジェクト ウィザード**:
   - Project Name: `ek_ra6m5_baseline` (任意．**`configuration.xml` 生成元としてのみ使用**)
   - Board: **EK-RA6M5**
   - Toolchain: **LLVM Embedded Toolchain for Arm (ATfE)** (本ポートは ARM LLVM)．
     なお Toolchain はあくまで configuration.xml 内のメタ情報．rascc が後で
     `--compiler LLVMARM` で再生成するので暫定で OK．GCC でも可．
   - Device: **R7FA6M5BH3CFC**
   - Project Type: **Flat (Non-TrustZone) Project**
   - RTOS: **No RTOS**
2. **`configuration.xml` を開いて構成**:
   - **Clocks**: HOCO 20MHz → PLL → ICLK 200MHz, PCLKD = ICLK/2 = 100MHz
   - **Stacks → New Stack → Driver → Connectivity → r_sci_uart**: **SCI7** を選択
   - **Stacks → New Stack → Driver → Timers → r_gpt**: GPT320 (32-bit, Free Run)
   - **Stacks → New Stack → Driver → Timers → r_gpt**: GPT321 (32-bit, One-Shot)
   - **Stacks → New Stack → Driver → Input → r_ioport**: デフォルト
   - **Pins**: P614 = RXD7 (Arduino D0 / Pin 0), P613 = TXD7 (Arduino D1 / Pin 1) を AF (SCI7) に設定
3. **Generate Project Content** をクリック．
4. 生成プロジェクト直下の **`configuration.xml` のみを** 本リポジトリにコピー:
   - `<ws>/ek_ra6m5_baseline/configuration.xml` → `target/ek_ra6m5_llvm/fsp/configuration.xml`
   - **`ra/` `ra_cfg/` `ra_gen/` はコピーしない** (gitignore 対象)．
5. `git add target/ek_ra6m5_llvm/fsp/configuration.xml` してコミット．推奨メッセージ:
   ```
   target/ek_ra6m5_llvm: configuration.xml 追加 (Smart Configurator baseline)

   FSP 6.4.0 (sc_v2025-12) 用．Board=EK-RA6M5, R7FA6M5BH3CFC,
   ICLK=200MHz, SCI7+GPT320+GPT321+IOPORT, Flat Non-TrustZone．
   ```
6. ユーザは Claude に「Phase 2-A §B 完了．§C 以降を引き継いで」と依頼．
   §I のブリーフテンプレートを使うと過不足ない引継ぎになる．

### C. `rascc --generate` で `ra/` `ra_cfg/` `ra_gen/` を生成 〔Claude 実行可〕

`configuration.xml` がコミットされた後，Claude が Bash 経由で実行:

```sh
"C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rascc.exe" \
    --generate \
    --device R7FA6M5BH3CFC \
    --compiler LLVMARM \
    target/ek_ra6m5_llvm/fsp/configuration.xml
```

実行後 `target/ek_ra6m5_llvm/fsp/` 配下に `ra/` `ra_cfg/` `ra_gen/` が新規作成．
これらは `.gitignore` で除外されているため commit されない．

成功条件:
- exit code = 0
- `target/ek_ra6m5_llvm/fsp/ra/fsp/inc/fsp_version.h` が生成される
- `target/ek_ra6m5_llvm/fsp/ra_cfg/fsp_cfg/bsp/bsp_cfg.h` が生成される
- `target/ek_ra6m5_llvm/fsp/ra_gen/vector_data.c` が生成される

詳細は [`arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md`](arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md) を参照．

### D. 検証 〔Claude 実行可〕

Claude は Read / Grep / Bash で確認:

- [ ] `target/ek_ra6m5_llvm/fsp/configuration.xml` が commit されている
- [ ] `target/ek_ra6m5_llvm/fsp/ra_cfg/fsp_cfg/bsp/bsp_cfg.h` が存在．内部に `BSP_MCU_GROUP_RA6M5` `BSP_MCU_R7FA6M5BH` の `#define`
- [ ] `target/ek_ra6m5_llvm/fsp/ra_gen/vector_data.c` が存在．`g_interrupt_event_link_select[]` あり
- [ ] `target/ek_ra6m5_llvm/fsp/ra/fsp/inc/fsp_version.h` が `FSP_VERSION_MAJOR (6U)` `FSP_VERSION_MINOR (4U)` を定義
- [ ] `git status target/ek_ra6m5_llvm/fsp/` で `ra/` `ra_cfg/` `ra_gen/` が **untracked にもならない** (gitignore 効果)

### E. INTNO スロット番号の読取り 〔Claude 実行可〕

`target/ek_ra6m5_llvm/fsp/ra_gen/vector_data.c` を Read /
Grep で開き，`g_interrupt_event_link_select[]` 配列のインデックスから
INTNO を導出:

| FSP イベント名 | 配列インデックス N | 対応 INTNO (= N + 16) |
|---|---|---|
| `BSP_PRV_VECTOR_EVENT_SCI7_RXI` | (§C 実行後に確定) | (確定) |
| `BSP_PRV_VECTOR_EVENT_GPT321_OVF` または相当 | (§C 実行後に確定) | (確定) |

### F. ターゲット依存ソースへの INTNO 反映 〔Claude 実行可〕

`configuration.xml` がコミットされ §C `rascc --generate` が実行済みに
なったら，Claude が Edit で下記を反映:

1. `target/ek_ra6m5_llvm/target_serial.h` の `INTNO_SIO` 暫定値を実値に．
2. `target/ek_ra6m5_llvm/target_serial.arxml` の `OsIsrInterruptNumber` を実値に．
3. `target/ek_ra6m5_llvm/target_hw_counter.h` `GPT321_INTNO` を実値に．
4. `target/ek_ra6m5_llvm/target_hw_counter.arxml` の `OsIsrInterruptNumber` を実値に．
5. `vector_data.c` 取扱方式を (a)/(b)/(c) から確定．Claude が試行順
   ((a) → (b) → (c)) でビルド試行 (Phase 3 着手後)．

### G. リスクと事前回避

| 症状 | 原因 | 回避策 |
|---|---|---|
| `rascc --generate` が「configuration.xml メタデータ不足」エラー | 不完全な XML | 必ず GUI で 1 回開き直して保存 |
| EK-RA6M5 で Arduino D0/D1 (P614/P613) が SCI7 でない | ボード Rev 違い | ボード silkscreen と [EK-RA6M5 User's Manual](https://www.renesas.com/en/document/mat/ek-ra6m5-v1-users-manual) を確認 |
| Smart Configurator が `BSP_MCU_GROUP_RA6M5` を定義しない | Board 選択漏れ | プロジェクト再生成．`bsp_cfg.h` を grep |
| `BSP_TZ_NONSECURE_BUILD` が定義されている | TrustZone を選んだ | **Flat (Non-TrustZone)** で再生成 |

### H. 次セッションで Claude に渡すブリーフ (テンプレート)

```
Phase 2-A 完了．configuration.xml は commit ___ で追加済み．
ローカルで `rascc --generate target/ek_ra6m5_llvm/fsp/configuration.xml` 実行済み．
target/ek_ra6m5_llvm/fsp/ra_gen/vector_data.c から読取った INTNO:
- SCI7_RXI       : N=___ → INTNO=___
- GPT321_OVF 相当: N=___ → INTNO=___
これで Phase 2-B 残作業 (INTNO 反映 + vector_data.c 取扱確定) と Phase 3 を進めてほしい．
```

---

## 目的

EK-RA6M5 ボード固有のターゲット依存部 `target/ek_ra6m5_llvm/` を新規作成し，Phase 1 のチップ依存部と組合せてビルド可能な状態にする．Smart Configurator 生成物 (`ra_cfg/`, `ra_gen/`) の取り込みも本フェーズで完結させる．

## 前提

- Phase 1 完了 (チップ依存部 `arch/arm_m_llvm/ra_fsp/` がコミット済み，codex レビュー済み)．
- ユーザが e² studio Smart Configurator を 1 度起動して下記構成のプロジェクトを生成できる:
  - Board: EK-RA6M5
  - Toolchain: ARM LLVM (ATfE) — configuration.xml 内のメタ情報．`rascc --compiler LLVMARM` で再生成するため初回は GCC でも可
  - Clock: ICLK 200 MHz
  - Stacks: ATK2 が後から再構成するので最小値でよい
  - Pin Configuration: SCI7 UART (P614 = RXD7 / Arduino D0, P613 = TXD7 / Arduino D1) を有効化
  - Modules: r_ioport, r_sci_uart, r_gpt × 2 (32-bit free-run + one-shot)

## 設計判断

- 既存 `target/nucleo_h563zi_gcc/` の構成を最大限踏襲する．差分は MCU 固有部分 (リンカスクリプト，ペリフェラル，割込み番号定義) のみ．
- **シリアル**: SCI7 を使用．EK-RA6M5 の Arduino-UNO 互換ヘッダ J24 の Pin 0 (RX = P614 = RXD7) / Pin 1 (TX = P613 = TXD7) に接続．115200bps, 8N1, ISR 駆動 RX．外付け USB-Serial 変換アダプタを J24 に接続して使う想定．J-Link OB VCOM (= SCI9) は使用しない．H5 と同様にレジスタ直叩きを基本とし，FSP `r_sci_uart` は使わない (Phase 4 で評価し，FSP に切替えても可)．
- **HW カウンタ**: GPT320 (32-bit) をフリーランニング 1 MHz (PCLKD=100MHz / 100)，GPT321 をワンショットアラーム 1 MHz．H5 の TIM2/TIM5 と同役割．
- **割込み優先度**: Cortex-M33 (4-bit, STM32H5xx と同じ): `tmin_basepri = 0x10`，GPT321 INTPRI=1，SCI7 RXI INTPRI=2，PendSV=0xFF，SVCall=0xE0．
- **ICU IELSR マッピング**: FSP 生成 `g_interrupt_event_link_select` (in `vector_data.c`) を `target_initialize()` で参照し，`target_serial.arxml` `target_hw_counter.arxml` の INTNO と一致させる．INTNO は FSP が決めた NVIC スロット (0〜95) をそのまま採用．
- **`vector_data.c` の取扱 (重要)**: FSP 生成 `vector_data.c` には `g_vector_table[]` (ATK2 と衝突) と `g_interrupt_event_link_select[]` (必須) が同居する．**ファイルごと除外すると IELSR テーブルも失う**ため，下記いずれかの方式を採る:
  - **(a) 抽出**: Smart Configurator 生成の `vector_data.c` から `g_interrupt_event_link_select[]` 部分だけを `target_irq_data.c` に転記，`vector_data.c` は除外．Smart Configurator 再生成時は手動で再抽出．
  - **(b) リネーム**: `vector_data.o` をビルド後に `llvm-objcopy --redefine-sym g_vector_table=fsp_g_vector_table_unused` で衝突回避．Smart Configurator 再生成に強い．
  - **(c) リンカ廃棄**: リンカスクリプトの `/DISCARD/` で FSP `g_vector_table[]` を破棄．
  Phase 2 で (a)→(b)→(c) の順に検証し，最初に通ったものを採用する．
- **`hardware_init_hook` の実装 (重要)**: `arch/arm_m_gcc/common/start.S` は `bl hardware_init_hook` を **BSS 初期化「前」** に呼ぶ．FSP `SystemInit()` は内部で `bsp_init_uninitialized_vars()` 等 BSS 領域へのアクセスを行うため **`hardware_init_hook` から呼んではいけない**．Phase 2 で下記のいずれかを採る:
  - **(α) FSP SystemInit を BSS 後に呼ぶ**: `hardware_init_hook` は空 (FPU CPACR 設定のみ等の最小処理)．`target_hardware_initialize()` (BSS 後; StartOS 経由) で `SystemInit()` を呼ぶ．**第一候補**．
  - **(β) target 専用 SystemInit に置換**: FSP 同梱 `system.c` を `KERNEL_COBJS` から外し，target 層で薄い `SystemInit()` (FPU enable + VTOR 設定 + `bsp_clock_init` の最小ラッパ) を再定義．制御は完全に握れるが FSP の WarmStart フックを失う．
  - **(γ) start.S 改造案は禁止**: 共通プロセッサ依存部は変更しない方針 (CLAUDE.md 開発項目)．

## 成果物

```
target/ek_ra6m5_llvm/
├── README.md                  ボード固有解説 (NUCLEO-H563ZI 版に倣う)
├── Makefile.target            FPU_USAGE / リンカ指定 / chip include
├── r7fa6m5bh.ld               リンカスクリプト (FSP 雛形を派生)
├── ek_ra6m5.h                 CPU_CLOCK_HZ, LED ピン, SCI7 ピン定数
├── target_kernel.h            TMIN_INTNO=16, TMAX_INTNO=111, TBITW_IPRI=4 等
├── target_config.c / .h       初期化 (R_BSP_WarmStart 連携 + IELSR 設定 + SCI7 ISR テーブル)
├── target_serial.h / .arxml   sysmod/serial.c 用 + ATK2 cfg 定義
├── target_hw_counter.c / .h / .arxml  GPT320/GPT321 ドライバ + ATK2 cfg
├── target_sysmod.h            システムモジュール用ヘッダ
├── target_test.h              テスト用ヘッダ
├── target_cfg1_out.h          cfg1_out リンク用スタブ
├── target_rename.h / target_unrename.h
├── target.tf                  pass2 ターゲット依存テンプレート
├── target_check.tf            pass3 チェック用テンプレート
├── target_offset.tf           offset.h 生成用テンプレート
└── fsp/                       Renesas FSP 関連 (本サブツリーに集約)
    ├── configuration.xml      Smart Configurator のソース (committed; 真値)
    ├── ra/                    rascc --generate 生成 (gitignored)
    │   └── fsp/               FSP 本体 (inc/, src/bsp/, src/r_*/)
    ├── ra_cfg/                rascc --generate 生成 (gitignored)
    │   └── fsp_cfg/           bsp_cfg.h, bsp_clock_cfg.h, bsp_module_irq_cfg.h
    └── ra_gen/                rascc --generate 生成 (gitignored)
        ├── common_data.{c,h}  hal モジュール初期化テーブル
        ├── hal_data.{c,h}     FSP モジュールインスタンス定義
        ├── pin_data.c         ピン構成 (R_IOPORT_Open に渡される)
        └── vector_data.{c,h}  ベクタテーブル + IELSR マッピング (※ vector_data.c は
                               ビルド対象外．IELSR テーブルだけ参照する)
```

## 実施手順

### Phase 2-A: configuration.xml + ローカル FSP 取得

→ 上記「ユーザー作業 (Phase 2-A)」 §A〜§D を参照．要点:

1. ユーザが GUI (rasc.exe または e² studio) で `configuration.xml` を作成．
   Board=EK-RA6M5, **SCI7** (Arduino D0/D1) + GPT320 + GPT321 + IOPORT．
2. `target/ek_ra6m5_llvm/fsp/configuration.xml` のみコミット．`ra/` `ra_cfg/`
   `ra_gen/` は gitignore．
3. `rascc.exe --generate target/ek_ra6m5_llvm/fsp/configuration.xml --compiler LLVMARM
   --device R7FA6M5BH3CFC` でローカル生成．
4. `target/ek_ra6m5_llvm/fsp/ra_gen/vector_data.c` から SCI7_RXI / GPT321_OVF の
   NVIC スロット番号を読取．

### Phase 2-B: ターゲット依存部一式の作成

1. `target/nucleo_h563zi_gcc/` 全体を `target/ek_ra6m5_llvm/` に複製．
2. **リンカスクリプト** `r7fa6m5bh.ld`: FSP 生成の `fsp.ld` をベースに，ATK2 流儀のセクション (`STARTUP(start.o)`, `_estack`, `__StackTop`, `__StackLimit`, `__data_start__/__data_end__`, `__bss_start__/__bss_end__`) を追加．Flash=2MB@`0x00000000`, SRAM=512KB@`0x20000000`．
3. **ボード資源** `ek_ra6m5.h`: `CPU_CLOCK_HZ=200000000`，LED1=P006, LED2=P004, LED3=P008，User Button=P009 (EK-RA6M5 仕様確認)．
4. **シリアル**: `target_config.c` の H5 USART3 部分を SCI7 に置換．`target_serial.h` の `INTNO_SIO` を `g_interrupt_event_link_select` の SCI7_RXI スロット番号に．
5. **HW カウンタ**: `target_hw_counter.c/h` の TIM2/TIM5 部分を GPT320/GPT321 に置換．`target_hw_counter.arxml` の `INTNO` を GPT321_OVF (またはアラームに使う事象) のスロット番号に．
6. **target_kernel.h**:
   - `TARGET_MIN_STKSZ=256`, `MINIMUM_OSTKSZ=512`, `DEFAULT_TASKSTKSZ=1024`, `DEFAULT_ISRSTKSZ=1024`, `DEFAULT_HOOKSTKSZ=1024`, `DEFAULT_OSSTKSZ=8192`
   - `TBITW_IPRI=4`
   - `TMIN_INTNO=16` (Cortex-M33 IRQ0 = 例外番号 16)
   - `TMAX_INTNO=16+96-1=111` (RA6M5 NVIC は 96 スロット)．要確認
7. **Makefile.target**:
   - `FPU_USAGE = FPU_LAZYSTACKING`
   - `INIT_MSP` 定義
   - `LDSCRIPT = $(TARGETDIR)/r7fa6m5bh.ld`
   - `INCLUDES += -I$(TARGETDIR)/fsp/ra_cfg/fsp_cfg -I$(TARGETDIR)/fsp/ra_cfg/fsp_cfg/bsp -I$(TARGETDIR)/fsp/ra_gen`
   - `KERNEL_DIR += $(TARGETDIR)/fsp/ra_gen`
   - `KERNEL_COBJS += target_config.o target_hw_counter.o common_data.o hal_data.o pin_data.o`
   - **`vector_data.o` は意図的に除外** (cfg 生成のベクタテーブルと衝突するため)
   - 必要に応じて `r_ioport.o`, `r_sci_uart.o`, `r_gpt.o` を追加 (FSP ドライバを使う場合)
   - `include $(SRCDIR)/arch/arm_m_llvm/ra_fsp/Makefile.chip`
8. **cfg テンプレート**: `target.tf`, `target_check.tf`, `target_offset.tf` を H5 から複製．ターゲット固有 ISR 検証ロジックは Phase 3 ビルド時に必要に応じて差替え．
9. **target_config.c の追加実装**:
   - **`hardware_init_hook()`**: 空 もしくは FPU CPACR enable 等 BSS 非依存処理のみ．**FSP `SystemInit()` は呼ばない** (BSS 前のため)．
   - **`target_hardware_initialize()`**: BSS 後．下記順序で初期化:
     1. `SystemInit()` (FSP `system.c`) を呼ぶ ＝ クロック初期化 + VTOR 仮設定 + R_BSP_WarmStart 一連
     2. `R_IOPORT_Open(&g_ioport_ctrl, &g_bsp_pin_cfg)` (`pin_data.c` のテーブルを使用)
     3. SCI7 の low-level 初期化 (レジスタ直叩き or `R_SCI_UART_Open`)
     4. `prc_hardware_initialize()` (ATK2 共通)
   - **`target_initialize()`** (StartOS から呼出，`target_hardware_initialize()` の後):
     1. ICU.IELSR 設定: `for (i=0; i<n; i++) R_ICU->IELSR[i] = (uint32_t)g_interrupt_event_link_select[i]`
     2. `prc_initialize()` (ATK2 共通; VTOR を ATK2 ベクタへ書換 + PendSV/SVC 優先度設定)
   - VTOR の確定書込みは `prc_initialize()` で行うため，FSP `SystemInit()` 内の VTOR 書込みは後で上書きされる (順序依存; 必ず `target_hardware_initialize` → `target_initialize` の順を守る)．
10. **README.md**: NUCLEO-H563ZI README に倣い，ボード資源・GPIO・ペリフェラル割当・優先度を記述．

## 検証 / 終了条件

- [ ] `target/ek_ra6m5_llvm/` が完成しコミット．
- [ ] `obj/obj_ek_ra6m5/Makefile` (Phase 3 で作成予定) と組み合わせて pass1 の `cfg1_out.c` 生成までが通る．
- [ ] BSP/FSP コードがエラーなくコンパイルされる (`bsp_clocks.o` 等の生成成功)．
- [ ] リンクは Phase 3 で完了させる．

## リスク

| 項目 | 内容 | 緩和策 |
|---|---|---|
| Smart Configurator 出力の `vector_data.c` を除外しても，`vector_data.h` の `BSP_VECTOR_TABLE_MAX_ENTRIES` 等の定数が他で参照される | ヘッダだけ残しソースを除外する形で大半は解決．残ればヘッダから一部抜粋 | Phase 3 ビルド時に判明 |
| `g_interrupt_event_link_select` シンボルが `bsp_irq.c:39` の弱定義 (全 0) にフォールバックして IELSR が空になる | 上記「設計判断」(a)/(b)/(c) のいずれかで FSP 生成テーブルを必ず compile・link する | Phase 2-B step 9 検証で `R_ICU->IELSR[N]` が 0 でないこと確認 |
| FSP `SystemInit()` を BSS 前に呼んで未定義動作 | `hardware_init_hook` を空にし，`target_hardware_initialize()` (BSS 後) で `SystemInit()` を呼ぶ | Phase 2-B step 9 |
| EK-RA6M5 の VCOM が SCI7 でない可能性 (ボード Rev 違い) | ユーザーズマニュアルで配線確認．異なれば適切な SCI に変更 | Phase 2-B step 4 |
| `TMAX_INTNO` の値が 96 で正しくない (RA6M5 の実 NVIC スロット数と一致しない) | `R7FA6M5BH.h` の `IRQn_Type` 定義から最大値を導出 | Phase 2-B step 6 |
| FSP `pin_data.c` が `R_IOPORT_Open` 呼出を要求する (どこから呼ぶ?) | `target_hardware_initialize()` で `R_IOPORT_Open(&g_ioport_ctrl, &g_bsp_pin_cfg)` を実行 | Phase 2-B step 9 |
| `BSP_MCU_GROUP_RA6M5` `BSP_MCU_R7FA6M5BH` が定義されない | これらは `bsp_cfg.h` (Smart Configurator 生成; target 層) で定義．chip 層 `Makefile.chip` の `-D` には含めない | Phase 2-A の bsp_cfg.h 内容を確認 |

## 後続フェーズへの引継

- Phase 3 が `obj/obj_ek_ra6m5/Makefile` を作成し，本層+チップ層+カーネルを統合してリンク可能状態にする．
- `configuration.xml` をコミットすることで，Smart Configurator 再起動時に同じ baseline を再生成できる．FSP バージョン更新時はこのファイルを基点に regen．

---

## 進捗記録 (Phase 2-B 骨格)

### 完了 (2026-04-29)

- `target/ek_ra6m5_llvm/` 一式を新規作成．`target/nucleo_h563zi_gcc/` 構造を踏襲．
- 主要ファイル:
  - `Makefile.target` (FPU_LAZYSTACKING, ra_cfg/ra_gen 検索パス, KERNEL_COBJS から vector_data.o 除外)
  - `r7fa6m5bh.ld` (Flash 2MB@0x00000000, SRAM 512KB@0x20000000．`/DISCARD/ : *(.fixed_vectors)` で FSP `__VECTOR_TABLE` を保険破棄)
  - `ek_ra6m5.h` (CPU_CLOCK_HZ=200M, PCLKD_HZ=100M, P006/P004/P008 LED 定義)
  - `target_kernel.h` (スタックサイズ等．TMIN_INTNO/TMAX_INTNO/TBITW_IPRI は `arch/arm_m_gcc/common/prc_config.h` の値を流用)
  - `target_config.c` (起動経路 §設計判断 (α): `hardware_init_hook` 空，`target_hardware_initialize` で SystemInit + IOPORT + SCI7 + prc_hw_init)
  - `target_serial.c/h` ＋ `target_serial.arxml` (SCI7 RX 割込み，INTNO 暫定 16)
  - `target_hw_counter.c/h` ＋ `target_hw_counter.arxml` (GPT320 free-run + GPT321 one-shot．INTNO 暫定 18)
  - `target_sysmod.h` `target_test.h` `target_cfg1_out.h` `target_rename.h` `target_unrename.h`
  - `target.tf` `target_check.tf` `target_offset.tf` (H5 同様 prc.tf を include するだけの薄い派生)
  - `ra_cfg/` `ra_gen/` は **commit しない**．clone 後ユーザが `rascc --generate` で生成する (gitignore 対象)
  - `README.md` (ボード構成・GPIO・優先度・Phase 2-A 操作手順)

### 設計判断の確定状況

| 項目 | phase2.md §設計判断 候補 | 採用 | 備考 |
|---|---|---|---|
| `vector_data.c` 取扱 | (a) 抽出 / (b) リネーム / (c) リンカ廃棄 | **未確定** | `Makefile.target` は (a) 仮定で `vector_data.o` を `KERNEL_COBJS` から除外．Phase 2-A 完了後に最終決定．`r7fa6m5bh.ld` は (c) 用の `/DISCARD/` も併設 |
| `hardware_init_hook` 実装 | (α) FSP SystemInit を BSS 後に呼ぶ / (β) target 専用 SystemInit | **(α) 採用** | `hardware_init_hook` は空，`target_hardware_initialize` で `SystemInit()` を呼ぶ |

### Phase 2-A (ユーザ作業) 待ち項目

以下は `ra_cfg/` `ra_gen/` `configuration.xml` の Smart Configurator 出力受領後に確定:

- `target_serial.h` `INTNO_SIO` の実値 (`g_interrupt_event_link_select[]` の SCI7_RXI スロット番号 + 16)
- `target_serial.arxml` の `OsIsrInterruptNumber` `<VALUE>16</VALUE>` 部
- `target_hw_counter.h` `GPT321_INTNO` の実値 (GPT321_OVF スロット番号 + 16)
- `target_hw_counter.arxml` の `OsIsrInterruptNumber` `<VALUE>18</VALUE>` 部
- `target_config.c` の `EK_RA6M5_HAVE_VECTOR_DATA` 有効化判断 (Makefile.target で `-DEK_RA6M5_HAVE_VECTOR_DATA` を付与)
- `target_config.c` の `EK_RA6M5_USE_FSP_PINCFG` 有効化 (Smart Configurator 生成 `pin_data.c` の `g_bsp_pin_cfg` を取込）
- `vector_data.c` 取扱方式 (a)/(b)/(c) の最終確定．それに応じて `Makefile.target` `KERNEL_COBJS` を更新

### 既知の検証ポイント (Phase 3 でビルド時に解消)

- IDE (clangd) は `kernel_impl.h` `bsp_api.h` を解決できないため `target_config.c` `target_hw_counter.c` に多数のエラーマーカが出る．これは IDE の INCLUDE 設定問題であり実ビルドでは解決される．
- SCI7 BRR=26 計算は PCLKB=100MHz 仮定．Smart Configurator の `bsp_clock_cfg.h` で PCLKB 値を確認し，必要なら更新．
- GPT のクロック源は PCLKD 直結 (`TPCS=DIV1`) 固定で TIMER_CLOCK_HZ=1MHz としているが，PCLKD=100MHz では実 100tick/us になる．Phase 4 で 1tick=1us 相当にする最終調整 (PCLKD 設定変更 or GTPR でのソフト分周) を決定．
- `bsp_linker.c` (Option Setting Memory) は Phase 3 で `KERNEL_COBJS` に追加判断．現状リンカスクリプトに `.option_setting_*` セクションを置いていない．
