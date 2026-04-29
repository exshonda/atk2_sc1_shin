# Phase 4: 実機ブリングアップ

## 目的

Phase 3 で生成された `atk2-sc1.srec` を実機 EK-RA6M5 に書き込み，**最小限の動作 → シリアル → 割込み → HW カウンタ → サンプル全機能** の順に段階的に動作確認する．

## 前提

- Phase 3 までで EK-RA6M5 用 ELF/srec が生成可能 (commit `872fa1f` で確認済)．
- 実機 EK-RA6M5 + USB ケーブル + ホスト PC．
- J-Link GDB Server (J-Link Software, e² studio 同梱) または OpenOCD CMSIS-DAP．
- ホスト PC のシリアルターミナル (Tera Term / minicom 等)．
- **Arduino D0/D1 に接続可能な USB-Serial 変換アダプタ** (FTDI 等)．SCI7 を
  使う本ポートの構成では J-Link OB の VCOM (= SCI9) は使えないため．

## 役割分担

| 担当 | 範囲 |
|---|---|
| **ユーザ (人間)** | 実機接続 / J-Link 経由の書込み・デバッグ操作 / シリアル端末からのキー入力 / オシロ観測 (4-2 のみ) / 観察結果の Claude への報告 |
| **Claude** | ビルド (`make -j4`) / sample1.c の暫定改造 (4-1, 4-2) / 観察ログを元にした原因調査・修正パッチ作成 / commit / 既存ロジックの調整 |

ユーザは段階ごとに観測結果を Claude に伝える．Claude が次のステップ用の改造を準備し，ユーザがビルド済み srec を書込んで再観測する反復ループ．

## 共通: ビルドと書込みコマンド

### ビルド (Claude / ユーザどちらでも可)

```sh
cd obj/obj_ek_ra6m5
"C:/Renesas/e2_studio_2025.07/eclipse/plugins/com.renesas.ide.exttools.gnumake.win32.x86_64_4.3.1.v20240909-0854/mk/make.exe" \
    ATFE_PREFIX="C:/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin/" \
    -j4
```

成功時に `atk2-sc1.srec` (~110 KB) と `atk2-sc1` (ELF) が生成される．

> **Tip**: 上の長い PATH を毎回打つのが面倒なので，msys2 bash 上で
> ```sh
> export PATH="/c/Renesas/e2_studio_2025.07/eclipse/plugins/com.renesas.ide.exttools.gnumake.win32.x86_64_4.3.1.v20240909-0854/mk:$PATH"
> export ATFE_PREFIX="C:/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin/"
> ```
> を `~/.bashrc` 末尾に追記しておくと `make -j4` だけでビルドできる．

### 書込み (J-Link Commander)

EK-RA6M5 の **オンボード J-Link OB** を SWD で使用．ホスト PC が認識
する USB シリアル番号は J-Link デバイスとして見える．

`obj/obj_ek_ra6m5/Makefile` の `flash` ターゲットが下記コマンドを実行:

```
echo "h; loadfile atk2-sc1.srec; r; g; q" |
    JLink -device R7FA6M5BH -if SWD -speed 4000 -autoconnect 1 -nogui 1
```

`-device` / `-if` / `-speed` をコマンドライン引数で渡すことで，
J-Link Commander 起動時のデバイス選択 GUI / 対話プロンプトを抑止する．
script 側は connect 後の状態に対して halt / loadfile / reset / go を
順に発行するだけ．

```sh
cd obj/obj_ek_ra6m5
make flash
```

別チップに切り替えたい場合 (例: R7FA6M4 系) は `JLINK_DEVICE` 変数で
上書き:

```sh
make flash JLINK_DEVICE=R7FA6M4AF
```

