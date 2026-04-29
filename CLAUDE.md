# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

TOPPERS/ATK2 (AUTOSAR Kernel Version 2, SC1) ported from the original Nios2 distribution to **two ARM Cortex-M33 boards**:

- **STMicroelectronics NUCLEO-H563ZI** (STM32H563ZI) — original ARM port; built with arm-none-eabi-gcc.
- **Renesas EK-RA6M5** (R7FA6M5BH) — second port; built with ATfE clang 21.1.1 + Renesas FSP 6.4.0.

The Nios2 target has been **removed** from this tree. The dispatcher and ARM port were modeled on TOPPERS/ASP3.

User-facing documentation (Japanese) is in:

- [README.md](README.md) — repository top-level
- [arch/arm_m_gcc/common/README.md](arch/arm_m_gcc/common/README.md) — ARM-M PRC layer (shared)
- [arch/arm_m_gcc/stm32h5xx_stm32cube/README.md](arch/arm_m_gcc/stm32h5xx_stm32cube/README.md) — STM32H5 chip layer
- [arch/arm_m_llvm/ra_fsp/README.md](arch/arm_m_llvm/ra_fsp/README.md) — RA + FSP chip layer
- [target/nucleo_h563zi_gcc/README.md](target/nucleo_h563zi_gcc/README.md) — NUCLEO-H563ZI board
- [target/ek_ra6m5_llvm/README.md](target/ek_ra6m5_llvm/README.md) — EK-RA6M5 board
- [cfg/cfg_py/README.md](cfg/cfg_py/README.md) — cfg Python port

Read those before guessing. Source-level docs in `doc/` describe the original ATK2 SC1 kernel.

## Toolchain paths (Windows / MSYS2 bash)

`make` and ATfE clang are **not on the default `PATH`** in this environment.
Locations (all use forward-slash MSYS-style for bash):

| Tool | Path | Used for |
|---|---|---|
| GNU Make 4.4 | `/c/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/eclipse/plugins/com.renesas.ide.exttools.gnumake.win32.x86_64_4.3.1.v20240909-0854/mk/make.exe` | Both targets |
| `arm-none-eabi-gcc` 13.x | `/c/SW/ST/STM32CubeCLT_1.18.0/GNU-tools-for-STM32/bin/` (already on `PATH`) | NUCLEO-H563ZI |
| ATfE 21.1.1 (`clang.exe`) | `/c/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin/` | EK-RA6M5 |
| `rascc.exe` (FSP generator) | `/c/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rascc.exe` | EK-RA6M5 (one-shot, post-clone) |
| J-Link CLI | `/c/Program Files/SEGGER/JLink_V920/JLink.exe` (already on `PATH`) | EK-RA6M5 flashing |

One-liner to set up the shell for an EK-RA6M5 build (assumes you've
already run `rascc --generate target/ek_ra6m5_llvm/fsp/configuration.xml`
once after clone — see "開発項目 / EK-RA6M5 ポート" below):

```sh
MAKE='/c/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/eclipse/plugins/com.renesas.ide.exttools.gnumake.win32.x86_64_4.3.1.v20240909-0854/mk/make.exe'
export PATH="/c/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin:$PATH"
cd obj/obj_ek_ra6m5 && "$MAKE" -j4
```

NUCLEO-H563ZI build needs only `MAKE` exported (`arm-none-eabi-gcc` is
already on `PATH` from `STM32CubeCLT`):

```sh
MAKE='/c/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/eclipse/plugins/com.renesas.ide.exttools.gnumake.win32.x86_64_4.3.1.v20240909-0854/mk/make.exe'
cd obj/obj_nucleo_h563zi && "$MAKE" -j4
```

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

The kernel is layered (innermost → outermost). PRC sources live exclusively in `arch/arm_m_gcc/common/` and are reused by both targets — the LLVM target picks them up via vpath instead of duplicating:

