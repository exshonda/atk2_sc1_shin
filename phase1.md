# Phase 1: チップ依存部の骨格作成

## 目的

Renesas RA ファミリ (Cortex-M33) 向けチップ依存部 `arch/arm_m_llvm/ra_fsp/` を新規作成し，後続フェーズが取り込めるよう **ビルド配線の骨格** を整備する．EK-RA6M5 (R7FA6M5BH) を最初の対象とし，**他の Cortex-M33 RA シリーズ (RA4M2/M3, RA6M4, RA6T2, RA8M1 等) にも展開可能な汎用構成** とする．

## 前提

- ATK2 共通プロセッサ依存部 `arch/arm_m_gcc/common/` は変更しない (Cortex-M33 共通部分はそのまま再利用)．
- Renesas FSP 6.4.0 (Smart Configurator sc_v2025-12) を使用．インストール先 `C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/` 想定．
- **FSP ソースは本リポジトリには同梱しない**．clone 後にユーザが `rascc.exe --generate <configuration.xml>` でターゲット直下に生成する．

## 設計判断

- **(A) FSP の取り込み方**: **オンデマンド生成方式**．`configuration.xml` のみコミットし，clone 後にユーザが `rascc --generate` で `target/<TARGET>/ra/` `ra_cfg/` `ra_gen/` を生成．これらは `.gitignore` で除外．**chip 層 (`arch/arm_m_llvm/ra_fsp/`) には FSP ソースを置かない**．
  - 旧方針 (FSP 6.4.0 を chip 層に同梱) は撤回．配布サイズと FSP バージョンアップ容易性のため．
- **(B) ベクタテーブル戦略**: ATK2 cfg pass2 が生成する `Os_Lcfg.c` 内のテーブルに統一．FSP 生成の `vector_data.c` の `g_vector_table[]` は Phase 2 でビルド対象外にする．`ICU.IELSR` (NVIC スロット ↔ ペリフェラル割込みのマップ) は FSP 生成の `g_interrupt_event_link_select` テーブルを参照する．
- **(C) RA ファミリ汎用化**: chip 層は `MCU_GROUP` (例: `ra6m5`/`ra6m4`/`ra4m2`/`ra6t2`) と `CORE_CPU` (例: `cortex-m33`/`cortex-m85`) を `Makefile.target` から受け取って組み立てる．EK-RA6M5 以外のボードを将来追加する際は，target 層を新設するだけで chip 層は変更不要．

## 成果物

```
arch/arm_m_llvm/ra_fsp/
├── README.md                  RA ファミリ汎用 chip 層解説 + 責務分担表
├── chip_config.h              ATK2 → FSP BSP API への接続点 (#include "bsp_api.h")
├── Makefile.chip              CPU/FSP コンパイルオプション + BSP COBJS リスト
└── docs/
    └── fsp_setup.md           clone 後にユーザが実施する FSP 取込手順
```

`fsp/` サブディレクトリは **存在しない**．FSP ソースは各ターゲット直下に
`rascc --generate` で生成される設計．

## 実施手順

1. ブランチ `feat/ek_ra6m5_phase1` を切る．
2. `chip_config.h` を H5 版に倣って作成．`#include "bsp_api.h"` のみ．
3. `Makefile.chip` に下記を定義:
   - `CHIPDIR = $(SRCDIR)/arch/$(PRC)_$(TOOL)/$(CHIP)`
   - `FSPDIR = $(TARGETDIR)/ra/fsp` (ターゲット直下を参照．rascc 生成)
   - `MCU_GROUP` 必須化 (Makefile.target が指定．未指定時 `$(error)`)
   - `CORE_CPU ?= cortex-m33` (上書き可．M85 系 RA8 で使用)
   - `COPTS += -mcpu=$(CORE_CPU) -mthumb -mlittle-endian`
   - `CDEFS += -D_RENESAS_RA_`
   - `FPU_ARCH_OPT ?= fpv5-sp-d16`, `FPU_ARCH_MACRO ?= __TARGET_FPU_FPV5_SP`
   - `INCLUDES`: `$(CHIPDIR)`, `$(FSPDIR)/inc`, `$(FSPDIR)/inc/api`, `$(FSPDIR)/inc/instances`, `$(FSPDIR)/src/bsp/cmsis/Device/RENESAS/Include`, `$(FSPDIR)/src/bsp/mcu/all`, `$(FSPDIR)/src/bsp/mcu/$(MCU_GROUP)`
   - `KERNEL_DIR += $(CHIPDIR) $(FSPDIR)/src/bsp/mcu/all $(FSPDIR)/src/bsp/cmsis/Device/RENESAS/Source`
   - `KERNEL_COBJS += bsp_clocks.o bsp_common.o bsp_delay.o bsp_group_irq.o bsp_guard.o bsp_io.o bsp_irq.o bsp_macl.o bsp_register_protection.o bsp_sbrk.o bsp_security.o system.o`
   - `include $(SRCDIR)/arch/$(PRC)_$(TOOL)/common/Makefile.prc`
