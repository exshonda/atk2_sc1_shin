# Phase 2: ターゲット依存部の作成

## 新セッション着手手順 (Handoff)

> 本節は **後続セッション (別の Claude / 開発者) が Phase 2 を引き継ぐ際**
> の起点情報．Phase 1 までの全コンテキストをここに集約してある．以下を
> 上から順に確認すれば cold start でも進められる．

### 0-1. ブランチと commit 履歴

リポジトリ: `c:/home/proj/edge-ai/embcode/atk2_ra6m5/work/atk2_sc1_shin`
ブランチ: `feat/ek_ra6m5_phase1` (Phase 2 もこのブランチで継続．Phase 完了時に PR 化を検討)

main からの差分 commit:

| Commit | 内容 |
|---|---|
| `f0dfb10` | `CLAUDE.md`: リポジトリ概要 + EK-RA6M5 開発項目 (`/init` 由来) |
| `650f82e` | `arch/arm_m_gcc/ra6m5_fsp/`: FSP 6.1.0 同梱 + `Makefile.chip` + `chip_config.h` + README (377 ファイル，~133k 行) |
| `75dcc0a` | `phase1.md`〜`phase6.md`: 全 6 フェーズの計画 |
| `d3bd62b` | docs: codex Phase 1 レビュー指摘 (B-1/B-2/R-2/R-3/R-4) を文書に反映 |

### 0-2. 必読ファイル (この順)

1. `CLAUDE.md` — プロジェクト全体像・3-pass cfg ビルドフロー・層構造・H5 移植時の落とし穴．特に **「開発項目」** 節 (末尾) が本タスクのブリーフ．
2. `phase1.md` — Phase 1 の成果物と codex レビュー反映後のリスク表．
3. `arch/arm_m_gcc/ra6m5_fsp/README.md` — **`§6.1` 起動経路と `§6.3` `vector_data.c` 取扱を必ず読む**．Phase 2 の実装方針はここに集約済．
4. 本ファイル (`phase2.md`) 残りの節．
5. `arch/arm_m_gcc/stm32h5xx_stm32cube/{Makefile.chip,chip_config.h,README.md}` および `target/nucleo_h563zi_gcc/{Makefile.target,target_config.c,target_hw_counter.c,nucleo_h563zi.h,stm32h563zi.ld,README.md}` — H5 版を **そのまま踏襲する** ターゲット層の見本．
6. `arch/arm_m_gcc/common/{start.S,Makefile.prc,prc_config.{c,h},prc_support.S}` — **絶対に変更しない** 共通プロセッサ依存部．
7. `obj/obj_nucleo_h563zi/Makefile` — Phase 3 で複製する Makefile の見本．

### 0-3. Phase 1 で確定した設計判断 (再議論不要)

| ID | 判断 | 根拠 |
|---|---|---|
| (A) | FSP は Smart Configurator 出力をそのままコミット (vendoring) | ユーザ確認済 |
| (B) | ベクタテーブルは ATK2 cfg pass2 生成 (`Os_Lcfg.c`) を使う．FSP 生成 `g_vector_table[]` は除外 | ユーザ確認済 |
| (C) | `arch/arm_m_gcc/common/` は変更しない | CLAUDE.md 開発項目 |
| (D) | FSP は `arch/arm_m_gcc/ra6m5_fsp/fsp/` 配下に as-is で同梱．Smart Configurator 生成 (`ra_cfg/` / `ra_gen/`) は target 層配下 | Phase 1 README §3 |

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

1. **e² studio Smart Configurator** で baseline プロジェクト生成 (本ファイル §実施手順 Phase 2-A)．これは GUI 必須．Claude が代替できないため，**ユーザに依頼する作業**．
2. ユーザから生成物 (`ra_cfg/`, `ra_gen/`, `configuration.xml`) を受領．
3. `target/nucleo_h563zi_gcc/` を `target/ek_ra6m5_gcc/` に複製して Phase 2-B 着手．

### 0-7. 制約・運用ルール

- **共通プロセッサ依存部 `arch/arm_m_gcc/common/` は変更禁止** (CLAUDE.md 開発項目)．
- 再度 codex レビューを依頼する場合は `Agent` (subagent_type=`codex:codex-rescue`) を使う．本セッションのレビュー結果は本ブランチ commit `d3bd62b` のメッセージにサマリあり．
- Smart Configurator の **初回プロジェクト作成は GUI 必須** (人間しかできない)．ただし **2 回目以降の `ra_cfg/` `ra_gen/` 再生成は CLI で完全ヘッドレス化可能** (`rascc.exe --generate configuration.xml`)．§J 「rascc CLI による再生成」を参照．`rasc.exe` 本体は `C:/Users/honda/.renesas/platform/sc/ra/fsp_<ver>/eclipse/rasc.exe` に standalone で存在し，e² studio に依存せず単体起動できる．
- Windows make の高並列度問題があるため `-j` は `4` 以下を推奨．
- コミットメッセージは日本語．`<area>: <要約>` 形式 (例: `target/ek_ra6m5_gcc: r7fa6m5bh.ld 追加`)．
- 共著者末尾は `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`．

