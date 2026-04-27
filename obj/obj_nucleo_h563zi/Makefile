#
#  TOPPERS ATK2
#      Toyohashi Open Platform for Embedded Real-Time Systems
#      Automotive Kernel Version 2
#
#  Copyright (C) 2000-2003 by Embedded and Real-Time Systems Laboratory
#                              Toyohashi Univ. of Technology, JAPAN
#  Copyright (C) 2006-2017 by Center for Embedded Computing Systems
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#
#  上記著作権者は，以下の(1)〜(4)の条件を満たす場合に限り，本ソフトウェ
#  ア（本ソフトウェアを改変したものを含む．以下同じ）を使用・複製・改
#  変・再配布（以下，利用と呼ぶ）することを無償で許諾する．
#  (1) 本ソフトウェアをソースコードの形で利用する場合には，上記の著作
#      権表示，この利用条件および下記の無保証規定が，そのままの形でソー
#      スコード中に含まれていること．
#  (2) 本ソフトウェアを，ライブラリ形式など，他のソフトウェア開発に使
#      用できる形で再配布する場合には，再配布に伴うドキュメント（利用
#      者マニュアルなど）に，上記の著作権表示，この利用条件および下記
#      の無保証規定を掲載すること．
#  (3) 本ソフトウェアを，機器に組み込むなど，他のソフトウェア開発に使
#      用できない形で再配布する場合には，次のいずれかの条件を満たすこ
#      と．
#    (a) 再配布に伴うドキュメント（利用者マニュアルなど）に，上記の著
#        作権表示，この利用条件および下記の無保証規定を掲載すること．
#    (b) 再配布の形態を，別に定める方法によって，TOPPERSプロジェクトに
#        報告すること．
#  (4) 本ソフトウェアの利用により直接的または間接的に生じるいかなる損
#      害からも，上記著作権者およびTOPPERSプロジェクトを免責すること．
#      また，本ソフトウェアのユーザまたはエンドユーザからのいかなる理
#      由に基づく請求からも，上記著作権者およびTOPPERSプロジェクトを
#      免責すること．
#
#  本ソフトウェアは，AUTOSAR（AUTomotive Open System ARchitecture）仕
#  様に基づいている．上記の許諾は，AUTOSARの知的財産権を許諾するもので
#  はない．AUTOSARは，AUTOSAR仕様に基づいたソフトウェアを商用目的で利
#  用する者に対して，AUTOSARパートナーになることを求めている．
#
#  本ソフトウェアは，無保証で提供されているものである．上記著作権者お
#  よびTOPPERSプロジェクトは，本ソフトウェアに関して，特定の使用目的
#  に対する適合性も含めて，いかなる保証も行わない．また，本ソフトウェ
#  アの利用により直接的または間接的に生じたいかなる損害に関しても，そ
#  の責任を負わない．
#

#
#  ターゲットの指定（Makefile.target で上書きされるのを防ぐため）
#
all:

#
#  ターゲット略称の定義
#
TARGET = nucleo_h563zi_gcc

#
#  プログラミング言語の定義
#
SRCLANG = c

#
#  ソースファイルのディレクトリの定義
#
SRCDIR = ../..

#
#  オブジェクトファイル名の拡張子の設定（ELF形式）
#
#OBJEXT = elf

#
#  カーネルライブラリ（libkernel.a）のディレクトリ名
#
KERNEL_LIB =

#
#  カーネルを関数単位でコンパイルするかどうかの定義
#
KERNEL_FUNCOBJS =

#
#  トレースログを取得するかどうかの定義
#
ENABLE_TRACE =

#
#  ハードウェアカウンタを無効にするかどうかの定義
#
OMIT_HW_COUNTER =

#
#  トレースログに関する設定
#
ifeq ($(ENABLE_TRACE),true)
      CDEFS := $(CDEFS) -DTOPPERS_ENABLE_TRACE
      KERNEL_DIR := $(KERNEL_DIR) $(SRCDIR)/arch/logtrace
      KERNEL_COBJS := $(KERNEL_COBJS) trace_config.o trace_dump.o
endif

#
#  コンフィギュレーションファイルに関する定義
#
CFGNAME = sample1
CFGNAME := $(CFGNAME) target_serial
ifndef OMIT_HW_COUNTER
  CFGNAME := $(CFGNAME) target_hw_counter
endif

