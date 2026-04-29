# Phase 6: ドキュメントと IDE 統合

## 目的

EK-RA6M5 移植を NUCLEO-H563ZI 移植と同等の完成度に揃える．README 整備，CLAUDE.md 更新，e² studio プロジェクト雛形同梱を行い，**他開発者が手順書通りに辿ればクリーンビルド + 実機書込みまで到達できる** 状態にする．

## 前提

- Phase 4 完了 (実機動作確認済み)．
- (任意) Phase 5 完了 (cfg_py 回帰テスト)．

## 成果物

### ドキュメント更新

```
README.md                       ルート: 対応ターゲット表に EK-RA6M5 追加
CLAUDE.md                       Architecture layering 表に行追加，
                                Common pitfalls に RA 固有事項追記
arch/arm_m_llvm/ra_fsp/README.md   Phase 1 で作成済．Phase 6 で実機検証
                                済バージョンに更新 (動作確認状況追記)
target/ek_ra6m5_llvm/README.md   Phase 2 で作成済．Phase 6 で完成版に更新
                                (NUCLEO-H563ZI README と同章構成)
```

### IDE 統合 (任意; e² studio 用)

```
target/ek_ra6m5_llvm/e2studio/
├── .project                    Eclipse プロジェクトファイル
├── .cproject                   CDT ビルド設定
├── configuration.xml           Smart Configurator のソース (Phase 2 で作成済)
└── sample/
    └── Makefile                IDE 内ビルド用 (configure 不要; obj/ 相当)
```

NUCLEO-H563ZI の `target/nucleo_h563zi_gcc/STM32CubeIDE/` と同じ位置付け．

## 実施手順

### 6-A: README/CLAUDE.md 更新

1. ルート `README.md` 修正:
   - 「ディレクトリ構成」: `target/ek_ra6m5_llvm/` と `obj/obj_ek_ra6m5/` を追加．
   - 「セットアップ」: e² studio (Smart Configurator 用) と J-Link Software (書込み用) のバージョン追記．
   - 「ビルド・実行」: EK-RA6M5 用ビルド手順節を追加．
   - 「対応ターゲット」表 (新設または既存テーブル拡張) に EK-RA6M5 を記載．
2. `CLAUDE.md` 修正:
   - 「Architecture layering」表に行追加: chip = `arch/arm_m_llvm/ra_fsp/`, target = `target/ek_ra6m5_llvm/` (RA6M5 + FSP 6.4.0).
   - 「ARXML and the configuration model」: ICU IELSR が ARXML INTNO に紐づくことを追記．
   - 「Common pitfalls」: RA 固有事項を追記:
     - FSP 再生成は Smart Configurator (e² studio GUI) が必要．`configuration.xml` が source-of-truth．
     - `vector_data.c` は `Makefile.target` で除外 (cfg 生成のベクタテーブルと衝突)．
     - Option Setting Memory (OFS0/OFS1) はリンカスクリプトで配置．
3. `arch/arm_m_llvm/ra_fsp/README.md` の §9 「バージョン履歴」を Phase 6 完了に更新．§7 「既知の制限」から「コンパイルできない」を削除．
4. `target/ek_ra6m5_llvm/README.md` 完成版を NUCLEO-H563ZI README の章立てで作成:
   - §1 構成
   - §2 開発環境バージョン
   - §3 メモリマップ (Flash 2MB / SRAM 512KB)
   - §4 システムクロック (200 MHz, HOCO/MOSC, PLL 設定値)
   - §5 使用システムリソース (GPIO, USART/SCI, ペリフェラル, 例外優先度)
   - §6 ターゲット定義事項 (`target_kernel.h` 値)
   - §7 ファイル構成
   - §8 ビルド方法 (Make + msys2)
   - §9 ビルド方法 (e² studio)
   - §10 サンプルアプリケーション (sample1 コマンド表)
   - §11 既知の制限
   - §12 バージョン履歴

### 6-B: e² studio プロジェクト同梱 (任意)

1. Phase 2 で生成した e² studio プロジェクトを `target/ek_ra6m5_llvm/e2studio/` にコピー．`configuration.xml` を含む．
2. `.cproject` の Build Behavior で並列度を `-j4` に固定 (Windows make 制約)．
3. プロジェクトの「Linked Resources」設定でカーネル/サンプル/sysmod のソースを参照する形にする (NUCLEO-H563ZI 版を参考)．
4. `target/ek_ra6m5_llvm/README.md` §9 に取込手順を記載．
5. 取込手順を実機で再現してクリーンビルド可能なことを確認．

## 検証 / 終了条件

- [ ] ルート `README.md` で EK-RA6M5 と NUCLEO-H563ZI が同等に紹介されている．
- [ ] `CLAUDE.md` の Architecture layering / Pitfalls 表に RA6M5 行が追加され，整合性が保たれている．
- [ ] `target/ek_ra6m5_llvm/README.md` が独立したドキュメントとして完結．
- [ ] (任意) e² studio で `target/ek_ra6m5_llvm/e2studio/` を import → Build → Flash → 実機動作 が手順書通りに到達できる．
- [ ] フェーズ進行用ドキュメント (`phase*.md`) は本フェーズ完了時にリポジトリから削除するか `doc/` 配下にアーカイブする．

## リスク

| 項目 | 内容 | 緩和策 |
|---|---|---|
| Smart Configurator が再起動時に `ra/` ツリーを再生成しようとする | configuration.xml と project プロパティの整合性．`ra/` を read-only マウントするか，FSP version lock | NUCLEO-H563ZI と同様にローカル import 推奨 |
| Microsoft Store Python が e² studio から見えない | H5 で同じ問題に直面．README §9 で対処手順を明記 | NUCLEO-H563ZI README §9 の説明をそのまま流用 |
| 配布サイズが大きい (FSP 同梱で +8 MB) | 必要なら `git lfs` 化 or サブモジュール化を検討 | 通常の commit でも問題ないサイズではある |

## 後続作業 (Phase 6 以降)

- 別ターゲット (例: AE-CLOUD2 や CK-RA6M5) への展開: chip 層は再利用可．target 層を新設する形．
- TrustZone Secure 側対応: 別途設計が必要．本ポートでは未対応．
- DMA / DTC を使った高速 I/O: FSP の `r_dtc` `r_dmac` を取り込み．
- FreeRTOS との共存ではなく ATK2 単独だが，同形式で他 Renesas RA / RX シリーズに展開可能．
