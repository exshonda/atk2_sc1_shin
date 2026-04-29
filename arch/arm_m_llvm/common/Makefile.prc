#
#  TOPPERS ATK2
#      Toyohashi Open Platform for Embedded Real-Time Systems
#      Automotive Kernel Version 2
#
#  Copyright (C) 2008-2017 by Center for Embedded Computing Systems
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#  Copyright (C) 2026 by Center for Embedded Computing Systems
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#
#  上記著作権者は，以下の(1)〜(4)の条件を満たす場合に限り，本ソフトウェ
#  ア（本ソフトウェアを改変したものを含む．以下同じ）を使用・複製・改
#  変・再配布（以下，利用と呼ぶ）することを無償で許諾する．
#
#  本ソフトウェアは，無保証で提供されているものである．
#

#
#  Makefile のプロセッサ依存部 (ARM Cortex-M + ARM LLVM)
#
#  Renesas RA / その他 Cortex-M33 系 SoC を ARM LLVM (Arm Toolchain for
#  Embedded; ATfE) でビルドするための Makefile．
#
#  ソースコード本体 (start.S / prc_config.{c,h} / prc_support.S 等) は
#  arch/arm_m_gcc/common/ 配下のものを **そのまま再利用** する．
#  (TOPPERS 共通 Cortex-M コードを 1 箇所で管理するため．)
#  本層は LLVM 用のビルド設定 (CC/AR/LD コマンド名，パス) のみを定義する．
#

#
#  プロセッサ名，開発環境名の定義
#
PRC  = arm_m
TOOL = llvm

#
#  プロセッサ依存部ディレクトリ名の定義
#
#  PRCDIR    : 本ディレクトリ (空; 共通ソースは PRC_SRC_DIR を参照)
#  PRC_SRC_DIR : ソース本体 (start.S 等) の場所．arch/arm_m_gcc/common/ を流用．
#
PRCDIR     = $(SRCDIR)/arch/$(PRC)_$(TOOL)/common
PRC_SRC_DIR = $(SRCDIR)/arch/$(PRC)_gcc/common

#
#  ARM LLVM (ATfE) ツールチェーンのデフォルトパス
#
#  Renesas e² studio v2025-12 同梱の場合:
#    C:/Renesas/RA/e2studio_v2025-12_fsp_v6.4.0/toolchains/llvm_arm/ATfE-21.1.1-Windows-x86_64/bin/
#  ユーザは下記いずれかで指定可能:
#    1. PATH にバイナリを通す (推奨)
#    2. make ATFE_PREFIX="<full path>/" でフルパス指定
#    3. obj/.../Makefile に直書き
#
ATFE_PREFIX ?=

#
#  LLVM ツール群．clang は --target=arm-none-eabi で ARM ELF を出力．
#
CC      = $(ATFE_PREFIX)clang --target=arm-none-eabi
CXX     = $(ATFE_PREFIX)clang++ --target=arm-none-eabi
AS      = $(ATFE_PREFIX)clang --target=arm-none-eabi
LD      = $(ATFE_PREFIX)clang --target=arm-none-eabi
AR      = $(ATFE_PREFIX)llvm-ar
NM      = $(ATFE_PREFIX)llvm-nm
RANLIB  = $(ATFE_PREFIX)llvm-ranlib
OBJCOPY = $(ATFE_PREFIX)llvm-objcopy
OBJDUMP = $(ATFE_PREFIX)llvm-objdump
LINK    = $(CC)

#
#  ソース検索パスの設定 (arch/arm_m_gcc/common/ の .S/.c を解決)
#
vpath %.c $(PRC_SRC_DIR)
vpath %.S $(PRC_SRC_DIR)

#
#  コンパイルオプション
#
#  -I$(SRCDIR)/arch/llvm: AUTOSAR Compiler 抽象化 (Compiler.h, Compiler_Cfg.h)
#                        の LLVM 用ブリッジ．実体は arch/gcc/ を取込んでいる
#                        が，clang ビルドからは arch/llvm/ を経由する命名
#                        にしてある (arch/gcc/ を直接参照すると誤読される)．
#
INCLUDES := $(INCLUDES) -I$(PRC_SRC_DIR) -I$(SRCDIR)/arch/llvm
COPTS    := $(COPTS) -fno-common -ffunction-sections -fdata-sections
LDFLAGS  := $(LDFLAGS) -Wl,--gc-sections
#
#  ATfE clang は picolibc / newlib が同梱．デフォルトで適切なものがリンクされる．
#  -nostdlib は ATK2 が start.S で C ランタイム初期化する都合上で残す．
#
LIBS     := $(LIBS) -lc -lm