#
#  ユーティリティプログラムの名称
#
#  USE_PY_CFG=1 (default): Python 移植版 cfg ($(SRCDIR)/cfg/cfg_py/cfg.py)
#  USE_PY_CFG=0          : 既存 cfg バイナリ ($(SRCDIR)/cfg/cfg/cfg)
#
USE_PY_CFG ?= 1
ifeq ($(USE_PY_CFG),1)
  # Python インタープリタの自動検出．`make PYTHON=<path>` で上書き可能．
  # STM32CubeIDE では Project Properties -> C/C++ Build -> Environment に
  # PYTHON 変数を追加 (python.exe の絶対パス) すれば良い．
  ifndef PYTHON
    ifneq ($(shell python --version 2>/dev/null),)
      PYTHON := python
    else ifneq ($(shell python3 --version 2>/dev/null),)
      PYTHON := python3
    else ifneq ($(shell py -3 --version 2>/dev/null),)
      PYTHON := py -3
    else
      $(error Python interpreter not found. Install Python 3.7+ or set \
PYTHON=<absolute path to python.exe>. For STM32CubeIDE: Project Properties \
-> C/C++ Build -> Environment, add PYTHON with full path to python.exe \
(e.g. C:/Users/<user>/AppData/Local/Programs/Python/Python313/python.exe))
    endif
  endif
  CFG = $(PYTHON) $(SRCDIR)/cfg/cfg_py/cfg.py
else
  CFG = $(SRCDIR)/cfg/cfg/cfg
endif

#
#  オブジェクトファイル名の定義
#
OBJNAME = atk2-sc1
ifdef OBJEXT
  OBJFILE = $(OBJNAME).$(OBJEXT)
  CFG1_OUT = cfg1_out.$(OBJEXT)
else
  OBJFILE = $(OBJNAME)
  CFG1_OUT = cfg1_out
endif

#
#  中間オブジェクトファイルと依存関係ファイルを置くディレクトリの定義
#
OBJDIR = objs
DEPDIR = objs

#
#  ターゲット依存部のディレクトリの定義
#
TARGETDIR = $(SRCDIR)/target/$(TARGET)

#
#  ターゲット依存の定義のインクルード
#
include $(TARGETDIR)/Makefile.target

#
#  ジェネレータ関係の変数の定義
#
PASS2_TF = $(SRCDIR)/kernel/kernel.tf
DEF_TABS = $(SRCDIR)/kernel/kernel.csv
CFG_KERNEL = atk2
CFG_TABS := --ini-file $(SRCDIR)/kernel/kernel.ini $(CFG_TABS)

CFG_TABS := --api-table $(DEF_TABS) \
			--cfg1-def-table $(SRCDIR)/kernel/kernel_def.csv $(CFG_TABS)
CFG_OBJS := Os_Lcfg.o $(CFG_OBJS)
CFG2_OUT := Os_Lcfg.c Os_Lcfg.h Os_Cfg.h $(CFG2_OUT)
ALL_CFG_OBJS := $(CFG_OBJS) cfg1_out.o

#
#  共通コンパイルオプションの定義
#
COPTS := $(COPTS) -g
ifndef OMIT_WARNING_ALL
  COPTS := $(COPTS) -Wall -Wno-unused-label -Wpointer-arith
endif
ifndef OMIT_OPTIMIZATION
  COPTS := $(COPTS) -O2
endif
CDEFS := $(CDEFS)
INCLUDES := -I. -I$(SRCDIR)/include -I$(SRCDIR)/arch -I$(SRCDIR) $(INCLUDES)
LDFLAGS := $(LDFLAGS)
LIBS := $(LIBS)
CFLAGS = $(COPTS) $(CDEFS) $(INCLUDES)

#
#  cfg1_out リンク時はガベージコレクションを無効化
#  （MAGIC_1/2/4 などのシンボルが除去されないようにする）
#
CFG1_OUT_LDFLAGS = -Wl,--no-gc-sections

#
#  アプリケーションプログラムに関する定義
#
APPLNAME = sample1
APPLDIR  = $(SRCDIR)/sample
APPL_CFG_INPUT := $(foreach file,$(CFGNAME),$(file).arxml)

APPL_DIR = $(APPLDIR) $(SRCDIR)/library
APPL_ASMOBJS =
APPL_COBJS = $(APPLNAME).o
APPL_CFLAGS =
APPL_LIBS =
INCLUDES := $(INCLUDES) $(foreach dir,$(APPLDIR),-I$(dir))

