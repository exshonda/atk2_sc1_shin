# `ra_cfg/` — Smart Configurator 生成ヘッダ配置ディレクトリ

このディレクトリには **Renesas e² studio Smart Configurator** が生成する
構成ヘッダ群を配置する．Phase 2-A で初回生成し，以後 FSP 設定変更時に
このディレクトリ全体を上書き再生成する．

## 期待される構成

```
ra_cfg/
└── fsp_cfg/
    ├── bsp/
    │   ├── bsp_cfg.h               BSP 全体設定 (BSP_MCU_R7FA6M5BH 等の MCU 識別)
    │   ├── bsp_clock_cfg.h         クロック設定 (HOCO/PLL/ICLK/PCLKD)
    │   ├── bsp_module_irq_cfg.h    モジュール (SCI/GPT/...) の優先度
    │   └── ...
    └── r_*/                        各ペリフェラルドライバの設定ヘッダ
```

これらは **`-I$(TARGETDIR)/ra_cfg/fsp_cfg`** および
**`-I$(TARGETDIR)/ra_cfg/fsp_cfg/bsp`** として
[`Makefile.target`](../Makefile.target) の `INCLUDES` に追加される．

## 生成手順

[`../README.md`](../README.md) §3 (Smart Configurator 操作手順) を参照．

## 留意事項

- `bsp_cfg.h` 内で `#define BSP_MCU_GROUP_RA6M5` および
  `#define BSP_MCU_R7FA6M5BH` が定義されていることを確認すること．これらは
  `Makefile.chip` の `-D` には書かない方針．
- FSP バージョン更新時は本ディレクトリを丸ごと上書き．差分はリポジトリの
  diff で確認可能．