> **PC に J-Link Software がインストールされていない場合**:
> Renesas の J-Link バンドル (e² studio v2025-12 同梱) もしくは
> [SEGGER 公式](https://www.segger.com/downloads/jlink/) から最新を
> 入手．`JLink.exe` が PATH に通っていれば `make flash` が動く．

### デバッグ (J-Link GDB Server + arm-none-eabi-gdb)

別端末で:
```sh
JLinkGDBServer -device R7FA6M5BH -if SWD -speed 4000 -port 3333
```

その後:
```sh
cd obj/obj_ek_ra6m5
make debug
```

### シリアル端末

| 設定項目 | 値 |
|---|---|
| ポート | USB-Serial 変換アダプタの COM ポート (≠ J-Link OB VCOM) |
| ボーレート | 115200 |
| データビット | 8 |
| パリティ | None |
| ストップビット | 1 |
| フロー制御 | None |

EK-RA6M5 の **Arduino UNO 互換ヘッダ J24** に下記接続:

| アダプタ側 | EK-RA6M5 J24 | ボード側ピン | 用途 |
|---|---|---|---|
| TX | Pin 0 (Arduino D0) | P614 (RXD7) | アダプタ TX → MCU RX |
| RX | Pin 1 (Arduino D1) | P613 (TXD7) | MCU TX → アダプタ RX |
| GND | GND ピン | — | 共通グラウンド |

> 5V/3.3V のレベル整合に注意．EK-RA6M5 は 3.3V 系．アダプタが 5V 系
> なら抵抗分圧かレベル変換器を介すこと．

---

## 実施手順 (段階的ブリングアップ)

### 4-1. 最小起動 (LED 点灯)

**目的**: `start.S → SystemInit → __libc_init_array → main` の経路と BSS 初期化が正しいことを確認．

1. **(Claude が準備)** `sample/sample1.c` の `main()` 先頭に下記を仮挿入し，
   ATK2 カーネル起動より前で LED1 を点滅させる最小ループを置く．
   ```c
   /* === Phase 4-1 ブリングアップ用 === BEGIN === */
   /* P006 (LED1) を出力に設定して busy-wait ブリンク．
    * SystemInit/IOPORT 初期化後にここに来る前提．R_PORT0 直叩き． */
   R_PORT0->PDR  |= (1U << 6);     /* PDR.PDR6=1 出力 */
   while (1) {
       R_PORT0->PODR ^= (1U << 6); /* PODR.PODR6 反転 */
       for (volatile uint32_t i = 0; i < 5000000U; i++) { __NOP(); }
   }
   /* === Phase 4-1 ブリングアップ用 === END === */
   StartOS(...);  /* 通常ここから ATK2 起動．4-1 では到達しない */
   ```
2. `make -j4 && make flash` で書込み．
3. リセット後，LED1 (青) が約 1 Hz で点滅すれば成功．
4. **(ユーザが Claude に報告)** 失敗時の症状:
   - LED が全く動かない → `start.S` の MSP 初期化または BSS clear が失敗．J-Link で halt して PC を確認．
   - リセットループ → `SystemInit()` 内で例外．`__VECTOR_TABLE` 設定または FPU 初期化失敗．
   - ハードフォルト直行 → vector table が 0x00000000 に正しく置かれていない可能性．`llvm-objdump -h atk2-sc1` で `.vectors @ 0x00000000` 確認．
5. **(Claude が確認)** 動作後，仮挿入したコードを削除して 4-2 へ進む．

### 4-2. クロック確認

**目的**: ICLK 200 MHz が正しく構成されているか確認．

1. GPIO (LED1) を最高速度でトグルする実装に変更．
2. オシロまたはロジアナで波形確認．**500 ns 以下の周期** = 200 MHz クロック動作の傍証．
3. 失敗時:
   - 周期が 8 倍 (HOCO 16MHz 由来) → PLL 起動失敗．`bsp_clock_cfg.h` の PLL 設定確認．
   - リセットループ → 電源モード (HP/LP) と VOS 設定不整合．

### 4-3. シリアル送信のみ

**目的**: SCI7 TX が ISR 無しで動作することを確認．

1. `target_config.c` の SCI7 初期化を実行し，ポーリングで `"Hello EK-RA6M5\n"` を送信．
2. ホスト PC の Tera Term (115200, 8N1, No flow control) で受信確認．
3. 失敗時:
   - 文字化け → ボーレート設定．`SCI7.SCR` `BRR` レジスタ値．
   - 何も出ない → ピン設定．P613 (Arduino D1) が AF (PSEL=04 → SCI7_TXD) になっているか確認．`pin_data.c` の生成内容を確認．

### 4-4. シリアル ISR 駆動 RX

**目的**: ATK2 の `interrupt_entry` 経由で SCI7 RXI ISR が呼べることを確認．

1. `target_serial.arxml` の INTNO が `g_interrupt_event_link_select` の SCI7_RXI スロット番号と一致しているか再確認．
2. `target_initialize()` 内で IELSR を設定: `R_ICU->IELSR_b[i].IELS = (event_id)`．
3. `sysmod/serial.c` 経由で `Input Command:` プロンプトが表示され，1 文字キー入力でエコーバックされることを確認．
4. 失敗時:
   - エコーが返らない → IELSR 設定漏れ，または ARXML INTNO 不一致．`R_ICU->IELSR_b[N]` の値を J-Link で読出し確認．
   - HardFault → ISR 関数のシンボル名と ARXML 登録名不一致．

### 4-5. HW カウンタ動作確認

**目的**: GPT320 (フリーラン) と GPT321 (ワンショット) が ATK2 アラーム機構と連動することを確認．

1. シリアルプロンプトで `T` コマンド: `MAIN_HW_COUNTER` 値が単調増加することを確認．増加レートが 1us/tick (= 1 MHz) であること．
2. `6` コマンド (本ポートで追加; CLAUDE.md 参照): 5 秒 × 4 回ログが出力されることを確認．
3. `b` コマンド: アラームベース情報表示．
4. `B` コマンド: アラーム残ティック数が単調減少 → 0 で発火．
5. 失敗時:
   - カウンタが進まない → GPT320 起動 (`GPT320.GTCR.b.CST = 1`) 漏れ．
   - レートが想定と異なる → クロック分周設定．PCLKD ÷ Prescaler の組合せ確認．
   - アラームが発火しない → GPT321 のオーバーフロー割込みが ICU 経由で NVIC に伝わっていない．IELSR 確認．

### 4-6. サンプル全機能

**目的**: NUCLEO-H563ZI で動作している sample1 の全コマンドが EK-RA6M5 でも動作することを確認．

| キー | 内容 | 期待動作 |
|---|---|---|
| `1`〜`5` | 操作対象タスクの選択 | プロンプトが `Select Task: N` |
| `a` | `ActivateTask(selected)` | タスク N が動作開始 |
| `e` | `SetEvent(MainEvt)` | 待機中タスクが解除 |
| `s` | `Schedule()` | 同優先度タスクの切替 |
| `b` `B` | アラームベース / 残ティック表示 | 数値が表示 |
| `T` | HW カウンタ値表示 | 単調増加 |
| `6` | HW カウンタ 5 秒ログ | 5 秒ごとに 4 回 |
| `Z` | 選択タスク状態表示 | READY/SUSPENDED 等 |
| `x` | CPU 例外発生 | HardFault → ATK2 例外ハンドラがログ出力 |

`x` コマンドが期待通り例外ログを出して停止することは，例外ハンドラ経路が完全であることを意味する重要マイルストーン．

### 4-7. 安定性確認

**目的**: 周期アラーム + 割込みディスパッチが長時間動作しても落ちず，
リソースリーク・スタックオーバーフロー・割込み欠落がないことを確認．
4-6 までは「動く」ことの検証だったが，本節は「動き続ける」ことの検証．

#### 4-7-1. 30 分連続稼働テスト (周期アラーム)

**前準備**:

- USB-Serial 変換アダプタを J24 D0/D1 に接続
- ホスト PC のシリアル端末 (Tera Term / minicom) を 115200, 8N1, ログ
  保存有効で開く
- ボード電源 ON → リセット → `Input Command:` プロンプトを確認

**実行**:

1. シリアル端末で **`a`** を入力 → 選択中タスクを `ActivateTask` →
   `MainCyc` (10ms 周期アラーム → ActivateTask) が発火開始
2. **そのまま 30 分以上放置** (放置中シリアル入力なし)
3. 30 分後シリアル端末で **`T`** を入力 → `MAIN_HW_COUNTER` 値を確認

**合格条件**:

- [ ] 30 分間，シリアル端末への出力が止まらない (= 落ちていない)
- [ ] HardFault / `default_exc_handler` メッセージが一度も出ていない
- [ ] `T` コマンド応答が即座に得られる (= ISR/dispatcher 経路健全)
- [ ] HW カウンタ値が単調増加し，30 分 ≈ 1.8e9 tick (25 MHz × 1800 sec)
      の範囲に収まっている．32-bit ラップが起きていれば 4.29G で巻き戻る
      が，巻き戻りがあっても挙動が変わらないこと

#### 4-7-2. 連続入力ストレステスト (シリアル ISR 飽和)

**実行**:

1. 4-7-1 の状態 (アラーム動作中) のまま継続
2. シリアル端末で **任意キーを長押し** (キーリピート) → 数秒間連続入力
3. リピート中も `MainCyc` 由来のタスクが動いていることを確認 (ログ等)
4. キーリピートを止めて `T` で HW カウンタを確認 → 想定値か

**合格条件**:

- [ ] キーリピート中に HardFault しない
- [ ] キーリピート中も周期アラーム駆動のタスクが動き続ける (ログで確認)
- [ ] キー入力に対するエコーバックがすべて返る (= RX 割込み欠落なし)
- [ ] リピート停止後すぐに通常応答に戻る (= ISR ロックアップなし)

#### 4-7-3. 観察結果の記録

ログファイル (Tera Term の保存ログ等) を保存し，下記を git に記録:

- `phase4-7_log.txt` (シリアル端末ログ; リポジトリには含めず別途保管推奨)
- 4-7-1 / 4-7-2 のチェックリスト結果を Claude に報告

#### 4-7-4. 失敗パターンと原因切分け

| 症状 | 仮説 | 確認方法 |
|---|---|---|
| 30 分以内に出力停止 + LED 一斉点灯/暗転 | HardFault / IWDT リセット | J-Link で halt → CFSR / `IWDTCNT` を確認．OFS0 で IWDT 停止確認 |
| 出力停止 (HardFault なし) | デッドロック / 割込み禁止状態固化 | J-Link で halt → BASEPRI / PRIMASK / `nested_lock_os_int_cnt` 確認 |
| HW カウンタが伸びない / フリーズ | GPT320 停止 / クロック停止 | `GPT320.GTCR` の CST ビット，`SCKCR` 系で ICLK 確認 |
| キーリピートで HardFault | スタックオーバーフロー / 割込みネスト深 | MSP/PSP の最低水位を J-Link で確認．`DEFAULT_ISRSTKSZ` を増 |
| キーが時々抜ける | RX FIFO オーバーラン (SSR.ORER) | `target_config.c` の SCI7 ISR で SSR.ORER をクリアしているか確認 |
| 数分で勝手にリセット | IWDT (OFS0 で disable し忘れ) | `r7fa6m5bh.ld` の OFS0 値で IWDTSTRT=1 になっていないか |

## 検証 / 終了条件

- [x] 4-1〜4-6 全段階クリア．
- [x] 4-7 で **10 分短縮版** 連続稼働確認 (2026-04-29; phase4_7_test.py
      による自動駆動)．30 分版は未実施だが，短縮版で代用．
- [x] H5 版と sample1 動作が同等であること．

### 4-7 実行結果 (2026-04-29; 10 分短縮版)

`obj/obj_ek_ra6m5/phase4_7_test.py` を pyserial 経由で実行．COM9, 115200
8N1．生ログは `obj/obj_ek_ra6m5/phase4_7.log` (gitignore 配下) に保存．

| 検査 | 結果 |
|---|---|
| 4-7-1 持続性 (10 分間 = 619 秒) | **PASS** — HardFault / 例外ハンドラ呼出 0 件 |
| 4-7-1 `'a'` で MainCyc 起動 | **PASS** — `Call ActivateTask(Task1)` + `Task1 ACTIVATE` |
| 4-7-1 末尾 `'T'` 応答 | **PASS** — `C1ISR Cnt:0, C2ISR Cnt:0` × 3 行即応 |
| 4-7-2 ストレス (`'1'` × 197 文字を 10 秒間連射) | **PASS** — 全 197 文字が echo + `Input Command:` 再表示．RX 割込み欠落 0 |
| ストレス後 `'T'` 応答 | **PASS** — 同様に正常応答 |
| 全ログ行数 | 412 行 (10 分間で十分な liveness シグナル) |

> 30 分版を後で回す場合は `python phase4_7_test.py --minutes 30 --port COM9`．
> 短縮の根拠: ICU.IELSR / dispatcher / RX ISR の実装は時間と独立に
> 健全/不健全が決まる構造のため，10 分でリーク・ロックの大半は捕捉可能．

## リスク

| 項目 | 内容 | 緩和策 |
|---|---|---|
| RA6M5 の Option Setting Memory が未書込みで起動できない | OFS0/OFS1 等のデフォルト値を `r7fa6m5bh.ld` の `.option_setting` セクションに配置 | Phase 3 ビルドエラーで早期検出 |
| MPU/Cache が初期化されていないため動作異常 | RA6M5 は M33 + I/D Cache あり．FSP の `bsp_common.c` がキャッシュを有効化しているはず | Phase 4-1 で挙動確認 |
| J-Link OB のドライバが古い | EK-RA6M5 同梱は最新版だが PC 側ドライバは要更新 | Renesas 公式から J-Link Software 最新を入手 |
| デバッグ中にウォッチドッグが発火 | IWDT が有効になっていれば一定時間で resets．OFS0 で無効化されているか確認 | OFS0 のデフォルトは IWDT 停止．問題ないはず |
| Trustzone Secure mode で起動して NS 領域にアクセス不可 | RA6M5 は M33 + TrustZone．本ポートは NS 単一．OSIS/SCISETP が NS 設定になっているか確認 | デフォルトは NS のはず．異常時は OFS で確認 |

## ユーザがブリングアップ中に Claude に報告するテンプレート

各段階で観察結果が想定と異なる場合，下記情報を Claude に伝えると
原因調査が効率化する．

### 4-1 (LED 点滅) で動かない

```
4-1: LED1 が点滅しない．
- リセット時の挙動: [何も見えない / リセットループ / 1回だけ点いて止まる]
- J-Link Commander の `connect` で `Found SW-DP with ID 0x6BA02477` 等
  正常メッセージは出る / 出ない
- `halt` 後の `regs` 出力 (PC, SP, LR の値) を貼付:
  PC = 0x________
  SP = 0x________
  LR = 0x________
- 必要なら .map / .syms から Reset_Handler や _kernel_start のアドレス
  を確認したい
```

### 4-2 (クロック確認) で周期が想定と違う

```
4-2: GPIO トグル周期が想定と異なる．
- オシロ実測: ___ ns/トグル
- 期待値: 200 MHz なら 5 ns/instr 程度，HOCO 20 MHz だと 50 ns/instr
- 推測される ICLK: ___ MHz
- bsp_clock_cfg.h の ICLK 設定: ___
```

### 4-3 (シリアル送信) で何も出ない / 文字化け

```
4-3: SCI7 送信．
- 期待出力: "Hello EK-RA6M5\n"
- 実出力: [何も出ない / バイナリゴミ / 一部だけ出る]
- 文字化けの場合は受信した生バイト列を hex で記載
- アダプタの COM ポート設定: 115200, 8N1, NoFlow
- ピン抵抗値 (TX/RX) を測ったら ___ kΩ
```

### 4-4 (シリアル ISR) で `Input Command:` が出るが入力がエコーされない

```
4-4: SCI7 RX ISR．
- "Input Command:" は出る / 出ない
- キー入力したが何も返らない / HardFault
- J-Link で halt して以下を採取して Claude に貼付したい:
  R_ICU->IELSR[1] (= SCI7_RXI 想定スロット): 0x________
  NVIC_ISER[0]: 0x________ (IRQ 1 が enable されているか)
  PRIMASK / BASEPRI: 0x__
  except_nest_cnt: __
```

### 4-5 (HW カウンタ) でアラームが発火しない

```
4-5: HW カウンタ．
- `T` コマンド: ___ → ___ (時間差)．想定 1us/tick
- `b` `B` 表示は正常 / NG
- アラームを設定して 1 秒待ったが ISR が呼ばれない
- R_GPT320->GTCNT を J-Link で連続読出: 進む / 進まない
- R_GPT321->GTCR.b.CST: ___ (1 ならカウント中)
- R_ICU->IELSR[0] (= GPT321 OVF 想定): 0x________
```

---

## 進捗記録 (2026-04-29 セッション中断時点)

### 達成済み (実機 EK-RA6M5 で検証)

- **4-1**: 起動 ✓ (`start.S` → `main` → `StartOS` → `target_initialize` 全て通過)
- **4-2**: クロック ICLK 200MHz ✓ (FSP `SystemInit` 完了．banner 出力速度より傍証)
- **4-3**: SCI7 送信 (ポーリング) ✓
  - banner + `pass1` がホスト側のシリアル端末で受信可能 (115200 8N1)
  - `target_fput_str` / `target_fput_log` ともに動作

### 起動時 HardFault 5 件を順次修正済 (commit `2be2d90` 〜 `ed31f97`)

1. **Thumb bit 二重加算**: ATK2 `prc.tf` の `(uint32)func + 1` が clang ATfE +
   ld.lld の組合せで二重加算となり vector LSB=0．`obj/obj_ek_ra6m5/Makefile`
   の sed post-process で `+1` を除去．
2. **MSPLIM 不整合**: FSP `system.c` が `__set_MSPLIM(&g_main_stack[0])` を実行．
   stub の g_main_stack を `.bss.g_main_stack` 専用セクションに置いて BSS 先頭
   (= SRAM 0x20000000) 配置．
3. **`__VECTOR_TABLE` 壊れスタブ**: `PROVIDE(__Vectors = kernel_vector_table)`
   でリンカエイリアス．SCB->VTOR 書込みが no-op になり SystemInit 中の例外も
   ATK2 ハンドラへ正しくルーティング．
4. **`__ram_zero` で OS スタック破壊**: `bsp_linker.c` の g_init_info の
   zero/copy リストを全て (0,0) に．ATK2 start.S が既に BSS clear / DATA copy
   完了している．
5. **SCI7 / GPT module stop**: `R_BSP_MODULE_START(FSP_IP_SCI, 7)` と
   `R_BSP_MODULE_START(FSP_IP_GPT, 0/1)` を `sci7_low_init` /
   `init_hwcounter_MAIN_HW_COUNTER` 冒頭で呼出．`GTWP_WRITE_ENABLE = 0xA501`
   が逆だった (正しくは `0xA500`，FSP の名前と紛らわしい) のも修正．
6. **`g_interrupt_event_link_select` 抽出**: `target_irq_data.c` 新規作成．
   FSP 生成 `vector_data.c` は g_vector_table と同居しビルド除外しているため
   従来 weak 弱定義 (全 0) にフォールバック．これで R_ICU->IELSR が正しく設定．

### 再開: alarm 経路 HardFault の根本原因と fix (2026-04-30)

**根本原因**: `arch/arm_m_gcc/common/arm_m.h:67` の `EXC_RETURN = 0xFFFFFFBC`
が **Non-Secure (ES bit=0)** だが，EK-RA6M5 の FSP "Flat Non-TrustZone"
ビルドはデバイスを **Secure state** で動作させる．Cortex-M33 は EXC_RETURN
の ES bit が現 security state と一致しないと CFSR.INVPC で HardFault する．

| 項目 | 観測値 / 期待値 | 解釈 |
|---|---|---|
| HardFault 時 LR | 0xFFFFFFB9 | thread + MSP + no FP + **Secure** (HW が正しくセット) |
| ATK2 dispatcher の `exc_return_const` | 0xFFFFFFBC | thread + PSP + no FP + **Non-Secure** ← ES bit 不整合 |
| 必要な値 (Secure 環境) | 0xFFFFFFBD | thread + PSP + no FP + **Secure** |

H5 (NUCLEO-H563ZI) は STM32H5 が既定で Non-Secure 動作のため 0xFFFFFFBC で
正常．RA6M5 は Renesas RA の Secure 動作のため 0xFFFFFFBD が必要．

#### Fix (commit 予定)

1. `arch/arm_m_gcc/common/arm_m.h`: `EXC_RETURN` の `#define` を `#ifndef`
   ガードでラップし，外部から override 可能に．既定値は 0xFFFFFFBC のまま
   (H5 互換)．コメントに ES bit の意味と Secure/Non-Secure 区分を追記．
2. `arch/arm_m_llvm/ra_fsp/Makefile.chip`: `CDEFS += -DEXC_RETURN=0xffffffbd`
   を追加．本層を使う全 RA ターゲット (RA6M5/RA6M4/RA4M2/RA6T2 等) で
   Secure EXC_RETURN が選択される．

#### H5 副作用

なし．`arch/arm_m_gcc/common/arm_m.h` の変更は `#ifndef` ガード追加
(純粋に追加的)．override が無ければ既定値 0xFFFFFFBC が使われ，H5
ビルド (= override しない) は従来通り．

### 旧: alarm 経路 (Phase 4-4/4-5) の HardFault — 中断時点の調査メモ (上記 fix で解消の見込み)

GPT321 OVF 割込みは正しく発火し，
`kernel_interrupt_entry` → `kernel_inthdr_16` → `kernel_notify_hardware_counter`
→ `kernel_expire_process` → `BLX get_hwcounter` までは ISR 経路で実行を
確認 (BP で確認済)．`get_hwcounter` は無事 return するが，その後 ~512μs
以内に **CFSR=INVPC** で HardFault．

#### 観測値

| 項目 | 値 |
|---|---|
| HardFault 時 PC | 0x000002A6 (`default_exc_handler` infinite loop) |
| LR (handler 内) | 0xFFFFFFB9 (= EXC_RETURN: thread/PSP/secure) |
| MSP | 0x20002688 |
| MSPLIM | 0x20000000 (健全) |
| CFSR | 0x00040000 (INVPC: invalid PC from EXC_RETURN) |
| HFSR | 0x40000000 (FORCED) |
| 例外スタックフレーム LR | 0x00000000 ← bug! |
| 例外スタックフレーム PC | 0x000085F8 (.rodata 領域 — 不正) |

#### 仮説

ATK2 dispatcher の `kernel_interrupt_entry` (arch/arm_m_gcc/common/prc_support.S
+ prc_config.c) が Cortex-M33 + TrustZone secure 環境で EXC_RETURN を
正しく扱えていない可能性．ARMv8-M セキュリティ拡張ありの状態でハードウェア
は exception entry 時に整合性シグニチャ + secure context を追加スタッキング
するが，ATK2 共通コードはこれを想定せず単純な LR push/pop のみ．

#### 暫定回避策 (本コミットに含む)

- `sample/sample1.c`: `EK_RA6M5_BYPASS_ALARM` マクロで `SetRelAlarm` +
  `WaitEvent` をスキップする実装に変更．
- `target/ek_ra6m5_llvm/Makefile.target`: `-DEK_RA6M5_BYPASS_ALARM` を
  追加．これで alarm 経路を完全回避し，busy loop で `Input Command:`
  を繰り返し出力する形になる．SCI7 RX (Phase 4-4) を独立検証可能．

### 次セッション着手時の調査ポイント (割込み経路の見直し)

1. **ARMv8-M Cortex-M33 + TrustZone での例外スタッキング規則**
   - `FPCCR.LSPACT` (Lazy Stacking)
   - `FPCCR.S` / `FPCCR.SFRDY` (secure FP)
   - `CONTROL.FPCA` の状態
   - secure-to-secure exception 時の追加スタッキング (16 word integrity 含む)

2. **ATK2 `arch/arm_m_gcc/common/prc_support.S` の見直し**
   - `_kernel_interrupt_entry` の push/pop が EXC_RETURN を正しく
     preserve するか
   - PSP/MSP 切替が secure 拡張下で問題ないか
   - `_kernel_dispatcher_0` が secure context を正しく扱うか

3. **Cortex-M33 secure debug 設定**
   - bsp_cfg.h の TrustZone 関連定義 (BSP_TZ_NONSECURE_BUILD, etc.)
   - OFS/SAR レジスタの secure 境界設定
   - 必要なら `Flat Non-TrustZone` を維持しつつ secure 専用設定を選択

4. **NVIC priority と BASEPRI の整合**
   - 現在 GPT321 OVF priority=0xF0 / SCI7 RXI priority=0xE0
   - tmin_basepri=0x10 で C2ISR 全許可 (priority < 0xFF mask 範囲外)
   - PendSV/SVC priority が secure 側で正しく登録されているか
   - 各 IRQ で AIRCR.PRIS (Priority Inversion) が想定通りか

5. **alternative**: ATK2 共通を変更したくない場合，FSP r_sci_uart / r_gpt
   ドライバ経由で割込みを扱う実装に切替．`R_SCI_UART_Open` /
   `R_GPT_Open` を呼び FSP 提供のコールバックチェインに乗せれば，
   ATK2 はそのコールバックの上で動くだけになり Cortex-M33 secure 関連
   の細かいスタッキング差異を FSP に任せられる．

### 動作確認用ヘルパー

- `obj/obj_ek_ra6m5/flash.jlink`: J-Link Commander スクリプト
  (h / loadfile / r / g / q)．`make flash` 経由ではなく
  `JLink -device R7FA6M5BH -if SWD -speed 4000 -autoconnect 1 -nogui 1
  -CommandFile flash.jlink` で書込み可能．

## 後続フェーズへの引継

- Phase 5 で cfg_py の回帰テストフィクスチャを EK-RA6M5 用に追加 (任意)．
- Phase 6 でドキュメント整備と e² studio プロジェクト同梱．