#
#  システムモジュールに関する定義
#
SYSMOD_DIR := $(SYSMOD_DIR) $(SRCDIR)/sysmod $(SRCDIR)/library
SYSMOD_ASMOBJS := $(SYSMOD_ASMOBJS)
SYSMOD_COBJS := $(SYSMOD_COBJS) banner.o syslog.o serial.o \
				log_output.o vasyslog.o t_perror.o strerror.o
SYSMOD_CFLAGS := $(SYSMOD_CFLAGS)
SYSMOD_LIBS := $(SYSMOD_LIBS)

#
#  カーネルに関する定義
#
KERNEL_DIR := $(KERNEL_DIR) $(SRCDIR)/kernel
KERNEL_ASMOBJS := $(KERNEL_ASMOBJS)
KERNEL_COBJS := $(KERNEL_COBJS)
KERNEL_CFLAGS := $(KERNEL_CFLAGS) -I$(SRCDIR)/kernel
ifdef OMIT_MAKEOFFSET
  OFFSET_H =
else
  OFFSET_H = offset.h
endif

#
#  ターゲットファイル
#
all: $(OBJFILE)

##### 以下は編集しないこと #####

#
#  カーネルのファイル構成の定義
#
include $(SRCDIR)/kernel/Makefile.kernel
ifdef KERNEL_FUNCOBJS
  KERNEL_LCSRCS := $(KERNEL_FCSRCS)
  KERNEL_LCOBJS := $(foreach file,$(KERNEL_FCSRCS),$($(file:.c=)))
else
  KERNEL_CFLAGS := -DALLFUNC $(KERNEL_CFLAGS)
  KERNEL_COBJS := $(KERNEL_COBJS) \
					$(foreach file,$(KERNEL_FCSRCS),$(file:.c=.o))
endif

#
#  ソースファイルのあるディレクトリに関する定義
#
vpath %.c $(KERNEL_DIR) $(SYSMOD_DIR) $(APPL_DIR)
vpath %.S $(KERNEL_DIR) $(SYSMOD_DIR) $(APPL_DIR)
vpath %.arxml $(KERNEL_DIR) $(SYSMOD_DIR) $(APPL_DIR)

#
#  中間オブジェクトファイルを置くディレクトリの処理
#
APPL_ASMOBJS     := $(addprefix $(OBJDIR)/, $(APPL_ASMOBJS))
APPL_COBJS       := $(addprefix $(OBJDIR)/, $(APPL_COBJS))
SYSMOD_ASMOBJS   := $(addprefix $(OBJDIR)/, $(SYSMOD_ASMOBJS))
SYSMOD_COBJS     := $(addprefix $(OBJDIR)/, $(SYSMOD_COBJS))
KERNEL_ASMOBJS   := $(addprefix $(OBJDIR)/, $(KERNEL_ASMOBJS))
KERNEL_COBJS     := $(addprefix $(OBJDIR)/, $(KERNEL_COBJS))
KERNEL_LCOBJS    := $(addprefix $(OBJDIR)/, $(KERNEL_LCOBJS))
KERNEL_AUX_COBJS := $(addprefix $(OBJDIR)/, $(KERNEL_AUX_COBJS))
CFG_OBJS         := $(addprefix $(OBJDIR)/, $(CFG_OBJS))
ALL_CFG_OBJS     := $(addprefix $(OBJDIR)/, $(ALL_CFG_OBJS))
# HIDDEN_OBJS / START_OBJS / END_OBJS は Makefile.prc / Makefile.target 等の
# 定義側で $(OBJDIR)/ を付与済みのため、ここでは再付与しない

#
#  コンパイルのための変数の定義
#
KERNEL_LIB_OBJS = $(KERNEL_ASMOBJS) $(KERNEL_COBJS) $(KERNEL_LCOBJS)
SYSMOD_OBJS = $(SYSMOD_ASMOBJS) $(SYSMOD_COBJS)
APPL_OBJS = $(APPL_ASMOBJS) $(APPL_COBJS)
ALL_OBJS = $(START_OBJS) $(APPL_OBJS) $(SYSMOD_OBJS) $(CFG_OBJS) \
										$(END_OBJS) $(HIDDEN_OBJS)
