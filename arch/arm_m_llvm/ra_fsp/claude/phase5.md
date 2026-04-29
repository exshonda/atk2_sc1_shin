# Phase 5: cfg_py 回帰テストの追加 (推奨; 任意)

## 目的

EK-RA6M5 ターゲットの cfg 出力 (`cfg1_out.c`, `Os_Lcfg.c/h`, `Os_Cfg.h`, `offset.h`) を `cfg/cfg_py/tests/` 配下のフィクスチャとして取り込み，**今後の cfg_py 改修で EK-RA6M5 ターゲットが壊れないこと** を pytest で保証する．

## 前提

- Phase 4 完了 (実機で sample1 全機能が動作)．
- 既存の H5 用 `test_integration_target_offset.py` 等が pass している．

## 設計判断

- C++ 版 cfg.exe は本リポジトリに同梱しないため，「C++ 版とのバイト一致」検証は H5 でしか行わない．EK-RA6M5 はバイト一致 baseline は cfg_py 自身の出力に対する **スナップショット比較** とする (回帰検出が目的)．
- フィクスチャは `cfg/cfg_py/tests/fixtures/ek_ra6m5/` 配下に，ARXML + 期待生成物のセットを配置．

## 成果物

```
cfg/cfg_py/tests/
├── fixtures/
│   └── ek_ra6m5/
│       ├── sample1.arxml           sample1 + ターゲットアラーム
│       ├── target_serial.arxml     SCI7 ISR 定義
│       ├── target_hw_counter.arxml GPT321 ISR 定義
│       └── expected/
│           ├── cfg1_out.c
│           ├── Os_Lcfg.c
│           ├── Os_Lcfg.h
│           ├── Os_Cfg.h
│           └── offset.h
├── test_integration_ek_ra6m5.py   pass1/2/3 を呼んで expected/ と比較
└── conftest.py                    既存 (フィクスチャ拡張があれば)
```

## 実施手順

1. Phase 4 完了時の `obj/obj_ek_ra6m5/` から下記をコピー:
   - 入力: `*.arxml` (sample1.arxml は `sample/` 由来，target_*.arxml は target 層由来)
   - 期待出力: `cfg1_out.c`, `Os_Lcfg.c`, `Os_Lcfg.h`, `Os_Cfg.h`, `offset.h`
2. `cfg/cfg_py/tests/fixtures/ek_ra6m5/` に整理して配置．
3. `test_integration_ek_ra6m5.py` を作成．`test_integration_kernel_tf.py` `test_integration_target_offset.py` を参考に，
   - pass1: `cfg.py --pass 1 --kernel atk2 ...` を呼んで生成 `cfg1_out.c` が `expected/cfg1_out.c` と一致することを assert
   - pass2: 同様に `Os_Lcfg.c/h` `Os_Cfg.h` 一致確認
   - pass3 / offset.h: 同様
4. `pytest -v cfg/cfg_py/tests/test_integration_ek_ra6m5.py` でグリーンになるまで調整．
5. Phase 4 で確認した sample1 仕様と乖離が出たら expected/ を更新 (この更新は意図的な仕様変更のときのみ)．

## 検証 / 終了条件

- [ ] `pytest -v cfg/cfg_py/` 全件 pass．
- [ ] EK-RA6M5 用テストが H5 用テストと同形式で書かれている．
- [ ] CI 等で自動実行する場合は `pytest` 既定経路で拾われる位置に配置．

## リスク

| 項目 | 内容 | 緩和策 |
|---|---|---|
| `cfg1_out.c` 内の絶対パスが Windows と Linux で違う | 既存 H5 テストは relative path 化済の生成物を使用．同方式踏襲 | 既存 fixture を参考に |
| GPT/SCI 番号の差異で多数のセクションが変動 | スナップショット比較は「変更検知」なのでこれで OK．意図的変更時に baseline 更新 | 通常運用 |

## 後続フェーズへの引継

- Phase 6 で README にテスト実行方法を記述．

## 任意性について

本フェーズはあると望ましいが必須ではない．Phase 4 が成立していれば実機ベースで動作保証されているため．Phase 5 を飛ばす判断は以下の場合に妥当:

- 既存 H5 用 cfg_py テストでバイト一致まで検証済 → cfg_py の正しさは別ルートで保証される．
- 開発者が常に Phase 4 を手動回帰可能 → 自動回帰の代用が可能．

その場合は Phase 6 に直行し，将来の必要時に立ち戻る．