4. `README.md` に責務分担表 (§6) と FSP 取込が必要な点 (§7 既知制限) を記述．
5. `docs/fsp_setup.md` でユーザ向け手順 (rascc インストール → `--generate` 実行 → 検証) を整備．
6. `.gitignore` に `target/*/ra/` `target/*/ra_cfg/` `target/*/ra_gen/` を追加．
7. コミット．

## 検証 / 終了条件

- [ ] 上記成果物が `feat/ek_ra6m5_phase1` ブランチにコミット済み．
- [ ] `arch/arm_m_llvm/ra_fsp/fsp/` サブディレクトリが**存在しない** (FSP 同梱しない方針の遵守)．
- [ ] `target/<T>/ra/` 等が `.gitignore` で除外されている．
- [ ] `arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md` を読んだだけで，新規開発者が rascc を導入し `--generate` を実行できる．
- [ ] **本フェーズではコンパイルは行わない**．コンパイル検証は Phase 3 (Phase 2-A の rascc --generate 完了後) で実施．

## リスク

| 項目 | 内容 | 緩和策 |
|---|---|---|
| FSP `system.c` の `SystemInit()` 内部で BSS 領域変数を初期化する (`bsp_init_uninitialized_vars()`) | `start.S` の **`hardware_init_hook` (BSS 前) からは呼べない**．`target_hardware_initialize()` (BSS 後) から呼ぶ設計に決定 | README §6.1 に詳述 |
| FSP の弱定義 `Default_Handler` / NMI/HardFault 等が ATK2 ベクタと衝突 | `bsp_irq.c` 内に `Default_Handler` の弱定義あり．ATK2 cfg pass2 出力のベクタが弱定義を上書きする想定．Phase 3 ビルド時に `nm $(OBJFILE) \| grep Default_Handler` で確認 | Phase 3 検証項目 |
| `vector_data.c` のシンボル `g_interrupt_event_link_select[]` (必須) と `g_vector_table[]` (衝突) の同居 | Phase 2 で抽出/リネーム/廃棄のいずれかで対処．`bsp_irq.c:39` に `g_interrupt_event_link_select` の弱定義 (全 0) があるため，何も対処せず `vector_data.c` を除外すると IELSR テーブルが空になる | phase2.md「設計判断」「リスク」表に詳述 |
| `BSP_MCU_GROUP_RA6M5` `BSP_MCU_R7FA6M5BH` 等の MCU 識別マクロが定義されない | これらは Smart Configurator 生成の `bsp_cfg.h` (target 層) で定義．`Makefile.chip` の `-D` には書かない | README §4 と §7 で明示 |
| `bsp_linker.c` (Option Setting Memory `.option_setting_*`) が `KERNEL_COBJS` に未追加 | Phase 1 では意図的に外している．Phase 3 でリンカスクリプト整備時に追加し，OFS デフォルト値 (IWDT 停止等) が Flash 既定領域に配置されるようにする | phase3.md リスク表に記載 |
| RA8 系 (Cortex-M85) は `CORE_CPU=cortex-m85` 指定だけでは不十分 | Cortex-M85 は `-mfpu=fpv5-d16`，DCache 等 M33 と差異あり．現状は M33 系のみ動作確認．M85 対応は別途タスク | README §1 で明記 |

## 後続フェーズへの引継

- Phase 2 が `target/ek_ra6m5_llvm/configuration.xml` を整備し，ユーザが `rascc --generate` を実行することで，本層と組み合わせて全体ビルドが成立するようになる．
- 他の Cortex-M33 RA チップ向けターゲットを追加する場合は，`target/<board>_gcc/Makefile.target` で `MCU_GROUP` `CORE_CPU` を変更するだけで chip 層は再利用可．