#
#  FPU の設定 (arch/arm_m_gcc/common/Makefile.prc と同じロジック)
#
#  FPU_USAGE で 3 通りの動作モードを切り替える (ASP3 と同じ識別子):
#    FPU_NO_PRESERV     : FPU を有効にするが OS は s16-s31 を保存/復帰しない．
#    FPU_NO_LAZYSTACKING: FPU を有効にし，OS が s16-s31 を保存/復帰する．
#    FPU_LAZYSTACKING   : 同上 + HW Lazy Stacking 有効．
#  FPU_USAGE 未指定の場合は soft-float (-mfloat-abi=soft) でビルドする．
#  -mfloat-abi のデフォルトは softfp．
#
ifeq ($(FPU_ABI),)
  FPU_ABI = softfp
endif

ifeq ($(FPU_USAGE),FPU_NO_PRESERV)
  COPTS := $(COPTS) -mfloat-abi=$(FPU_ABI) -mfpu=$(FPU_ARCH_OPT)
  LDFLAGS := $(LDFLAGS) -mfloat-abi=$(FPU_ABI) -mfpu=$(FPU_ARCH_OPT)
  CDEFS := $(CDEFS) -D$(FPU_ARCH_MACRO) \
                    -DTOPPERS_FPU_ENABLE -DTOPPERS_FPU_NO_PRESERV
else ifeq ($(FPU_USAGE),FPU_NO_LAZYSTACKING)
  COPTS := $(COPTS) -mfloat-abi=$(FPU_ABI) -mfpu=$(FPU_ARCH_OPT)
  LDFLAGS := $(LDFLAGS) -mfloat-abi=$(FPU_ABI) -mfpu=$(FPU_ARCH_OPT)
  CDEFS := $(CDEFS) -D$(FPU_ARCH_MACRO) \
                    -DTOPPERS_FPU_ENABLE -DTOPPERS_FPU_NO_LAZYSTACKING \
                    -DTOPPERS_FPU_CONTEXT
else ifeq ($(FPU_USAGE),FPU_LAZYSTACKING)
  COPTS := $(COPTS) -mfloat-abi=$(FPU_ABI) -mfpu=$(FPU_ARCH_OPT)
  LDFLAGS := $(LDFLAGS) -mfloat-abi=$(FPU_ABI) -mfpu=$(FPU_ARCH_OPT)
  CDEFS := $(CDEFS) -D$(FPU_ARCH_MACRO) \
                    -DTOPPERS_FPU_ENABLE -DTOPPERS_FPU_LAZYSTACKING \
                    -DTOPPERS_FPU_CONTEXT
else
  COPTS := $(COPTS) -mfloat-abi=soft
  LDFLAGS := $(LDFLAGS) -mfloat-abi=soft
endif

#
#  cfg1_out.exe (pass2 用) のリンク時はガベージコレクションを無効化
#  (理由は arch/arm_m_gcc/common/Makefile.prc 参照)
#
CFG1_OUT_LDFLAGS = -Wl,--no-gc-sections

#
#  カーネルに関する定義 (arch/arm_m_gcc/common/ のソースを再利用)
#
KERNEL_DIR     := $(KERNEL_DIR) $(PRC_SRC_DIR)
KERNEL_ASMOBJS := $(KERNEL_ASMOBJS) prc_support.o
KERNEL_COBJS   := $(KERNEL_COBJS) prc_config.o

#
#  スタートアップモジュールに関する定義
#  (arch/arm_m_gcc/common/start.S を流用)
#
HIDDEN_OBJS = start.o
HIDDEN_OBJS := $(addprefix $(OBJDIR)/, $(HIDDEN_OBJS))

$(HIDDEN_OBJS): $(OBJDIR)/%.o: %.S | $(OBJDIR)
	$(CC) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d $(CFLAGS) $(KERNEL_CFLAGS) $<

LDFLAGS := -nostdlib $(LDFLAGS)

#
#  ジェネレータ関係の依存
#
cfg1_out.c: $(PRC_SRC_DIR)/prc_def.csv
Os_Lcfg.timestamp: $(PRC_SRC_DIR)/prc.tf
offset.h: $(PRC_SRC_DIR)/prc_offset.tf

CFG_TABS := $(CFG_TABS) --cfg1-def-table $(PRC_SRC_DIR)/prc_def.csv