ifdef KERNEL_LIB
  ALL_LIBS = $(APPL_LIBS) $(SYSMOD_LIBS) -lkernel $(LIBS)
  LIBS_DEP = $(filter %.a,$(ALL_LIBS)) $(KERNEL_LIB)/libkernel.a
  LDFLAGS := $(LDFLAGS) -L$(KERNEL_LIB)
else
  ALL_LIBS = $(APPL_LIBS) $(SYSMOD_LIBS) libkernel.a $(LIBS)
  LIBS_DEP = $(filter %.a,$(ALL_LIBS))
endif

ifdef TEXT_START_ADDRESS
  LDFLAGS := $(LDFLAGS) -Wl,-Ttext,$(TEXT_START_ADDRESS)
endif
ifdef DATA_START_ADDRESS
  LDFLAGS := $(LDFLAGS) -Wl,-Tdata,$(DATA_START_ADDRESS)
endif
ifdef LDSCRIPT
  LDFLAGS := $(LDFLAGS) -T $(LDSCRIPT)
endif

#
#  リンカスクリプトの STARTUP(start.o) などが $(OBJDIR)/ 配下を見つけられる
#  ようにライブラリ検索パスへ加える
#
LDFLAGS := $(LDFLAGS) -L$(OBJDIR)

#
#  $(OBJDIR) の自動作成
#
$(OBJDIR):
	mkdir -p $(OBJDIR)

#
#  オフセットファイル（offset.h）の生成規則
#
offset.h: $(APPL_CFG_INPUT) Os_Lcfg.timestamp $(SRCDIR)/kernel/genoffset.tf
	$(CFG) --pass 3 --kernel $(CFG_KERNEL) $(INCLUDES) \
				--rom-image cfg1_out.srec --symbol-table cfg1_out.syms \
				-T $(OFFSET_TF) $(CFG_TABS) $(filter %.arxml,$^)

#
#  カーネルのコンフィギュレーションファイルの生成
#
cfg1_out.c: $(APPL_CFG_INPUT) $(SRCDIR)/kernel/kernel_def.csv
	$(CFG) --pass 1 --kernel $(CFG_KERNEL) $(INCLUDES) $(CFG_TABS) $(filter %.arxml,$^)

$(CFG2_OUT): Os_Lcfg.timestamp ;

Os_Lcfg.timestamp: $(APPL_CFG_INPUT) $(START_OBJS) $(OBJDIR)/cfg1_out.o $(END_OBJS) $(HIDDEN_OBJS) $(PASS2_TF) $(DEF_TABS)
	$(LINK) $(CFLAGS) $(LDFLAGS) $(CFG1_OUT_LDFLAGS) -o $(CFG1_OUT) \
						$(START_OBJS) $(OBJDIR)/cfg1_out.o $(END_OBJS)
	$(NM) -n $(CFG1_OUT) > cfg1_out.syms
	$(OBJCOPY) -O srec -S $(CFG1_OUT) cfg1_out.srec
	$(CFG) --pass 2 --kernel $(CFG_KERNEL) $(INCLUDES) \
				-T $(TARGETDIR)/target.tf $(CFG_TABS) $(filter %.arxml,$^)
	if ! cmp Os_Cfg.h Os_Cfg_tmp.h >/dev/null 2>&1 ; then \
		mv Os_Cfg_tmp.h Os_Cfg.h ;\
	else \
		rm Os_Cfg_tmp.h ;\
	fi
ifdef KERNEL_LIB
	if ! cmp Os_Cfg.h $(KERNEL_LIB)/Os_Cfg.h >/dev/null 2>&1 ; then \
		echo Config files Os_Cfg.h and $(KERNEL_LIB)/Os_Cfg.h differ! ;\
		diff -c Os_Cfg.h $(KERNEL_LIB)/Os_Cfg.h ;\
		false;\
	fi
endif
	@: > $@

#
#  カーネルライブラリファイルの生成
#
libkernel.a: $(OFFSET_H) $(KERNEL_LIB_OBJS)
	rm -f libkernel.a
	$(AR) -rcs libkernel.a $(KERNEL_LIB_OBJS)
	$(RANLIB) libkernel.a