---

## ユーザー作業 (Phase 2-A) — Smart Configurator baseline 生成

> **本節はユーザーが手作業で実施する必須タスク**．Claude では代替不能
> (Smart Configurator の **初回**プロジェクト作成は GUI 必須．`rascc.exe`
> も完全な `configuration.xml` がないと動かないため，初回はどちらにせよ
> GUI が要る)．Phase 2-B 骨格 (commit `9c7561e`) は完了済み．本節を実施
> した後，Phase 3 またはセッション再開で Claude に「Phase 2-A 完了．
> 後続作業を継続」と依頼する．
>
> **注**: 一度 `configuration.xml` ＋ `ra_cfg/` ＋ `ra_gen/` を本リポジトリに
> コミットしてしまえば，**FSP バージョンアップやモジュール構成変更は
> §J の `rascc.exe --generate` 手順で完全ヘッドレス化可能**．本節 §B の
> GUI 操作は **生涯一度** で済む．

### A. 前提状態の確認

実施前に以下を確認 (どれも commit `9c7561e` 時点で満たされているはず):

- [ ] ブランチ `feat/ek_ra6m5_phase1` 上にいる
- [ ] `target/ek_ra6m5_gcc/` 一式が存在する
- [ ] `target/ek_ra6m5_gcc/ra_cfg/` `ra_gen/` は **README.md のみ**で，他に
      ファイルが無い (まだ Smart Configurator 出力を入れていない)

### B. Smart Configurator で baseline 生成

GUI を **どちらか好きな方** で起動する:

- **B-1 (推奨・軽量)**: `rasc.exe` standalone (FSP 単体配布 GUI．e² studio 不要)
  - 実行ファイル: `C:/Users/honda/.renesas/platform/sc/ra/fsp_6.1.0/eclipse/rasc.exe`
  - 起動: エクスプローラから `rasc.exe` をダブルクリック，または PowerShell:
    ```powershell
    & "C:/Users/honda/.renesas/platform/sc/ra/fsp_6.1.0/eclipse/rasc.exe"
    ```
  - メニュー: `File → New → FSP Project` で新規プロジェクト ウィザードが開く．
  - 出力先 IDE は **GCC + CMake** または **GCC + Makefile** を選択 (本リポジトリは ATK2 が独自に Makefile を持つので IDE 形式は最終的に使わない．`ra_cfg/` `ra_gen/` `configuration.xml` だけ取り出す)．
- **B-2**: e² studio (2025-07 以降) 経由
  - 既存ワークスペースとは **別の場所** に新規ワークスペースを作る．
  - メニュー: `File → New → C/C++ Project → Renesas RA C/C++ Project`．

設定値はどちらの GUI でも共通:

1. **新規プロジェクト ウィザード**:
   - Project Name: `ek_ra6m5_baseline` (任意．**生成元としてのみ使用**)
   - Board: **EK-RA6M5**
   - Toolchain: **GCC ARM Embedded**
   - Device: **R7FA6M5BH3CFC**
   - Project Type: **Flat (Non-TrustZone) Project**
   - RTOS: **No RTOS**
2. **`configuration.xml` を開いて構成**:
   - **Clocks**: HOCO 20MHz → PLL → ICLK 200MHz, PCLKD = ICLK/2 = 100MHz
   - **Stacks → New Stack → Driver → Connectivity → r_sci_uart**: `SCI9` を選択
   - **Stacks → New Stack → Driver → Timers → r_gpt**: `GPT320` (32-bit)，Mode=Free Run
   - **Stacks → New Stack → Driver → Timers → r_gpt**: `GPT321` (32-bit)，Mode=One-Shot
   - **Stacks → New Stack → Driver → Input → r_ioport**: デフォルト
   - **Pins**: `P602=TXD9`, `P603=RXD9` が AF6 (SCI9) に設定されていることを確認
   - **Properties** タブで各モジュールの Interrupt Priority を確認
3. **`Generate Project Content`** をクリック．
4. プロジェクトが一度ビルドできることを GUI 上で確認 (任意，整合性検証目的)．

### C. 生成物のコピー (本リポジトリへ取込)

生成プロジェクトのワークスペース直下から，下記 3 箇所を本リポジトリへコピー:

| 元 (e² studio ワークスペース内) | 先 (本リポジトリ) |
|---|---|
| `<ws>/ek_ra6m5_baseline/ra_cfg/`     全体 (再帰) | `target/ek_ra6m5_gcc/ra_cfg/`       (既存 `README.md` は残す) |
| `<ws>/ek_ra6m5_baseline/ra_gen/`     全体 (再帰) | `target/ek_ra6m5_gcc/ra_gen/`       (既存 `README.md` は残す) |
| `<ws>/ek_ra6m5_baseline/configuration.xml`        | `target/ek_ra6m5_gcc/configuration.xml` (新規) |

