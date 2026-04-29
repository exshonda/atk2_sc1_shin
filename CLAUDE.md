# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

TOPPERS/ATK2 (AUTOSAR Kernel Version 2, SC1) ported from the original Nios2 distribution to **STMicroelectronics NUCLEO-H563ZI** (ARM Cortex-M33). The Nios2 target has been **removed** from this tree — only the NUCLEO-H563ZI target ships. The dispatcher and ARM port were modeled on TOPPERS/ASP3.

User-facing documentation (Japanese) is in [README.md](README.md), [arch/arm_m_gcc/common/README.md](arch/arm_m_gcc/common/README.md), [arch/arm_m_gcc/stm32h5xx_stm32cube/README.md](arch/arm_m_gcc/stm32h5xx_stm32cube/README.md), [target/nucleo_h563zi_gcc/README.md](target/nucleo_h563zi_gcc/README.md), and [cfg/cfg_py/README.md](cfg/cfg_py/README.md). Read those before guessing. Source-level docs in `doc/` describe the original ATK2 SC1 kernel.

## Common commands

All builds happen from the per-target build directory, **not** the repo root.

```sh
cd obj/obj_nucleo_h563zi
make -j4                  # default: USE_PY_CFG=1 (Python cfg)
make USE_PY_CFG=0 -j4     # use C++ cfg/cfg/cfg.exe (NOT shipped — see README §3)
make PYTHON=python3 -j4   # override Python interpreter
make clean
make flash                # OpenOCD program via STLink (requires openocd in PATH)
make debug                # arm-none-eabi-gdb against localhost:3333
```

Outputs land in the build directory: `atk2-sc1` (ELF), `atk2-sc1.srec`, `atk2-sc1.dump`, `atk2-sc1.map`, plus generator artifacts (`Os_Lcfg.c/h`, `Os_Cfg.h`, `cfg1_out.c`, `offset.h`).

`configure.py` regenerates `sample/Makefile` and template app files from `sample/` templates — it is rarely run for this target since `obj/obj_nucleo_h563zi/Makefile` is committed.

### cfg_py tests

```sh
pip install pytest
cd cfg/cfg_py
pytest -v                         # all
pytest -v tests/test_lexer.py     # single file
pytest -v -k integration_kernel   # by name
```

Integration tests under `cfg/cfg_py/tests/` run the actual pass1/pass2/pass3 against fixture ARXML and compare outputs to the C++ baseline; they are the canonical regression check for the Python port.

## High-level build pipeline (non-obvious)

The Makefile orchestrates the ATK2 generator (`cfg`) in three passes interleaved with C compilation. **`Os_Lcfg.timestamp` is the central pivot** — almost every `.o` has an order-only dependency on it.

1. **pass1**: `cfg --pass 1` reads `*.arxml` + `kernel_def.csv` → `cfg1_out.c`.
2. `cfg1_out.c` is compiled and linked (with `--no-gc-sections` so MAGIC_* symbols survive) into a host-checking ELF `cfg1_out`. `nm` and `objcopy` produce `cfg1_out.syms` and `cfg1_out.srec`.
3. **pass2**: `cfg --pass 2 -T target.tf` reads the srec/syms back and emits `Os_Lcfg.c`, `Os_Lcfg.h`, `Os_Cfg.h`, `cfg2_out.tf`. Touches `Os_Lcfg.timestamp` on success.
4. All application/sysmod/kernel `.o` files compile (they include the freshly generated headers).
5. Final link → `atk2-sc1` ELF. Then **pass3**: `cfg --pass 3 -T target_check.tf` validates the linked image against `target_check.tf` / `prc_check.tf` / `kernel_check.tf` using the final srec+syms.

If you change build rules, preserve the order-only deps in `obj/obj_nucleo_h563zi/Makefile` around line 377: `$(APPL_OBJS) $(SYSMOD_OBJS) $(CFG_OBJS) $(KERNEL_LIB_OBJS) $(KERNEL_AUX_COBJS): | Os_Lcfg.timestamp $(OBJDIR)`. `cfg1_out.o` and `start.o` (`HIDDEN_OBJS`) are deliberately excluded — adding them creates a cycle.

