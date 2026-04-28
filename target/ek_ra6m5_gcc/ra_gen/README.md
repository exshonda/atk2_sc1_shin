# `ra_gen/` — Smart Configurator 生成ソース配置ディレクトリ

このディレクトリには **Renesas e² studio Smart Configurator** が生成する
ペリフェラル初期化ソースを配置する．Phase 2-A で初回生成し，以後 FSP
設定変更時にこのディレクトリ全体を上書き再生成する．

## 期待される構成

```
ra_gen/
├── common_data.c / .h     hal モジュール初期化テーブル
├── hal_data.c / .h        FSP モジュールインスタンス定義 (g_uart9_ctrl, g_timer0_ctrl 等)
├── pin_data.c             ピン構成 (R_IOPORT_Open に渡される g_bsp_pin_cfg)
└── vector_data.c / .h     ベクタテーブル + IELSR マッピング
                           ※ vector_data.c は ATK2 とのベクタ衝突を避けるため
                              ビルド対象外．IELSR テーブル
                              g_interrupt_event_link_select[] のみ参照する．
                              詳細は本層 README §4 を参照．
```

これらのうち **`common_data.o` / `hal_data.o` / `pin_data.o`** は
[`Makefile.target`](../Makefile.target) の `KERNEL_COBJS` に登録され
ビルド対象になる．**`vector_data.o`** は意図的に除外．

## 生成手順

[`../README.md`](../README.md) §3 (Smart Configurator 操作手順) を参照．

## vector_data.c の取扱

FSP 生成 `vector_data.c` には次の 2 つのシンボルが同居する:

- `g_vector_table[]` — ARM Cortex-M ベクタテーブル．**ATK2 cfg pass2 が
  生成する `kernel_vector_table[]` と衝突するため使えない．**
- `g_interrupt_event_link_select[]` — ICU.IELSR の値の配列．**必須．**
  これが無いと FSP `bsp_irq.c:39` の弱定義 (全 0) にフォールバックして
  IELSR が空になる．

Phase 2-B で下記いずれかを採用 (本層 README §4 を参照):
- (a) 抽出方式: `g_interrupt_event_link_select[]` だけ別ファイルに転記
- (b) リネーム方式: `objcopy --redefine-sym` で `g_vector_table` をリネーム
- (c) リンカ廃棄方式: リンカスクリプトで FSP `g_vector_table` を `/DISCARD/`

TODO[Phase 2-A]: 上記方式を確定し，`Makefile.target` を更新．