> **注意**: `script/fsp.ld` `src/` `inc/` `.cproject` 等は **コピーしない**．
> 本リポジトリは ATK2 が独自にリンカスクリプト・スタートアップを持つ
> ため．

### D. コピー結果の検証

下記が満たされていることを確認:

- [ ] `target/ek_ra6m5_gcc/ra_cfg/fsp_cfg/bsp/bsp_cfg.h` が存在し，
      内部に `#define BSP_MCU_GROUP_RA6M5` および `#define BSP_MCU_R7FA6M5BH`
      が含まれている (chip 層 `Makefile.chip` に `-D` を書かない方針の根拠)
- [ ] `target/ek_ra6m5_gcc/ra_cfg/fsp_cfg/bsp/bsp_clock_cfg.h` が存在
- [ ] `target/ek_ra6m5_gcc/ra_gen/common_data.c` `hal_data.c` `pin_data.c`
      `vector_data.c` `vector_data.h` が存在
- [ ] `target/ek_ra6m5_gcc/configuration.xml` が存在

### E. INTNO スロット番号の読取り

`target/ek_ra6m5_gcc/ra_gen/vector_data.c` を開き，
`g_interrupt_event_link_select[]` 配列の並び順から下記イベントの
スロット番号 (= 配列インデックス) を読み取る:

| FSP イベント名 | 配列インデックス N | 対応 INTNO (= N + 16) |
|---|---|---|
| `BSP_PRV_VECTOR_EVENT_SCI9_RXI` (受信割込み) | (記入) | (記入) |
| `BSP_PRV_VECTOR_EVENT_GPT321_OVF` または GPT321 周期割込み相当 | (記入) | (記入) |

> 配列の **0 番目** に `SCI9_RXI` があれば INTNO=16，**1 番目** なら 17 ...
> 通常 SCI9 のみ + GPT320 + GPT321 の構成では SCI9_RXI は 0〜2 のいずれか，
> GPT321_OVF はその次のスロットに割り当てられる．

### F. 後続作業 (Claude に依頼) — 引継メモ

以下の作業は Claude が引き継げる．Phase 3 着手時または別セッション開始
時に「Phase 2-A 完了．以下を反映して Phase 2-B を仕上げてほしい」と
INTNO 値を伝える．

下記 6 項目を Claude が更新する:

1. **`target/ek_ra6m5_gcc/target_serial.h`** の `INTNO_SIO`
   暫定値 `UINT_C(16)` → §E で確認した実値．
2. **`target/ek_ra6m5_gcc/target_serial.arxml`** の
   `RxHwSerialInt` の `OsIsrInterruptNumber` `<VALUE>16</VALUE>`
   → 実値．
3. **`target/ek_ra6m5_gcc/target_hw_counter.h`** の `GPT321_INTNO`
   暫定値 `UINT_C(18)` → 実値．
4. **`target/ek_ra6m5_gcc/target_hw_counter.arxml`** の
   `C2ISR_for_MAIN_HW_COUNTER` の `OsIsrInterruptNumber` `<VALUE>18</VALUE>`
   → 実値．
5. **`target/ek_ra6m5_gcc/Makefile.target`** に下記マクロ定義を追加:
   - `-DEK_RA6M5_HAVE_VECTOR_DATA` (target_config.c の IELSR 設定ループを有効化)
   - `-DEK_RA6M5_USE_FSP_PINCFG` (target_config.c の R_IOPORT_Open 呼出を有効化)
6. **`vector_data.c` 取扱方式**を (a)/(b)/(c) から確定．Claude が試行順
   ((a) → (b) → (c)) でビルドを試し，最初に通った方式を採用．対応する
   `Makefile.target` 修正 (例: 方式 (b) なら objcopy ルール追加，方式 (c)
   なら `r7fa6m5bh.ld` の `/DISCARD/` を本格化) を行う．

### G. コミット責務

- §C のコピー作業は **ユーザー** がコミットする (FSP ベンダ生成物のため)．
  推奨コミットメッセージ:
  ```
  target/ek_ra6m5_gcc: Smart Configurator baseline (FSP 6.1.0) 取込

  e² studio Smart Configurator で生成した ra_cfg/ ra_gen/
  configuration.xml を取込．構成: Board=EK-RA6M5, ICLK=200MHz,
  PCLKD=100MHz, SCI9 + GPT320 + GPT321 + IOPORT．
  ```
- §F の Claude 作業は別コミットとする (`target/ek_ra6m5_gcc:
  Phase 2-A 完了に伴う INTNO/Makefile 修正` 等)．

### H. リスクと事前回避