`USE_PY_CFG=1` (default) substitutes `python cfg/cfg_py/cfg.py` for `cfg/cfg/cfg`. The Python port reproduces all three passes and is byte-equivalent to the C++ output (`atk2-sc1.dump` matches). The C++ binary is **not** in the repo — `USE_PY_CFG=0` requires downloading [cfg-mingw-static-1_9_6.zip](https://www.toppers.jp/download.cgi/cfg-mingw-static-1_9_6.zip) and placing `cfg.exe` at `cfg/cfg/cfg.exe`.

## Python port (cfg_py)

`cfg/cfg_py/` is a stdlib-only Python port of the C++ generator (`cfg_1.9.4`). Module roles:

- `cfg.py` — CLI entry point + pass dispatch.
- `atk2_xml.py` — ARXML parser (uses `xml.etree.ElementTree`, no XSD validation; semantic checks live here: `validate_type`, `validate_multiplicity`, ref resolution).
- `atk2_pass1.py` / `atk2_pass2.py` / `atk2_pass3.py` — the three pass implementations.
- `atk2_bind.py` — binds the XML object tree into the .tf evaluation context (the `macro_processor` equivalent).
- `tf_lexer.py` / `tf_parser.py` / `tf_ast.py` / `tf_eval.py` / `tf_value.py` / `tf_builtin.py` / `tf_engine.py` — full implementation of the TOPPERS `.tf` template language.
- `gen_file.py` — cmp-then-mv file writer (matches C++ `cmp_mv` semantics so unchanged outputs do not bump mtimes).
- `srecord.py` — Motorola S-record reader for pass3.
- `pass1.py` / `pass2.py` — legacy ASP3 (.cfg/.trb) handling; **not used** by ATK2 builds.

XSD files (`AUTOSAR_4-0-3_STRICT.xsd`, `xml.xsd`) that shipped with the C++ build are intentionally absent — see [cfg/cfg_py/README.md](cfg/cfg_py/README.md) for the full rationale.

## Architecture layering

The kernel is layered (innermost → outermost):

| Layer | Path | Notes |
|---|---|---|
| Generic SC1 kernel | `kernel/` | Unmodified TOPPERS/ATK2 SC1 1.4.2. |
| System modules | `sysmod/` (banner, syslog, serial) + `library/` | |
| Processor (CPU) | `arch/arm_m_gcc/common/` | ARMv7-M / ARMv8-M common; new in this port. |
| Chip | `arch/arm_m_gcc/stm32h5xx_stm32cube/` | STM32H5xx + STM32Cube HAL Driver. |
| Target (board) | `target/nucleo_h563zi_gcc/` | NUCLEO-H563ZI: linker script, USART3, TIM2/TIM5 HW counter, STM32CubeIDE project. |
| Application | `sample/sample1.c` (+ `*.arxml`) | |

Each layer contributes `Makefile.{prc,chip,target}`, a `.tf` template (pass2 emit), a `_check.tf` (pass3 verify), a `_def.csv` (pass1 token table), `_rename.h` / `_unrename.h`, and a `_cfg1_out.h` stub used when linking the pass1 host-side checker.

The dispatcher (in `arch/arm_m_gcc/common/prc_support.S` + `prc_config.{c,h}`) follows ASP3's design:
- Task-context dispatch goes through `do_dispatch` (saves r4-r11/LR/PSP into TCB) → `dispatcher_0` → either `svc #0` for EXC_RETURN-tagged resumption or `dispatcher_1` for fresh/normal Thread-mode resume.
- Interrupt-exit dispatch is deferred to **PendSV at priority 0xFF** (tail-chain after all ISRs).
- `BASEPRI` is the OS interrupt mask (`tmin_basepri = 0x10`); `PRIMASK` is full-mask. ARMv6-M is unsupported (no BASEPRI). TrustZone Secure mode is not supported.

FPU support is selected by `FPU_USAGE` in `Makefile.target`: `FPU_LAZYSTACKING` (recommended/default) / `FPU_NO_LAZYSTACKING` / `FPU_NO_PRESERV` / unset (soft float). `FPCCR_INIT` is selected accordingly in `arm_m.h`.

## ARXML and the configuration model

The application's static OS configuration (tasks, alarms, counters, ISRs, resources) lives in `*.arxml` files under `sample/` and `target/nucleo_h563zi_gcc/` (`target_serial.arxml`, `target_hw_counter.arxml`). The `CFGNAME` make variable is the space-separated list of arxml basenames (without extension) consumed by `cfg`. To add a new ISR or resource, edit the relevant arxml and rebuild — the generator regenerates `Os_Lcfg.c/h` and `Os_Cfg.h` from those.

`utils/abrex/abrex.py` (Python port of `abrex.rb`) converts a YAML description (`sample1.yaml`) into the equivalent ARXML — useful for hand-authoring. Requires PyYAML.

## 開発項目
- EK-RA6M5 向けの依存部を開発する
  - コア依存部（./arch/arm_m_gcc/common）は変更せずにそのまま使用する
  - RenesasのFSPドライバを使ってよい
    - **FSP ソースはリポジトリに同梱しない**．`configuration.xml` のみコミットし，clone 後にユーザが `rascc.exe --generate` で `target/<TARGET>/fsp/ra/` `target/<TARGET>/fsp/ra_cfg/` `target/<TARGET>/fsp/ra_gen/` を生成する．手順は [`arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md`](arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md) 参照．
  - 将来的に同じ Cortex-M33 を搭載した他の RA シリーズ (RA4M2/M3, RA6M4, RA6T2, RA8M1 等) に展開可能な構成とする．chip 層 `arch/arm_m_llvm/ra_fsp/` は RA ファミリ汎用．`MCU_GROUP` (`ra6m5`/`ra6m4`/`ra4m2` 等) と `CORE_CPU` (`cortex-m33`/`cortex-m85`) を `Makefile.target` で指定する設計．

### EK-RA6M5 ポート: 重要な構成情報

- **コンパイラ**: **ARM LLVM (Arm Toolchain for Embedded; ATfE) 21.1.1**．Renesas e² studio v2025-12 に同梱．`C:/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin/clang.exe`．`--target=arm-none-eabi` で ARM ELF を生成．
- **プロセッサ依存部**: `arch/arm_m_llvm/common/` (LLVM 用 Makefile.prc のみ)．**ソース本体 (`start.S`, `prc_config.{c,h}`, `prc_support.S` 等) は `arch/arm_m_gcc/common/` を vpath 経由で再利用** (`arch/arm_m_gcc/common/` は変更しない方針を維持)．
- **チップ依存部**: `arch/arm_m_llvm/ra_fsp/` (RA ファミリ汎用; FSP 同梱しない)．`MCU_GROUP` 変数で個別チップに対応 (例: `ra6m5`, `ra6m4`, `ra4m2`, `ra6t2`)．`CORE_CPU` 上書きで Cortex-M85 (RA8) も対応可．
- **ターゲット依存部**: `target/ek_ra6m5_llvm/` (EK-RA6M5 ボード固有)
- **ビルドディレクトリ**: `obj/obj_ek_ra6m5/` (Phase 3 で作成予定)
- **FSP**: バージョン 6.4.0 (Renesas Smart Configurator sc_v2025-12)．`C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rascc.exe`．
- **シリアル (ログ出力)**: **SCI3 経由 Arduino D0/D1**．EK-RA6M5 の J24 ヘッダ Pin 0 (RX = P303 = RXD3) / Pin 1 (TX = P302 = TXD3)．115200 bps, 8N1．外付け USB-Serial 変換アダプタを J24 に接続して使う想定．J-Link OB VCOM (SCI9) は使用しない．
- **clone 後の必須作業**: `rascc --generate target/ek_ra6m5_llvm/fsp/configuration.xml` を実行すること．生成物 `ra/` `ra_cfg/` `ra_gen/` は `.gitignore` で除外．手順詳細は [`arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md`](arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md)．
- **段階的実装計画**: `phase1.md`〜`phase6.md` 参照．現状は Phase 2-A (Smart Configurator baseline 取込) 待ち．