#
#  並列 make のための依存関係の定義
#
#  pass2 が生成する Os_Cfg.h / Os_Lcfg.h を取り込むすべての .o は
#  Os_Lcfg.timestamp が完了してから初めてコンパイル可能．
#  cfg1_out.o は Os_Lcfg.timestamp の前提条件 ($(CFG1_OUT) のリンクに必要)
#  なので除外する．HIDDEN_OBJS (start.o) も pass2 出力を参照しないため
#  除外する (start.S は OMIT_INCLUDE_OS_CFG を定義しており，かつ
#  Os_Lcfg.timestamp の前提条件である ── 含めると循環依存になる)．
#
$(APPL_OBJS) $(SYSMOD_OBJS) $(CFG_OBJS) $(KERNEL_LIB_OBJS) \
$(KERNEL_AUX_COBJS): | Os_Lcfg.timestamp $(OBJDIR)
$(APPL_ASMOBJS) $(SYSMOD_ASMOBJS) $(KERNEL_ASMOBJS): | $(OFFSET_H)

#
#  特別な依存関係の定義
#  banner.o は pass3 チェック用に他のすべての .o が出来てからリンクされるよう
#  全 .o とライブラリに依存させる．
#
$(OBJDIR)/banner.o: Os_Lcfg.timestamp \
                    $(filter-out $(OBJDIR)/banner.o,$(ALL_OBJS)) $(LIBS_DEP)

#
#  全体のリンク
#
$(OBJFILE): $(APPL_CFG_INPUT) Os_Lcfg.timestamp $(ALL_OBJS) $(LIBS_DEP)
	$(LINK) $(CFLAGS) $(LDFLAGS) -o $(OBJFILE) $(START_OBJS) \
			-Wl,-Map,$(OBJNAME).map \
			$(APPL_OBJS) $(SYSMOD_OBJS) $(CFG_OBJS) $(ALL_LIBS) $(END_OBJS)
	$(NM) -n $(OBJFILE) > $(OBJNAME).syms
	$(OBJCOPY) -O srec -S $(OBJFILE) $(OBJNAME).srec
	$(CFG) --pass 3 --kernel $(CFG_KERNEL) $(INCLUDES) \
				--rom-image $(OBJNAME).srec --symbol-table $(OBJNAME).syms \
				-T $(TARGETDIR)/target_check.tf $(CFG_TABS) $(filter %.arxml,$^)
	$(OBJDUMP) -d $(OBJFILE) > $(OBJNAME).dump

#
#  バイナリファイルの生成
#
$(OBJNAME).bin: $(OBJFILE)
	$(OBJCOPY) -O binary -S $(OBJFILE) $(OBJNAME).bin

#
#  Sレコードファイルの生成
#
$(OBJNAME).srec: $(OBJFILE)
	$(OBJCOPY) -O srec -S $(OBJFILE) $(OBJNAME).srec

#
#  コンパイル結果の消去
#
.PHONY: clean
clean:
	rm -rf $(OBJDIR)
	rm -f \#* *~ $(CLEAN_FILES)
	rm -f $(OBJFILE) $(OBJNAME).syms $(OBJNAME).srec $(OBJNAME).bin $(OBJNAME).map
	rm -f Os_Lcfg.timestamp $(CFG2_OUT)
	rm -f cfg2_out.tf
	rm -f cfg1_out.c $(CFG1_OUT) cfg1_out.syms cfg1_out.srec
	rm -f $(OBJNAME).dump
	rm -f kernel.res
ifndef KERNEL_LIB
	rm -f libkernel.a
endif
	rm -f offset.h

.PHONY: cleankernel
cleankernel:
	rm -f $(KERNEL_LIB_OBJS) $(KERNEL_LIB_OBJS:$(OBJDIR)/%.o=$(DEPDIR)/%.d)
	rm -f offset.h libkernel.a

.PHONY: realclean
realclean: clean
	rm -f $(REALCLEAN_FILES)

#
#  開発ツールのコマンド名の定義
#
ifeq ($(TOOL),gcc)
  ifdef GCC_TARGET
    GCC_TARGET_PREFIX = $(GCC_TARGET)-
  else
    GCC_TARGET_PREFIX =
  endif
  CC      = $(GCC_TARGET_PREFIX)gcc
  CXX     = $(GCC_TARGET_PREFIX)g++
  AS      = $(GCC_TARGET_PREFIX)as
  LD      = $(GCC_TARGET_PREFIX)ld
  AR      = $(GCC_TARGET_PREFIX)ar
  NM      = $(GCC_TARGET_PREFIX)nm
  RANLIB  = $(GCC_TARGET_PREFIX)ranlib
  OBJCOPY = $(GCC_TARGET_PREFIX)objcopy
  OBJDUMP = $(GCC_TARGET_PREFIX)objdump