| 症状 | 原因 | 回避策 |
|---|---|---|
| 生成物コピー後に `ra_cfg/README.md` `ra_gen/README.md` を上書きしてしまう | コピー時に既存 README を見落とした | `cp` ではなくマージコピー (rsync `--ignore-existing` または手動マージ)．README.md を一旦リポジトリ外に退避 → コピー後に戻す，も可 |
| EK-RA6M5 のボード Rev 違いで VCOM が SCI9 ではない | EK-RA6M5 v1.0/v2.0 の差異 | ボード silkscreen と [Renesas EK-RA6M5 User's Manual](https://www.renesas.com/en/document/mat/ek-ra6m5-v1-users-manual) で配線確認．異なれば `target_serial.h` `target_config.c` で別 SCI に変更 |
| Smart Configurator が `BSP_MCU_GROUP_RA6M5` を定義しない | プロジェクトテンプレートで Board=EK-RA6M5 を選び忘れ | プロジェクト再生成．`bsp_cfg.h` を grep で確認 |
| 生成物に `BSP_TZ_NONSECURE_BUILD` が定義されている | TrustZone Secure/Non-Secure 分割を選択した | プロジェクトを **Flat (Non-TrustZone)** で再生成．本ポートは Non-Secure 単一前提 |

### I. 次セッションで Claude に渡すブリーフ (テンプレート)

```
Phase 2-A 完了．下記を反映して Phase 2-B を仕上げてほしい．
- vector_data.c の g_interrupt_event_link_select[] から読取った INTNO:
  - SCI9_RXI       : N=___ → INTNO=___
  - GPT321_OVF 相当: N=___ → INTNO=___
- ra_cfg/ ra_gen/ configuration.xml は commit ___ で取込済．
  vector_data.c 取扱方式は (a)/(b)/(c) のうち未確定．Claude にビルド
  試行で確定してもらいたい．
- 続けて Phase 3 (obj/obj_ek_ra6m5/Makefile 作成) に進んでほしい．
```

### J. rascc CLI による再生成 (2 回目以降ヘッドレス化)

**§A〜§G が完了し `configuration.xml` が本リポジトリにコミット済み** で
あれば，以後 `ra_cfg/` `ra_gen/` の **再生成は CLI のみで完結する**．
GUI 操作は不要．Claude が Bash 経由で実行することも可能．

#### J-1. 再生成コマンド

```sh
# Windows (msys2 bash, PowerShell, cmd 何でも可) — FSP 6.1.0 を使用
"C:/Users/honda/.renesas/platform/sc/ra/fsp_6.1.0/eclipse/rascc.exe" \
    --generate \
    --device R7FA6M5BH3CFC \
    --compiler GCC \
    target/ek_ra6m5_gcc/configuration.xml
```

`rascc.exe` は `configuration.xml` のあるディレクトリを起点に
`ra_cfg/` `ra_gen/` (および IDE 別ファイル群) を再生成する．`--projectdir`
オプションでターゲットディレクトリを明示指定することも可能．

#### J-2. ユースケース

| 場面 | 実行手順 |
|---|---|
| **FSP モジュール構成変更** (例: r_dtc を追加) | (1) GUI で `configuration.xml` を編集 → (2) `rascc --generate` で再生成 → (3) commit |
| **FSP バージョンアップ** (例: 6.1.0 → 6.2.0) | `rascc.exe` のパスを `fsp_6.2.0/...` に変更して同コマンド．configuration.xml は version 互換 (raConfiguration version 属性) なら無修正で OK |
| **CI でコミット内容が configuration.xml と ra_cfg/ra_gen で乖離していないかチェック** | CI 上で `rascc --generate` を実行し `git diff --exit-code ra_cfg/ ra_gen/` で検証 |
| **Claude による FSP モジュール変更の自動化** | Claude が configuration.xml を編集 → Bash で `rascc --generate` 実行 → 差分を確認 |

#### J-3. CLI 単体ではできないこと (要 GUI)

- **新規プロジェクトの初回作成**．`rascc --generate` は **完全な
  configuration.xml を要求** する．不完全な `configuration.xml` を渡すと
  下記のエラーで失敗する:
  ```
  Cannot invoke "org.eclipse.core.runtime.IPath.append(String)" because
  the return value of "...getVersionedCMSISZoneResourceLocation(...)" is null
  ```
  これは BSP/FSP version metadata や device pack のひも付けが GUI ウィザード
  でしか挿入されないため．`Renesas##BSP##Board##ra6m5_ek##*##configuration.xml`
  のようなテンプレート断片だけでは不足．
- **モジュールの細かな依存解決**．Stack 追加に伴う必要モジュールの自動追加，
  Pin 設定の自動展開などは GUI が便利 (XML 編集でも可だが手間)．

#### J-4. Claude が実行するときのチェックリスト

Claude が `rascc --generate` を実行した場合，以下を確認:

- [ ] exit code = 0
- [ ] `target/ek_ra6m5_gcc/ra_cfg/fsp_cfg/bsp/bsp_cfg.h` が再生成 (mtime 更新)
- [ ] `target/ek_ra6m5_gcc/ra_gen/vector_data.c` の
      `g_interrupt_event_link_select[]` の並びが変わっていれば INTNO を再確認
- [ ] `git diff target/ek_ra6m5_gcc/ra_cfg/ target/ek_ra6m5_gcc/ra_gen/` で
      想定外の差分がないことを確認

---

## 目的

EK-RA6M5 ボード固有のターゲット依存部 `target/ek_ra6m5_gcc/` を新規作成し，Phase 1 のチップ依存部と組合せてビルド可能な状態にする．Smart Configurator 生成物 (`ra_cfg/`, `ra_gen/`) の取り込みも本フェーズで完結させる．

## 前提

- Phase 1 完了 (チップ依存部 `arch/arm_m_gcc/ra6m5_fsp/` がコミット済み，codex レビュー済み)．
- ユーザが e² studio Smart Configurator を 1 度起動して下記構成のプロジェクトを生成できる:
  - Board: EK-RA6M5
  - Toolchain: GCC ARM Embedded
  - Clock: ICLK 200 MHz
  - Stacks: ATK2 が後から再構成するので最小値でよい
  - Pin Configuration: SCI9 UART (P602/P603) を有効化
  - Modules: r_ioport, r_sci_uart, r_gpt × 2 (32-bit free-run + one-shot)

## 設計判断

- 既存 `target/nucleo_h563zi_gcc/` の構成を最大限踏襲する．差分は MCU 固有部分 (リンカスクリプト，ペリフェラル，割込み番号定義) のみ．
- **シリアル**: SCI9 を使用．EK-RA6M5 は J-Link OB の VCOM が SCI9 (P602=TXD9, P603=RXD9) に接続．115200bps, 8N1, ISR 駆動 RX．H5 と同様にレジスタ直叩きを基本とし，FSP `r_sci_uart` は使わない (Phase 4 で評価し，FSP に切替えても可)．
- **HW カウンタ**: GPT320 (32-bit) をフリーランニング 1 MHz (PCLKD=100MHz / 100)，GPT321 をワンショットアラーム 1 MHz．H5 の TIM2/TIM5 と同役割．
- **割込み優先度**: Cortex-M33 (4-bit, STM32H5xx と同じ): `tmin_basepri = 0x10`，GPT321 INTPRI=1，SCI9 RXI INTPRI=2，PendSV=0xFF，SVCall=0xE0．
- **ICU IELSR マッピング**: FSP 生成 `g_interrupt_event_link_select` (in `vector_data.c`) を `target_initialize()` で参照し，`target_serial.arxml` `target_hw_counter.arxml` の INTNO と一致させる．INTNO は FSP が決めた NVIC スロット (0〜95) をそのまま採用．
- **`vector_data.c` の取扱 (重要)**: FSP 生成 `vector_data.c` には `g_vector_table[]` (ATK2 と衝突) と `g_interrupt_event_link_select[]` (必須) が同居する．**ファイルごと除外すると IELSR テーブルも失う**ため，下記いずれかの方式を採る:
  - **(a) 抽出**: Smart Configurator 生成の `vector_data.c` から `g_interrupt_event_link_select[]` 部分だけを `target_irq_data.c` に転記，`vector_data.c` は除外．Smart Configurator 再生成時は手動で再抽出．
  - **(b) リネーム**: `vector_data.o` をビルド後に `arm-none-eabi-objcopy --redefine-sym g_vector_table=fsp_g_vector_table_unused` で衝突回避．Smart Configurator 再生成に強い．
  - **(c) リンカ廃棄**: リンカスクリプトの `/DISCARD/` で FSP `g_vector_table[]` を破棄．
  Phase 2 で (a)→(b)→(c) の順に検証し，最初に通ったものを採用する．
- **`hardware_init_hook` の実装 (重要)**: `arch/arm_m_gcc/common/start.S` は `bl hardware_init_hook` を **BSS 初期化「前」** に呼ぶ．FSP `SystemInit()` は内部で `bsp_init_uninitialized_vars()` 等 BSS 領域へのアクセスを行うため **`hardware_init_hook` から呼んではいけない**．Phase 2 で下記のいずれかを採る:
  - **(α) FSP SystemInit を BSS 後に呼ぶ**: `hardware_init_hook` は空 (FPU CPACR 設定のみ等の最小処理)．`target_hardware_initialize()` (BSS 後; StartOS 経由) で `SystemInit()` を呼ぶ．**第一候補**．
  - **(β) target 専用 SystemInit に置換**: FSP 同梱 `system.c` を `KERNEL_COBJS` から外し，target 層で薄い `SystemInit()` (FPU enable + VTOR 設定 + `bsp_clock_init` の最小ラッパ) を再定義．制御は完全に握れるが FSP の WarmStart フックを失う．
  - **(γ) start.S 改造案は禁止**: 共通プロセッサ依存部は変更しない方針 (CLAUDE.md 開発項目)．

## 成果物

```
target/ek_ra6m5_gcc/
├── README.md                  ボード固有解説 (NUCLEO-H563ZI 版に倣う)
├── Makefile.target            FPU_USAGE / リンカ指定 / chip include
├── r7fa6m5bh.ld               リンカスクリプト (FSP 雛形を派生)
├── ek_ra6m5.h                 CPU_CLOCK_HZ, LED ピン, SCI9 ピン定数
├── target_kernel.h            TMIN_INTNO=16, TMAX_INTNO=111, TBITW_IPRI=4 等
├── target_config.c / .h       初期化 (R_BSP_WarmStart 連携 + IELSR 設定 + SCI9 ISR テーブル)
├── target_serial.h / .arxml   sysmod/serial.c 用 + ATK2 cfg 定義
├── target_hw_counter.c / .h / .arxml  GPT320/GPT321 ドライバ + ATK2 cfg
├── target_sysmod.h            システムモジュール用ヘッダ
├── target_test.h              テスト用ヘッダ
├── target_cfg1_out.h          cfg1_out リンク用スタブ
├── target_rename.h / target_unrename.h
├── target.tf                  pass2 ターゲット依存テンプレート
├── target_check.tf            pass3 チェック用テンプレート
├── target_offset.tf           offset.h 生成用テンプレート
├── ra_cfg/                    Smart Configurator 出力
│   └── fsp_cfg/               bsp_cfg.h, bsp_clock_cfg.h, bsp_module_irq_cfg.h ほか
└── ra_gen/                    Smart Configurator 出力
    ├── common_data.{c,h}      hal モジュール初期化テーブル
    ├── hal_data.{c,h}         FSP モジュールインスタンス定義
    ├── pin_data.c             ピン構成 (R_IOPORT_Open に渡される)
    ├── vector_data.{c,h}      ベクタテーブル + IELSR マッピング (※ vector_data.c は
    │                          ビルド対象外．IELSR テーブルだけ参照する)
    └── (configuration.xml は target/ek_ra6m5_gcc/ 直下に配置 - Smart Configurator
         のソース)
```

## 実施手順

### Phase 2-A: Smart Configurator で baseline 生成

1. e² studio を起動，新規プロジェクト作成: `File → New → C/C++ Project → Renesas RA C/C++ Project`．
2. Board: EK-RA6M5，Toolchain: GCC ARM Embedded，FSP: 6.1.0．
3. Stacks タブで `r_ioport` `r_sci_uart` `r_gpt` を追加．SCI9 を選択．GPT320, GPT321 を 1 MHz 設定．
4. Pin Configuration タブで P602=TXD9, P603=RXD9 を確認．
5. Generate Project Content をクリック．
6. 生成されたプロジェクトから下記のみコピー:
   - `ra_cfg/` 全体 → `target/ek_ra6m5_gcc/ra_cfg/`
   - `ra_gen/` 全体 → `target/ek_ra6m5_gcc/ra_gen/`
   - `configuration.xml` → `target/ek_ra6m5_gcc/configuration.xml` (Smart Configurator 再起動用)
7. 生成された `script/fsp.ld` は `r7fa6m5bh.ld` のベースとして取り込む (Phase 2-B で改造)．

### Phase 2-B: ターゲット依存部一式の作成

1. `target/nucleo_h563zi_gcc/` 全体を `target/ek_ra6m5_gcc/` に複製．
2. **リンカスクリプト** `r7fa6m5bh.ld`: FSP 生成の `fsp.ld` をベースに，ATK2 流儀のセクション (`STARTUP(start.o)`, `_estack`, `__StackTop`, `__StackLimit`, `__data_start__/__data_end__`, `__bss_start__/__bss_end__`) を追加．Flash=2MB@`0x00000000`, SRAM=512KB@`0x20000000`．
3. **ボード資源** `ek_ra6m5.h`: `CPU_CLOCK_HZ=200000000`，LED1=P006, LED2=P004, LED3=P008，User Button=P009 (EK-RA6M5 仕様確認)．
4. **シリアル**: `target_config.c` の H5 USART3 部分を SCI9 に置換．`target_serial.h` の `INTNO_SIO` を `g_interrupt_event_link_select` の SCI9_RXI スロット番号に．
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
   - `INCLUDES += -I$(TARGETDIR)/ra_cfg/fsp_cfg -I$(TARGETDIR)/ra_cfg/fsp_cfg/bsp -I$(TARGETDIR)/ra_gen`
   - `KERNEL_DIR += $(TARGETDIR)/ra_gen`
   - `KERNEL_COBJS += target_config.o target_hw_counter.o common_data.o hal_data.o pin_data.o`
   - **`vector_data.o` は意図的に除外** (cfg 生成のベクタテーブルと衝突するため)
   - 必要に応じて `r_ioport.o`, `r_sci_uart.o`, `r_gpt.o` を追加 (FSP ドライバを使う場合)
   - `include $(SRCDIR)/arch/arm_m_gcc/ra6m5_fsp/Makefile.chip`
8. **cfg テンプレート**: `target.tf`, `target_check.tf`, `target_offset.tf` を H5 から複製．ターゲット固有 ISR 検証ロジックは Phase 3 ビルド時に必要に応じて差替え．
9. **target_config.c の追加実装**:
   - **`hardware_init_hook()`**: 空 もしくは FPU CPACR enable 等 BSS 非依存処理のみ．**FSP `SystemInit()` は呼ばない** (BSS 前のため)．
   - **`target_hardware_initialize()`**: BSS 後．下記順序で初期化:
     1. `SystemInit()` (FSP `system.c`) を呼ぶ ＝ クロック初期化 + VTOR 仮設定 + R_BSP_WarmStart 一連
     2. `R_IOPORT_Open(&g_ioport_ctrl, &g_bsp_pin_cfg)` (`pin_data.c` のテーブルを使用)
     3. SCI9 の low-level 初期化 (レジスタ直叩き or `R_SCI_UART_Open`)
     4. `prc_hardware_initialize()` (ATK2 共通)
   - **`target_initialize()`** (StartOS から呼出，`target_hardware_initialize()` の後):
     1. ICU.IELSR 設定: `for (i=0; i<n; i++) R_ICU->IELSR[i] = (uint32_t)g_interrupt_event_link_select[i]`
     2. `prc_initialize()` (ATK2 共通; VTOR を ATK2 ベクタへ書換 + PendSV/SVC 優先度設定)
   - VTOR の確定書込みは `prc_initialize()` で行うため，FSP `SystemInit()` 内の VTOR 書込みは後で上書きされる (順序依存; 必ず `target_hardware_initialize` → `target_initialize` の順を守る)．
10. **README.md**: NUCLEO-H563ZI README に倣い，ボード資源・GPIO・ペリフェラル割当・優先度を記述．

## 検証 / 終了条件

- [ ] `target/ek_ra6m5_gcc/` が完成しコミット．
- [ ] `obj/obj_ek_ra6m5/Makefile` (Phase 3 で作成予定) と組み合わせて pass1 の `cfg1_out.c` 生成までが通る．
- [ ] BSP/FSP コードがエラーなくコンパイルされる (`bsp_clocks.o` 等の生成成功)．
- [ ] リンクは Phase 3 で完了させる．

## リスク

| 項目 | 内容 | 緩和策 |
|---|---|---|
| Smart Configurator 出力の `vector_data.c` を除外しても，`vector_data.h` の `BSP_VECTOR_TABLE_MAX_ENTRIES` 等の定数が他で参照される | ヘッダだけ残しソースを除外する形で大半は解決．残ればヘッダから一部抜粋 | Phase 3 ビルド時に判明 |
| `g_interrupt_event_link_select` シンボルが `bsp_irq.c:39` の弱定義 (全 0) にフォールバックして IELSR が空になる | 上記「設計判断」(a)/(b)/(c) のいずれかで FSP 生成テーブルを必ず compile・link する | Phase 2-B step 9 検証で `R_ICU->IELSR[N]` が 0 でないこと確認 |
| FSP `SystemInit()` を BSS 前に呼んで未定義動作 | `hardware_init_hook` を空にし，`target_hardware_initialize()` (BSS 後) で `SystemInit()` を呼ぶ | Phase 2-B step 9 |
| EK-RA6M5 の VCOM が SCI9 でない可能性 (ボード Rev 違い) | ユーザーズマニュアルで配線確認．異なれば適切な SCI に変更 | Phase 2-B step 4 |
| `TMAX_INTNO` の値が 96 で正しくない (RA6M5 の実 NVIC スロット数と一致しない) | `R7FA6M5BH.h` の `IRQn_Type` 定義から最大値を導出 | Phase 2-B step 6 |
| FSP `pin_data.c` が `R_IOPORT_Open` 呼出を要求する (どこから呼ぶ?) | `target_hardware_initialize()` で `R_IOPORT_Open(&g_ioport_ctrl, &g_bsp_pin_cfg)` を実行 | Phase 2-B step 9 |
| `BSP_MCU_GROUP_RA6M5` `BSP_MCU_R7FA6M5BH` が定義されない | これらは `bsp_cfg.h` (Smart Configurator 生成; target 層) で定義．chip 層 `Makefile.chip` の `-D` には含めない | Phase 2-A の bsp_cfg.h 内容を確認 |

## 後続フェーズへの引継

- Phase 3 が `obj/obj_ek_ra6m5/Makefile` を作成し，本層+チップ層+カーネルを統合してリンク可能状態にする．
- `configuration.xml` をコミットすることで，Smart Configurator 再起動時に同じ baseline を再生成できる．FSP バージョン更新時はこのファイルを基点に regen．

---

## 進捗記録 (Phase 2-B 骨格)

### 完了 (2026-04-29)

- `target/ek_ra6m5_gcc/` 一式を新規作成．`target/nucleo_h563zi_gcc/` 構造を踏襲．
- 主要ファイル:
  - `Makefile.target` (FPU_LAZYSTACKING, ra_cfg/ra_gen 検索パス, KERNEL_COBJS から vector_data.o 除外)
  - `r7fa6m5bh.ld` (Flash 2MB@0x00000000, SRAM 512KB@0x20000000．`/DISCARD/ : *(.fixed_vectors)` で FSP `__VECTOR_TABLE` を保険破棄)
  - `ek_ra6m5.h` (CPU_CLOCK_HZ=200M, PCLKD_HZ=100M, P006/P004/P008 LED 定義)
  - `target_kernel.h` (スタックサイズ等．TMIN_INTNO/TMAX_INTNO/TBITW_IPRI は `arch/arm_m_gcc/common/prc_config.h` の値を流用)
  - `target_config.c` (起動経路 §設計判断 (α): `hardware_init_hook` 空，`target_hardware_initialize` で SystemInit + IOPORT + SCI9 + prc_hw_init)
  - `target_serial.c/h` ＋ `target_serial.arxml` (SCI9 RX 割込み，INTNO 暫定 16)
  - `target_hw_counter.c/h` ＋ `target_hw_counter.arxml` (GPT320 free-run + GPT321 one-shot．INTNO 暫定 18)
  - `target_sysmod.h` `target_test.h` `target_cfg1_out.h` `target_rename.h` `target_unrename.h`
  - `target.tf` `target_check.tf` `target_offset.tf` (H5 同様 prc.tf を include するだけの薄い派生)
  - `ra_cfg/README.md` `ra_gen/README.md` (Smart Configurator 出力配置の TODO 説明)
  - `README.md` (ボード構成・GPIO・優先度・Phase 2-A 操作手順)

### 設計判断の確定状況

| 項目 | phase2.md §設計判断 候補 | 採用 | 備考 |
|---|---|---|---|
| `vector_data.c` 取扱 | (a) 抽出 / (b) リネーム / (c) リンカ廃棄 | **未確定** | `Makefile.target` は (a) 仮定で `vector_data.o` を `KERNEL_COBJS` から除外．Phase 2-A 完了後に最終決定．`r7fa6m5bh.ld` は (c) 用の `/DISCARD/` も併設 |
| `hardware_init_hook` 実装 | (α) FSP SystemInit を BSS 後に呼ぶ / (β) target 専用 SystemInit | **(α) 採用** | `hardware_init_hook` は空，`target_hardware_initialize` で `SystemInit()` を呼ぶ |

### Phase 2-A (ユーザ作業) 待ち項目

以下は `ra_cfg/` `ra_gen/` `configuration.xml` の Smart Configurator 出力受領後に確定:

- `target_serial.h` `INTNO_SIO` の実値 (`g_interrupt_event_link_select[]` の SCI9_RXI スロット番号 + 16)
- `target_serial.arxml` の `OsIsrInterruptNumber` `<VALUE>16</VALUE>` 部
- `target_hw_counter.h` `GPT321_INTNO` の実値 (GPT321_OVF スロット番号 + 16)
- `target_hw_counter.arxml` の `OsIsrInterruptNumber` `<VALUE>18</VALUE>` 部
- `target_config.c` の `EK_RA6M5_HAVE_VECTOR_DATA` 有効化判断 (Makefile.target で `-DEK_RA6M5_HAVE_VECTOR_DATA` を付与)
- `target_config.c` の `EK_RA6M5_USE_FSP_PINCFG` 有効化 (Smart Configurator 生成 `pin_data.c` の `g_bsp_pin_cfg` を取込）
- `vector_data.c` 取扱方式 (a)/(b)/(c) の最終確定．それに応じて `Makefile.target` `KERNEL_COBJS` を更新

### 既知の検証ポイント (Phase 3 でビルド時に解消)

- IDE (clangd) は `kernel_impl.h` `bsp_api.h` を解決できないため `target_config.c` `target_hw_counter.c` に多数のエラーマーカが出る．これは IDE の INCLUDE 設定問題であり実ビルドでは解決される．
- SCI9 BRR=26 計算は PCLKB=100MHz 仮定．Smart Configurator の `bsp_clock_cfg.h` で PCLKB 値を確認し，必要なら更新．
- GPT のクロック源は PCLKD 直結 (`TPCS=DIV1`) 固定で TIMER_CLOCK_HZ=1MHz としているが，PCLKD=100MHz では実 100tick/us になる．Phase 4 で 1tick=1us 相当にする最終調整 (PCLKD 設定変更 or GTPR でのソフト分周) を決定．
- `bsp_linker.c` (Option Setting Memory) は Phase 3 で `KERNEL_COBJS` に追加判断．現状リンカスクリプトに `.option_setting_*` セクションを置いていない．