| Layer | NUCLEO-H563ZI (gcc) | EK-RA6M5 (llvm) |
|---|---|---|
| Generic SC1 kernel | `kernel/` (unmodified TOPPERS/ATK2 SC1 1.4.2) | (same) |
| System modules | `sysmod/` (banner, syslog, serial) + `library/` | (same) |
| Processor (CPU) sources | `arch/arm_m_gcc/common/` | (same; vpath from `arch/arm_m_llvm/common/Makefile.prc`) |
| Processor (CPU) toolchain glue | `arch/arm_m_gcc/common/Makefile.prc` | `arch/arm_m_llvm/common/Makefile.prc` |
| AUTOSAR Compiler abstraction | `arch/gcc/{Compiler.h,Compiler_Cfg.h}` | `arch/llvm/{Compiler.h,Compiler_Cfg.h}` (#includes the gcc one) |
| Chip | `arch/arm_m_gcc/stm32h5xx_stm32cube/` (HAL Driver bundled) | `arch/arm_m_llvm/ra_fsp/` (FSP **not** bundled — `rascc --generate` post-clone) |
| Target (board) | `target/nucleo_h563zi_gcc/` (USART3, TIM2/TIM5 HW counter, STM32CubeIDE project) | `target/ek_ra6m5_llvm/` (SCI7, GPT320/GPT321 HW counter, e² studio debug-only project) |
| Build directory | `obj/obj_nucleo_h563zi/` | `obj/obj_ek_ra6m5/` |
| Application | `sample/sample1.c` (+ `*.arxml`) | (same) |

Each layer contributes `Makefile.{prc,chip,target}`, a `.tf` template (pass2 emit), a `_check.tf` (pass3 verify), a `_def.csv` (pass1 token table), `_rename.h` / `_unrename.h`, and a `_cfg1_out.h` stub used when linking the pass1 host-side checker.

**Per-chip definitions** (live in chip layer, **not** in PRC layer):

- C macros `TMIN_INTNO` / `TMAX_INTNO` / `TNUM_INT` / `TBITW_IPRI` are defined in each `chip_config.h` (STM32H5: 16/147/132/4; RA6M5: 16/111/96/4).
- `.tf` template variables `INTNO_VALID` / `INTNO_CONTROLLABLE` / `TNUM_INTPRI` / `INTNO_CREISR2_VALID` are defined in each `chip.tf`, included from `target.tf` **before** `prc.tf`.

The dispatcher (in `arch/arm_m_gcc/common/prc_support.S` + `prc_config.{c,h}`) follows ASP3's design:
- Task-context dispatch goes through `do_dispatch` (saves r4-r11/LR/PSP into TCB) → `dispatcher_0` → either `svc #0` for EXC_RETURN-tagged resumption or `dispatcher_1` for fresh/normal Thread-mode resume.
- Interrupt-exit dispatch is deferred to **PendSV at priority 0xFF** (tail-chain after all ISRs).
- `BASEPRI` is the OS interrupt mask (`tmin_basepri = 0x10`); `PRIMASK` is full-mask. ARMv6-M is unsupported (no BASEPRI). TrustZone Secure mode is not supported.

FPU support is selected by `FPU_USAGE` in `Makefile.target`: `FPU_LAZYSTACKING` (recommended/default) / `FPU_NO_LAZYSTACKING` / `FPU_NO_PRESERV` / unset (soft float). `FPCCR_INIT` is selected accordingly in `arm_m.h`.

## ARXML and the configuration model

The application's static OS configuration (tasks, alarms, counters, ISRs, resources) lives in `*.arxml` files under `sample/` and the per-target directory:

- H5: `target/nucleo_h563zi_gcc/target_serial.arxml`, `target_hw_counter.arxml`
- RA6M5: `target/ek_ra6m5_llvm/target_serial.arxml`, `target_hw_counter.arxml`

The `CFGNAME` make variable is the space-separated list of arxml basenames (without extension) consumed by `cfg`. To add a new ISR or resource, edit the relevant arxml and rebuild — the generator regenerates `Os_Lcfg.c/h` and `Os_Cfg.h` from those.

**INTNO numbering**: ATK2 INTNO is the **ARM Cortex-M exception number**, i.e. `IRQn + 16`. NVIC slot 0 → INTNO 16, slot 1 → INTNO 17, etc.

- **STM32H5**: each NVIC slot is hard-wired to a specific peripheral (USART3 = IRQ60 → INTNO 76).
- **RA6M5**: each NVIC slot is **dynamically routable** via the ICU.IELSR register. Smart Configurator decides which RA event (e.g. `SCI7_RXI`, `GPT0_OVERFLOW`) sits in which slot, then writes that mapping to `ra_gen/vector_data.c`'s `g_interrupt_event_link_select[]` array. `target_irq_data.c` (target layer) extracts that array and `target_initialize()` copies it into `R_ICU->IELSR[]` at boot. **The arxml's INTNO must match the slot index Smart Configurator assigned, not a fixed peripheral number.**

`utils/abrex/abrex.py` (Python port of `abrex.rb`) converts a YAML description (`sample1.yaml`) into the equivalent ARXML — useful for hand-authoring. Requires PyYAML.

## Common pitfalls

### Both targets

- **`Os_Lcfg.timestamp` is the central pivot** — almost every `.o` has an order-only dependency on it (see "High-level build pipeline" above). Adding `cfg1_out.o` or `start.o` to that dependency list creates a cycle.
- **PendSV must be priority 0xFF** for tail-chain interrupt-exit dispatch. Other ISRs must be ≥ `tmin_basepri` (0x10).
- **TrustZone (TZEN/Secure state)**: every target must define exactly one of `TOPPERS_TZ_NS` / `TOPPERS_TZ_S` in `Makefile.target`'s `CDEFS`. `arm_m.h` `#error`s if neither or both are set. Different boards land on different sides:
  - H5 (TZEN=0): `TOPPERS_TZ_NS` → `EXC_RETURN = 0xFFFFFFBC`
  - RA6M5 (FSP "Flat Non-TrustZone Project", but Full Secure at runtime): `TOPPERS_TZ_S` → `EXC_RETURN = 0xFFFFFFFD`

### NUCLEO-H563ZI (gcc)

- Microsoft Store Python doesn't work from STM32CubeIDE — see [target/nucleo_h563zi_gcc/README.md §9](target/nucleo_h563zi_gcc/README.md).
- VTOR programming order: `prc_initialize()` writes ATK2's `kernel_vector_table` to VTOR after FSP/CMSIS `SystemInit()` — never reorder.

### EK-RA6M5 (llvm + FSP)

- **FSP source is not in the repo**. Run `rascc --generate target/ek_ra6m5_llvm/fsp/configuration.xml` once after clone. `configuration.xml` is the source-of-truth; `ra/`, `ra_cfg/`, `ra_gen/` are gitignored regenerable output. Smart Configurator (e² studio GUI or standalone) is required to re-edit `configuration.xml`.
- **`vector_data.c` is intentionally excluded** from `KERNEL_COBJS` in `Makefile.target`. FSP-generated `vector_data.c` ships both `g_vector_table[]` (collides with ATK2's vector table) and `g_interrupt_event_link_select[]` (mandatory). Solution: `target_irq_data.c` re-extracts just the IELSR array.
- **Option Setting Memory** (OFS0 / OFS1 / OSIS) is placed by the linker script (`r7fa6m5bh.ld`) into `.option_setting_*` sections from `bsp_linker.c` (FSP).
- **OFS1.TZEN=0 but Secure mode at runtime**: device boots into Secure state even though TrustZone is "disabled" at the option-byte level. `EXC_RETURN` must reflect this (`TOPPERS_TZ_S` → ES=1, S=1 = `0xFFFFFFFD`). `EXC_RETURN=0xFFFFFFBD` (ES=1 but S=0) raises SFSR.INVTRAN HardFault.
- **ATfE clang + lld doubles the Thumb bit** in static initializers like `(uint32)func + 1` (the linker auto-sets LSB=1 on R_ARM_ABS32 against a Thumb function symbol). The build's Makefile post-processes `Os_Lcfg.c` with a `sed -i` to strip the `+ 1`. Don't change `prc.tf` to drop the `+ 1` — H5 (gcc) needs it.
- **ICU IELSR.IR must be cleared** in each ISR after handling, otherwise the interrupt re-enters in a tight loop. Wrappers in `target_config.c` and `target_hw_counter.c` call `R_BSP_IrqStatusClear()` accordingly.

## 開発項目
- EK-RA6M5 向けの依存部を開発する  **(Phase 1〜5 完了; Phase 6 ドキュメント整備中)**
  - コア依存部（./arch/arm_m_gcc/common）は変更せずにそのまま使用する
  - Renesas の FSP ドライバを使ってよい
    - **FSP ソースはリポジトリに同梱しない**．`configuration.xml` のみコミットし，clone 後にユーザが `rascc.exe --generate` で `target/<TARGET>/fsp/ra/` `target/<TARGET>/fsp/ra_cfg/` `target/<TARGET>/fsp/ra_gen/` を生成する．手順は [`arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md`](arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md) 参照．
  - chip 層 `arch/arm_m_llvm/ra_fsp/` は **Cortex-M33 + 96-slot ICU** を持つ RA を対象．動作確認は RA6M5 のみだが，RA4M2/M3, RA4E1/E2, RA6M4, RA6T2 への流用は配線変更のみで可と推定 (未確認)．**RA8 (128-slot) と RA2 (Cortex-M23) は対象外**．`MCU_GROUP` (`ra6m5`/`ra6m4`/`ra4m2` 等) は `Makefile.target` で指定．

### EK-RA6M5 ポート: 重要な構成情報

- **コンパイラ**: **ARM LLVM (Arm Toolchain for Embedded; ATfE) 21.1.1**．Renesas e² studio v2025-12 に同梱．`C:/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin/clang.exe`．`--target=arm-none-eabi` で ARM ELF を生成．
- **プロセッサ依存部**: `arch/arm_m_llvm/common/` (LLVM 用 Makefile.prc のみ)．**ソース本体 (`start.S`, `prc_config.{c,h}`, `prc_support.S` 等) は `arch/arm_m_gcc/common/` を vpath 経由で再利用** (`arch/arm_m_gcc/common/` は変更しない方針を維持)．
- **AUTOSAR Compiler 抽象**: `arch/llvm/` (`Compiler.h`, `Compiler_Cfg.h`) — clang 用ブリッジ層．`arch/gcc/` の同名ファイルを `#include` で取り込む．clang は `__inline__` `__asm__ volatile` `__attribute__((__noreturn__))` 等 GCC 互換属性を受け入れるためそのまま動く．LLVM 固有の差異が必要になったら本層で override．
- **チップ依存部**: `arch/arm_m_llvm/ra_fsp/` (Cortex-M33 + 96-slot ICU + FSP 6.4.0; FSP 同梱しない)．`MCU_GROUP` 変数で個別チップに対応 (例: `ra6m5`, `ra6m4`, `ra4m2`, `ra6t2`)．
- **ターゲット依存部**: `target/ek_ra6m5_llvm/` (EK-RA6M5 ボード固有)
- **ビルドディレクトリ**: `obj/obj_ek_ra6m5/`
- **FSP**: バージョン 6.4.0 (Renesas Smart Configurator sc_v2025-12)．`C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rascc.exe`．
- **シリアル (ログ出力)**: **SCI7 経由 Arduino D0/D1**．EK-RA6M5 の J24 ヘッダ Pin 0 (RX = P614 = RXD7) / Pin 1 (TX = P613 = TXD7)．115200 bps, 8N1．外付け USB-Serial 変換アダプタを J24 に接続して使う想定．J-Link OB VCOM (SCI9) は使用しない．
- **HW カウンタ**: GPT320 (Free Run, PCLKD/4 = 25 MHz tick) + GPT321 (One-Shot Alarm)．**`TIMER_CLOCK_HZ = 25 MHz`** (H5 の 1 MHz tick と異なる)．
- **EXC_RETURN**: `0xFFFFFFFD` (Full Secure: ES=1, S=1)．`Makefile.target` で `-DTOPPERS_TZ_S` を指定．OFS1.TZEN=0 (TrustZone 無効化) でも実行時は Secure state なので `S=1` が必須．
- **clone 後の必須作業**: `rascc --generate target/ek_ra6m5_llvm/fsp/configuration.xml` を実行すること．生成物 `ra/` `ra_cfg/` `ra_gen/` は `.gitignore` で除外．手順詳細は [`arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md`](arch/arm_m_llvm/ra_fsp/docs/fsp_setup.md)．
- **デバッグ**: e² studio v2025-12 の `target/ek_ra6m5_llvm/e2studio/sample_debug/` プロジェクトを `Existing Projects into Workspace` で取込むと J-Link 経由でデバッグできる (ビルドは make で済ませた前提；e² studio はデバッグ目的のみ)．詳細は [`target/ek_ra6m5_llvm/README.md` §9](target/ek_ra6m5_llvm/README.md)．
- **段階的実装計画**: [`arch/arm_m_llvm/ra_fsp/claude/phase1.md`](arch/arm_m_llvm/ra_fsp/claude/phase1.md)〜[`phase6.md`](arch/arm_m_llvm/ra_fsp/claude/phase6.md) 参照．Phase 1〜6 完了 (Phase 4-7 安定性試験は 10 分短縮版で実機 PASS)．