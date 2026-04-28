# Phase 1: チップ依存部の骨格作成

## 目的

Renesas RA6M5 (R7FA6M5BH, EK-RA6M5 搭載) 向けチップ依存部 `arch/arm_m_gcc/ra6m5_fsp/` を新規作成し，後続フェーズが取り込めるよう **FSP ライブラリ同梱とビルド配線の骨格** を整備する．

## 前提

- ATK2 共通プロセッサ依存部 `arch/arm_m_gcc/common/` は変更しない (Cortex-M33 共通部分はそのまま再利用)．
- Renesas FSP 6.1.0 を e² studio 2025-07 同梱 pack から取り込む．
- Smart Configurator (e² studio GUI) でしか生成できない `ra_cfg/`/`ra_gen/` は本フェーズでは扱わない (Phase 2 で対応)．

## 設計判断

- **(A) FSP の取り込み方**: Smart Configurator 出力をそのままコミット．アップグレード時は手動で `fsp/` を上書き．
- **(B) ベクタテーブル戦略**: ATK2 cfg pass2 が生成する `Os_Lcfg.c` 内のテーブルに統一．FSP 生成の `vector_data.c` の `g_vector_table[]` は Phase 2 でビルド対象外にする．`ICU.IELSR` (NVIC スロット ↔ ペリフェラル割込みのマップ) は FSP 生成の `g_interrupt_event_link_select` テーブルを参照する．

## 成果物

```
arch/arm_m_gcc/ra6m5_fsp/
├── README.md                  Phase 1 骨格の解説 + FSP 同梱範囲 + 責務分担表
├── chip_config.h              ATK2 → FSP BSP API への接続点 (#include "bsp_api.h")
├── Makefile.chip              CPU/FSP コンパイルオプション + BSP COBJS リスト
└── fsp/                       Renesas FSP 6.1.0 (vendor as-is)
    ├── inc/                   API + instance ヘッダ全部入り (4.5 MB)
    ├── src/bsp/               cmsis + mcu/all + mcu/ra6m5
    ├── src/r_ioport/, r_cgc/, r_icu/, r_sci_uart/, r_gpt/  Phase 2 で使用
    ├── board/ra6m5_ek/        EK-RA6M5 ボード支援
    └── script/fsp.ld          GCC 用リンカスクリプト雛形
```

## 実施手順

1. ブランチ `feat/ek_ra6m5_phase1` を切る．
2. e² studio のパックディレクトリから 3 つの pack を抽出:
   - `Renesas.RA.6.1.0.pack` — FSP 本体
   - `Renesas.RA_mcu_ra6m5.6.1.0.pack` — RA6M5 MCU 固有 BSP + リンカスクリプト
   - `Renesas.RA_board_ra6m5_ek.6.1.0.pack` — EK-RA6M5 ボード支援
3. `arch/arm_m_gcc/ra6m5_fsp/fsp/` 配下に必要部分のみ配置 (詳細は README §3.1)．`lib/` (precompiled .a) と未使用 `*.template` は除外．
4. `chip_config.h` を H5 版に倣って作成．`#include "bsp_api.h"` のみ．
5. `Makefile.chip` に下記を定義:
   - `CHIPDIR`, `FSPDIR`
   - `COPTS += -mcpu=cortex-m33 -mthumb -mlittle-endian`
   - `CDEFS += -D_RENESAS_RA_ -D_RA_CORE=CM33 -D_RA_ORDINAL=1`
   - `FPU_ARCH_OPT = fpv5-sp-d16`, `FPU_ARCH_MACRO = __TARGET_FPU_FPV5_SP`
   - `INCLUDES`: `$(CHIPDIR)`, `$(FSPDIR)/inc`, `$(FSPDIR)/inc/api`, `$(FSPDIR)/inc/instances`, `$(FSPDIR)/src/bsp/cmsis/Device/RENESAS/Include`, `$(FSPDIR)/src/bsp/mcu/all`, `$(FSPDIR)/src/bsp/mcu/ra6m5`
   - `KERNEL_DIR += $(CHIPDIR) $(FSPDIR)/src/bsp/mcu/all $(FSPDIR)/src/bsp/cmsis/Device/RENESAS/Source`
   - `KERNEL_COBJS += bsp_clocks.o bsp_common.o bsp_delay.o bsp_group_irq.o bsp_guard.o bsp_io.o bsp_irq.o bsp_macl.o bsp_register_protection.o bsp_sbrk.o bsp_security.o system.o`
   - `include $(SRCDIR)/arch/$(PRC)_$(TOOL)/common/Makefile.prc`
6. README に同梱範囲・責務分担・既知制限を記述．
7. コミット (2 コミット: CLAUDE.md と ra6m5_fsp 骨格)．
8. codex に構成レビュー依頼．

## 検証 / 終了条件

- [ ] 上記成果物が `feat/ek_ra6m5_phase1` ブランチにコミット済み．
- [ ] codex レビューで "Recommended next move" が「Phase 2 に進める」または「軽微な修正後に進める」であること．Blocker が出た場合は Phase 1 を再着手．
- [ ] 本フェーズではコンパイルは行わない (Smart Configurator 生成物が無いため)．コンパイル検証は Phase 2 完了時に実施．

## リスク

| 項目 | 内容 | 緩和策 |
|---|---|---|
| FSP `system.c` の `SystemInit()` シグネチャが ATK2 `start.S` と非互換 | `void SystemInit(void)` で一致しているはずだが要確認 | Phase 2 着手前に codex で grep 確認 |
| FSP の弱定義 `Reset_Handler` / `NMI_Handler` 等が ATK2 ベクタと衝突 | `bsp_irq.c` などで weak alias がある可能性 | codex レビュー項目に含む |
| 同梱した BSP COBJS が依存ヘッダを `ra_cfg/` から探しに行く (`bsp_cfg.h` 等) | コンパイルは Phase 2 まで成立しないことを明記 | README §7 で明示済 |

## 後続フェーズへの引継

- Phase 2 が `target/ek_ra6m5_gcc/ra_cfg/` `ra_gen/` を整備した時点で，本層と組み合わせて全体ビルドが成立するようになる．
- FSP のドライバ追加 (例: `r_dtc`) が必要になった場合は，本層の `fsp/src/` 配下に上流 pack から追加コピーし，`Makefile.chip` の `KERNEL_COBJS` に追記．