endif

LINK = $(CC)

#
#  コンパイルルールの定義
#
KERNEL_ALL_COBJS = $(KERNEL_COBJS) $(KERNEL_AUX_COBJS)

$(KERNEL_ALL_COBJS): $(OBJDIR)/%.o: %.c | $(OBJDIR)
	$(CC) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d $(CFLAGS) $(KERNEL_CFLAGS) $<

$(KERNEL_ALL_COBJS:$(OBJDIR)/%.o=%.s): %.s: %.c
	$(CC) -S -o $@ $(CFLAGS) $(KERNEL_CFLAGS) $<

$(KERNEL_LCOBJS): $(OBJDIR)/%.o: | $(OBJDIR)
	$(CC) -DTOPPERS_$(*F) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d \
									$(CFLAGS) $(KERNEL_CFLAGS) $<

$(KERNEL_LCOBJS:$(OBJDIR)/%.o=%.s): %.s:
	$(CC) -DTOPPERS_$(*F) -S -o $@ $(CFLAGS) $(KERNEL_CFLAGS) $<

$(KERNEL_ASMOBJS): $(OBJDIR)/%.o: %.S | $(OBJDIR)
	$(CC) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d $(CFLAGS) $(KERNEL_CFLAGS) $<

$(SYSMOD_COBJS): $(OBJDIR)/%.o: %.c | $(OBJDIR)
	$(CC) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d $(CFLAGS) $(SYSMOD_CFLAGS) $<

$(SYSMOD_COBJS:$(OBJDIR)/%.o=%.s): %.s: %.c
	$(CC) -S -o $@ $(CFLAGS) $(SYSMOD_CFLAGS) $<

$(SYSMOD_ASMOBJS): $(OBJDIR)/%.o: %.S | $(OBJDIR)
	$(CC) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d $(CFLAGS) $(SYSMOD_CFLAGS) $<

$(APPL_COBJS): $(OBJDIR)/%.o: %.c | $(OBJDIR)
	$(CC) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d $(CFLAGS) $(APPL_CFLAGS) $<

$(APPL_COBJS:$(OBJDIR)/%.o=%.s): %.s: %.c
	$(CC) -S -o $@ $(CFLAGS) $(APPL_CFLAGS) $<

$(APPL_ASMOBJS): $(OBJDIR)/%.o: %.S | $(OBJDIR)
	$(CC) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d $(CFLAGS) $(APPL_CFLAGS) $<

#
#  ジェネレータが生成したファイルのコンパイルルール
#  ジェネレータが生成したファイルは，アプリケーション・システムサービス・
#  カーネル のすべてのオプションを付けてコンパイルする．
#
OS_LCFG_CFLAGS = $(APPL_CFLAGS) $(SYSMOD_CFLAGS) $(KERNEL_CFLAGS)

$(ALL_CFG_OBJS): $(OBJDIR)/%.o: %.c | $(OBJDIR)
	$(CC) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d $(CFLAGS) $(OS_LCFG_CFLAGS) $<

$(ALL_CFG_OBJS:$(OBJDIR)/%.o=%.s): %.s: %.c
	$(CC) -S -o $@ $(CFLAGS) $(OS_LCFG_CFLAGS) $<

#
#  デフォルトコンパイルルールを上書き
#
$(OBJDIR)/%.o: %.c
	@echo "*** Default compile rules should not be used."
	$(CC) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d $(CFLAGS) $<

%.s: %.c
	@echo "*** Default compile rules should not be used."
	$(CC) -S -o $@ $(CFLAGS) $<

$(OBJDIR)/%.o: %.S
	@echo "*** Default compile rules should not be used."
	$(CC) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d $(CFLAGS) $<

#
#  依存関係ファイルのインクルード
#
-include $(DEPDIR)/*.d

#
#  フラッシュ書き込み（OpenOCD / arm-none-eabi-gdb を使用）
#
flash: $(OBJNAME).srec
	openocd -f interface/stlink.cfg -f target/stm32h5x.cfg \
		-c "program $(OBJNAME).srec verify reset exit"

debug: $(OBJFILE)
	arm-none-eabi-gdb $(OBJFILE) \
		-ex "target remote localhost:3333" \
		-ex "monitor reset halt" \
		-ex "load"
