# Phase 4: 実機ブリングアップ

## 目的

Phase 3 で生成された `atk2-sc1.srec` を実機 EK-RA6M5 に書き込み，**最小限の動作 → シリアル → 割込み → HW カウンタ → サンプル全機能** の順に段階的に動作確認する．

## 前提

- Phase 3 までで EK-RA6M5 用 ELF/srec が生成可能．
- 実機 EK-RA6M5 + USB ケーブル + ホスト PC．
- J-Link GDB Server (J-Link Software, e² studio 同梱) または OpenOCD CMSIS-DAP．
- ホスト PC のシリアルターミナル (Tera Term / minicom 等)．

## 実施手順 (段階的ブリングアップ)

### 4-1. 最小起動 (LED 点灯)

**目的**: `start.S → SystemInit → __libc_init_array → main` の経路と BSS 初期化が正しいことを確認．

1. `sample/sample1.c` の `main()` 先頭に LED1 を 1 秒間隔で点滅させる最小コードを暫定追加 (FSP `R_BSP_PinAccessEnable` + IO レジスタ直接書込み)．
2. `make -j4 && make flash` で書込み．
3. リセット後，LED1 が点滅すれば成功．
4. 失敗時:
   - LED が全く動かない → `start.S` の MSP 初期化または BSS clear が失敗．J-Link で halt して PC を確認．
   - リセットループ → `SystemInit()` 内で例外．`__VECTOR_TABLE` 設定または FPU 初期化失敗．

### 4-2. クロック確認

**目的**: ICLK 200 MHz が正しく構成されているか確認．

1. GPIO (LED1) を最高速度でトグルする実装に変更．
2. オシロまたはロジアナで波形確認．**500 ns 以下の周期** = 200 MHz クロック動作の傍証．
3. 失敗時:
   - 周期が 8 倍 (HOCO 16MHz 由来) → PLL 起動失敗．`bsp_clock_cfg.h` の PLL 設定確認．
   - リセットループ → 電源モード (HP/LP) と VOS 設定不整合．

### 4-3. シリアル送信のみ

**目的**: SCI3 TX が ISR 無しで動作することを確認．

1. `target_config.c` の SCI3 初期化を実行し，ポーリングで `"Hello EK-RA6M5\n"` を送信．
2. ホスト PC の Tera Term (115200, 8N1, No flow control) で受信確認．
3. 失敗時:
   - 文字化け → ボーレート設定．`SCI3.SCR` `BRR` レジスタ値．
   - 何も出ない → ピン設定．P302 (Arduino D1) が AF (PSEL=04 → SCI3_TXD) になっているか確認．`pin_data.c` の生成内容を確認．

### 4-4. シリアル ISR 駆動 RX

**目的**: ATK2 の `interrupt_entry` 経由で SCI3 RXI ISR が呼べることを確認．

1. `target_serial.arxml` の INTNO が `g_interrupt_event_link_select` の SCI3_RXI スロット番号と一致しているか再確認．
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

1. `MainCyc` (10ms 周期アラーム + ActivateTask) を 30 分以上回し，落ちないこと．
2. シリアルへの連続入力 (キーリピート) でも不安定にならないこと．

## 検証 / 終了条件

- [ ] 4-1〜4-6 全段階クリア．
- [ ] 4-7 で 30 分連続稼働確認．
- [ ] H5 版と sample1 動作が同等であること．

## リスク

| 項目 | 内容 | 緩和策 |
|---|---|---|
| RA6M5 の Option Setting Memory が未書込みで起動できない | OFS0/OFS1 等のデフォルト値を `r7fa6m5bh.ld` の `.option_setting` セクションに配置 | Phase 3 ビルドエラーで早期検出 |
| MPU/Cache が初期化されていないため動作異常 | RA6M5 は M33 + I/D Cache あり．FSP の `bsp_common.c` がキャッシュを有効化しているはず | Phase 4-1 で挙動確認 |
| J-Link OB のドライバが古い | EK-RA6M5 同梱は最新版だが PC 側ドライバは要更新 | Renesas 公式から J-Link Software 最新を入手 |
| デバッグ中にウォッチドッグが発火 | IWDT が有効になっていれば一定時間で resets．OFS0 で無効化されているか確認 | OFS0 のデフォルトは IWDT 停止．問題ないはず |
| Trustzone Secure mode で起動して NS 領域にアクセス不可 | RA6M5 は M33 + TrustZone．本ポートは NS 単一．OSIS/SCISETP が NS 設定になっているか確認 | デフォルトは NS のはず．異常時は OFS で確認 |

## 後続フェーズへの引継

- Phase 5 で cfg_py の回帰テストフィクスチャを EK-RA6M5 用に追加 (任意)．
- Phase 6 でドキュメント整備と e² studio プロジェクト同梱．
