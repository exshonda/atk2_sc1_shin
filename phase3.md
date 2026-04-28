# Phase 3: ビルドディレクトリ作成と初回リンク

## 目的

`obj/obj_ek_ra6m5/Makefile` を作成し，pass1 → cfg1_out リンク → pass2 → 全 `.o` コンパイル → 最終リンク → pass3 の **ATK2 三段ビルドパイプラインを最後まで通す**．成果物 ELF (`atk2-sc1`) と書込み用 srec を生成する．

## 前提

- Phase 1 完了 (`arch/arm_m_gcc/ra6m5_fsp/`)．
- Phase 2 完了 (`target/ek_ra6m5_gcc/` 一式 + Smart Configurator 生成物)．

## 設計判断

- `obj/obj_nucleo_h563zi/Makefile` をベースに最小差分で作成．ATK2 ビルドフロー本体には触れない．
- `USE_PY_CFG=1` (デフォルト) で動作確認．Python 移植版 cfg を継続利用．
- 並列ビルド `-j4` を上限とする (Windows make の高並列度問題回避)．

## 成果物

```
obj/obj_ek_ra6m5/
└── Makefile                   ターゲット固有設定 (TARGET, CFGNAME, OMIT_HW_COUNTER 等)
```

ビルド成果 (`make -j4` で生成):
- `atk2-sc1` (ELF)
- `atk2-sc1.srec` (J-Link/OpenOCD 書込み用 S-record)
- `atk2-sc1.dump` (逆アセンブル)
- `atk2-sc1.map` (リンクマップ)
- `atk2-sc1.syms` (シンボル一覧)
- `Os_Lcfg.c/h`, `Os_Cfg.h`, `cfg1_out.c`, `offset.h` (cfg 生成物)

## 実施手順

1. `obj/obj_nucleo_h563zi/Makefile` を `obj/obj_ek_ra6m5/Makefile` に複製．
2. 主要変更点:
   - `TARGET = ek_ra6m5_gcc`
   - `CFGNAME = sample1` + `target_serial` + `target_hw_counter` (H5 と同じ)
   - その他は基本そのまま (`SRCDIR = ../..`, `OBJDIR = objs`, `USE_PY_CFG ?= 1` 等)
3. `flash` ターゲットを EK-RA6M5 用に修正:
   - J-Link 経由 (推奨): `JLinkExe -device R7FA6M5BH -if SWD -speed 4000 -CommanderScript ...`
   - もしくは OpenOCD: `openocd -f interface/cmsis-dap.cfg -f target/renesas_ra6m5.cfg -c "program $(OBJNAME).srec verify reset exit"`
   - EK-RA6M5 の J-Link OB を使う場合は J-Link 推奨
4. `debug` ターゲットも同様に J-Link GDB Server に切替え (`JLinkGDBServer -device R7FA6M5BH -if SWD &; arm-none-eabi-gdb ...`)．
5. **初回ビルド**: `cd obj/obj_ek_ra6m5 && make -j4`
6. エラー対処の典型:
   - **未解決シンボル `g_vector_table[]` 重複定義** → `vector_data.c` がビルド対象に入っている．`Makefile.target` で除外確認．
   - **`bsp_cfg.h` not found** → Phase 2 で `INCLUDES` に `ra_cfg/fsp_cfg` を追加し忘れ．
   - **`R7FA6M5BH.h` not found** → Phase 1 の `Makefile.chip` で `cmsis/Device/RENESAS/Include` パス追加し忘れ．
   - **`__bss_start__` 未定義** → リンカスクリプトのシンボルが ATK2 `start.S` の参照名と不一致．`r7fa6m5bh.ld` で名前合わせ．
   - **`__libc_init_array` 未定義** → `LIBS` に `-lgcc -lc -lnosys` あるか確認 (`Makefile.prc` 既定で OK)．
   - **pass3 で `magic number is not found`** → `cfg1_out` リンクで `--no-gc-sections` (`CFG1_OUT_LDFLAGS`) が効いているか確認．
   - **FSP `Default_Handler` と ATK2 ベクタの衝突** → `Os_Lcfg.c` 生成のベクタが上書きされているはず．診断は `nm $(OBJFILE) | grep -E "Reset_Handler|Default_Handler"`．
7. ELF が出たら検証:
   - `arm-none-eabi-objdump -h atk2-sc1` で `.isr_vector @ 0x00000000`, `.text`, `.data`, `.bss` 配置確認．
   - `arm-none-eabi-size atk2-sc1` で text/data/bss サイズが妥当か (text < 1 MB 程度)．
   - `Os_Cfg.h` を開き，`tmin_basepri = 0x10`，`tnum_isr2`，`tnum_alm` 等が想定通りか目視確認．
8. **コミット**: `obj/obj_ek_ra6m5: Makefile 追加 + 初回ビルド成功`

## 検証 / 終了条件

- [ ] `cd obj/obj_ek_ra6m5 && make -j4` がエラーなく完走．
- [ ] `atk2-sc1`, `atk2-sc1.srec`, `atk2-sc1.dump`, `atk2-sc1.map` 生成．
- [ ] pass3 が "0 errors" で完了．
- [ ] `arm-none-eabi-size atk2-sc1` の出力が妥当．
- [ ] **実機書込みは Phase 4 で実施**．Phase 3 はあくまで「ホストでビルドが通る」まで．

## リスク

| 項目 | 内容 | 緩和策 |
|---|---|---|
| FSP `bsp_irq.c` の弱定義シンボルが ATK2 ベクタテーブルと整合しない | `nm` でシンボル衝突確認．必要なら `bsp_irq.c` を除外 | Phase 1 codex レビューで先行確認 |
| FSP の `system.c` `SystemInit()` 内で VTOR を書換えている | ATK2 ベクタが上書きされ動作不能になる．`SCB->VTOR = ...` の有無を grep | Phase 1 codex レビュー |
| RA6M5 の Option Setting Memory (OFS0/OFS1/OSIS など) を初期化していないため起動しない | リンカスクリプトに `.option_setting` セクションを設置．FSP `bsp_linker.c` がデフォルト値を提供 | Phase 3 ビルド失敗時に確認 |
| Windows make の高並列度問題 | `-j4` 上限固定．`Makefile` のデフォルト記述で誘導 | Makefile に注記 |

## 後続フェーズへの引継

- Phase 4 が本フェーズ生成物 (`atk2-sc1.srec`) を実機 EK-RA6M5 に書込み，ブリングアップを行う．
