#
#  TOPPERS ATK2
#      Toyohashi Open Platform for Embedded Real-Time Systems
#      Automotive Kernel Version 2
#
#  Copyright (C) 2012-2022 by Center for Embedded Computing Systems
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#  Copyright (C) 2012-2014 by FUJI SOFT INCORPORATED, JAPAN
#  Copyright (C) 2012-2013 by Spansion LLC, USA
#  Copyright (C) 2012-2013 by NEC Communication Systems, Ltd., JAPAN
#  Copyright (C) 2012-2014 by Panasonic Advanced Technology Development Co., Ltd., JAPAN
#  Copyright (C) 2012-2014 by Renesas Electronics Corporation, JAPAN
#  Copyright (C) 2012-2014 by Sunny Giken Inc., JAPAN
#  Copyright (C) 2012-2014 by TOSHIBA CORPORATION, JAPAN
#  Copyright (C) 2012-2014 by Witz Corporation, JAPAN
#
#  上記著作権者は，以下の(1)～(4)の条件を満たす場合に限り，本ソフトウェ
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
#  $Id: Makefile.sample 540 2015-12-29 01:00:01Z ertl-honda $
#

#
#  ターゲットの指定（Makefile.target で上書きされるのを防ぐため）
#
all:

#
#  ターゲット略称の定義
#
TARGET = hsbrh850f1k_ccrh

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
OBJEXT = elf

#
#  実行環境の定義（ターゲット依存に上書きされる場合がある）
#
DBGENV :=

#
#  カーネルライブラリ（libkernel.a）のディレクトリ名
#  （カーネルライブラリも make 対象にする時は，空に定義する）
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
#  システムタイマ(タイマドライバ)を使用するかどうかの定義
#
ENABLE_SYS_TIMER =

#
#  ハードウェアカウンタを無効にするかどうかの定義
#
OMIT_HW_COUNTER =

#
#  トレースログに関する設定
#
ifeq ($(ENABLE_TRACE),true)
      ENABLE_SYS_TIMER = true
      CDEFS := $(CDEFS) -DTOPPERS_ENABLE_TRACE
      KERNEL_DIR := $(KERNEL_DIR) $(SRCDIR)/arch/logtrace
      KERNEL_COBJS := $(KERNEL_COBJS) trace_config.obj trace_dump.obj
endif

#
#  コンフィギュレーションファイルに関する定義
#
CFGNAME = sample1
CFGNAME := $(CFGNAME) target_serial
ifdef ENABLE_SYS_TIMER
  CFGNAME := $(CFGNAME) target_timer
endif
ifndef OMIT_HW_COUNTER
  CFGNAME := $(CFGNAME) target_hw_counter
endif

#
#  ユーティリティプログラムの名称
#
#  Python インタープリタの自動検出．`make PYTHON=<path>` で上書き可能．
#  ジェネレータ (cfg_py) と依存関係生成ツール (utils/makedep.py) の両方で
#  使用するため，常に必要．
#
ifndef PYTHON
  ifneq ($(shell python --version 2>/dev/null),)
    PYTHON := python
  else ifneq ($(shell python3 --version 2>/dev/null),)
    PYTHON := python3
  else ifneq ($(shell py -3 --version 2>/dev/null),)
    PYTHON := py -3
  else
    $(error Python interpreter not found. Install Python 3.7+ or set \
PYTHON=<absolute path to python.exe>)
  endif
endif

#
#  USE_PY_CFG=1 (default): Python 移植版 cfg ($(SRCDIR)/cfg/cfg_py/cfg.py)
#  USE_PY_CFG=0          : 既存 cfg バイナリ ($(SRCDIR)/cfg/cfg/cfg)
#
USE_PY_CFG ?= 1
ifeq ($(USE_PY_CFG),1)
  CFG = $(PYTHON) $(SRCDIR)/cfg/cfg_py/cfg.py
else
  CFG = $(SRCDIR)/cfg/cfg/cfg
endif

#
#  ヘッダファイル依存関係生成ツール
#
#  ccrh の -MMD は Windows 形式の絶対パスを出力するため Cygwin の make では
#  解決できない．代わりに utils/makedep.py で相対パスの .d を生成する．
#
MAKEDEP = $(PYTHON) $(SRCDIR)/utils/makedep.py

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
CFG_COBJS := Os_Lcfg.obj $(CFG_COBJS)
CFG_ASMOBJS := Os_Lcfg_asm.obj $(CFG_ASMOBJS)
CFG1_OUT_COBJS := cfg1_out.obj
CFG2_OUT := Os_Lcfg.c Os_Lcfg.h Os_Cfg.h $(CFG2_OUT)
CFG_OBJS := $(CFG_COBJS) $(CFG_ASMOBJS)

#
#  共通コンパイルオプションの定義
#
COPTS := $(COPTS) -g -g_line
ifndef OMIT_OPTIMIZATION
  COPTS := $(COPTS) -Ospeed -Oinline_size
endif
CDEFS := $(CDEFS)
INCLUDES := -I. -I$(SRCDIR)/include -I$(SRCDIR)/arch -I$(SRCDIR) $(INCLUDES)
LDFLAGS := $(LDFLAGS)
LIBS := $(LIBS) $(CXXLIBS)
CFLAGS = $(COPTS) $(CDEFS) $(INCLUDES)

#
#  アプリケーションプログラムに関する定義
#
APPLNAME = sample1
APPLDIR  = $(SRCDIR)/sample
APPL_CFG_INPUT := $(foreach file,$(CFGNAME),$(file).arxml)

APPL_DIR = $(APPLDIR) $(SRCDIR)/library
APPL_ASMOBJS =
APPL_COBJS = $(APPLNAME).obj
APPL_CFLAGS =
APPL_LIBS =
INCLUDES := $(INCLUDES) $(foreach dir,$(APPLDIR),-I$(dir))

#
#  システムモジュールに関する定義
#
SYSMOD_DIR := $(SYSMOD_DIR) $(SRCDIR)/sysmod $(SRCDIR)/library
SYSMOD_ASMOBJS := $(SYSMOD_ASMOBJS)
SYSMOD_COBJS := $(SYSMOD_COBJS) banner.obj syslog.obj serial.obj \
				log_output.obj vasyslog.obj t_perror.obj strerror.obj
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
#  環境に依存するコンパイルオプションの定義
#
ifdef DBGENV
  CDEFS := $(CDEFS) -D$(DBGENV)
endif

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
					$(foreach file,$(KERNEL_FCSRCS),$(file:.c=.obj))
endif

#
#  ソースファイルのあるディレクトリに関する定義
#
vpath %.c $(KERNEL_DIR) $(SYSMOD_DIR) $(APPL_DIR)
vpath %.asm $(KERNEL_DIR) $(SYSMOD_DIR) $(APPL_DIR)
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
CFG_COBJS        := $(addprefix $(OBJDIR)/, $(CFG_COBJS))
CFG_ASMOBJS      := $(addprefix $(OBJDIR)/, $(CFG_ASMOBJS))
CFG1_OUT_COBJS   := $(addprefix $(OBJDIR)/, $(CFG1_OUT_COBJS))
CFG_OBJS         := $(addprefix $(OBJDIR)/, $(CFG_OBJS))
# START_OBJS / END_OBJS / HIDDEN_OBJS は Makefile.prc / Makefile.target の
# 定義側で $(OBJDIR)/ を付与済みのため，ここでは再付与しない

#
#  コンパイルのための変数の定義
#
KERNEL_LIB_OBJS = $(KERNEL_ASMOBJS) $(KERNEL_COBJS) $(KERNEL_LCOBJS)
SYSMOD_OBJS = $(SYSMOD_ASMOBJS) $(SYSMOD_COBJS)
APPL_OBJS = $(APPL_ASMOBJS) $(APPL_COBJS)
ALL_OBJS = $(START_OBJS) $(APPL_OBJS) $(SYSMOD_OBJS) $(CFG_OBJS) \
											$(END_OBJS) $(HIDDEN_OBJS)
ifdef KERNEL_LIB
  ALL_LIBS = $(APPL_LIBS) $(SYSMOD_LIBS) $(KERNEL_LIB)/libkernel.a $(LIBS)
  LIBS_DEP = $(filter %.a,$(ALL_LIBS))
else
  ALL_LIBS = $(APPL_LIBS) $(SYSMOD_LIBS) libkernel.a $(LIBS)
  LIBS_DEP = $(filter %.a,$(ALL_LIBS))
endif

ifdef LDSCRIPT
  LDFLAGS := $(LDFLAGS) -subcommand=$(LDSCRIPT)
endif

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

Os_Lcfg.timestamp: $(APPL_CFG_INPUT) $(START_OBJS) $(CFG1_OUT_COBJS) \
										$(END_OBJS) $(HIDDEN_OBJS) \
										$(PASS2_TF) $(DEF_TABS)
	$(LINK) $(LDFLAGS) $(CFG1_OUT_LDFLAGS) -output=$(CFG1_OUT) \
						$(START_OBJS) $(CFG1_OUT_COBJS) $(END_OBJS) \
						-list=cfg1_out.map
	$(NM) -n $(CFG1_OUT) > cfg1_out.syms
	$(LINK) $(CFG1_OUT) -output=cfg1_out.srec -form=stype
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
	$(AR) $(KERNEL_LIB_OBJS) -form=library=u -memory=high -output=libkernel.a

#
#  並列 make のための依存関係の定義
#
#  pass2 が生成する Os_Cfg.h / Os_Lcfg.h / asm_config.inc を取り込む
#  すべてのオブジェクトは Os_Lcfg.timestamp が出来てから初めて生成できる．
#  cfg1_out.obj と start.obj ($(START_OBJS)) は Os_Lcfg.timestamp の
#  前提条件なので除外する（含めると循環依存になる）．
#
$(APPL_OBJS) $(SYSMOD_OBJS) $(CFG_OBJS) $(KERNEL_LIB_OBJS) \
$(KERNEL_AUX_COBJS): | Os_Lcfg.timestamp $(OBJDIR)
$(APPL_ASMOBJS) $(SYSMOD_ASMOBJS) $(KERNEL_ASMOBJS): | $(OFFSET_H)

#
#  特別な依存関係の定義
#
$(OBJDIR)/banner.obj: Os_Lcfg.timestamp \
                    $(filter-out $(OBJDIR)/banner.obj,$(ALL_OBJS)) $(LIBS_DEP)

#
#  全体のリンク
#
$(OBJFILE): $(APPL_CFG_INPUT) Os_Lcfg.timestamp $(ALL_OBJS) $(LIBS_DEP)
	$(LINK) $(LDFLAGS) -output=$(OBJFILE) $(START_OBJS) \
			-list=$(OBJNAME).map \
			$(APPL_OBJS) $(SYSMOD_OBJS) $(CFG_OBJS) \
			$(foreach file,$(ALL_LIBS),-library=$(file)) $(END_OBJS)
	$(NM) -n $(OBJFILE) > $(OBJNAME).syms
	$(LINK) $(OBJFILE) -output=$(OBJNAME).srec -form=stype
	$(CFG) --pass 3 --kernel $(CFG_KERNEL) $(INCLUDES) \
				--rom-image $(OBJNAME).srec --symbol-table $(OBJNAME).syms \
				-T $(TARGETDIR)/target_check.tf $(CFG_TABS) $(filter %.arxml,$^)

#
#  Sレコードファイルの生成
#
$(OBJNAME).srec: $(OBJFILE)
	$(LINK) $(OBJFILE) -output=$(OBJNAME).srec -form=stype

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
	rm -f cfg1_out.c $(CFG1_OUT) cfg1_out.syms cfg1_out.srec cfg1_out.map
	rm -f kernel.res
ifndef KERNEL_LIB
	rm -f libkernel.a
endif
	rm -f offset.h

.PHONY: cleankernel
cleankernel:
	rm -f $(KERNEL_LIB_OBJS) $(KERNEL_LIB_OBJS:$(OBJDIR)/%.obj=$(DEPDIR)/%.d)
	rm -f offset.h libkernel.a

.PHONY: realclean
realclean: clean
	rm -f $(REALCLEAN_FILES)

#
#  開発ツールのコマンド名の定義
#
ifeq ($(TOOL),ccrh)
  CC   = ccrh
  AR   = rlink
  LINK = rlink
  NM   = nm
endif

#
#  コンパイルルールの定義
#
#  各ルールはコンパイル後に makedep.py を呼び出して .d を生成する．
#
KERNEL_ALL_COBJS = $(KERNEL_COBJS) $(KERNEL_AUX_COBJS)

$(KERNEL_ALL_COBJS): $(OBJDIR)/%.obj: %.c | $(OBJDIR)
	$(CC) -c -o$@ $(CFLAGS) $(KERNEL_CFLAGS) $<
	@$(MAKEDEP) -o $@ -f $(DEPDIR)/$*.d $< $(INCLUDES) $(KERNEL_CFLAGS)

$(KERNEL_LCOBJS): $(OBJDIR)/%.obj: | $(OBJDIR)
	$(CC) -DTOPPERS_$(*F) -c -o$@ $(CFLAGS) $(KERNEL_CFLAGS) $<
	@$(MAKEDEP) -o $@ -f $(DEPDIR)/$*.d $< $(INCLUDES) $(KERNEL_CFLAGS)

$(KERNEL_ASMOBJS): $(OBJDIR)/%.obj: %.asm | $(OBJDIR)
	$(CC) -c -o$@ $(CFLAGS) $(KERNEL_CFLAGS) $<
	@$(MAKEDEP) -o $@ -f $(DEPDIR)/$*.d $< $(INCLUDES) $(KERNEL_CFLAGS)

$(SYSMOD_COBJS): $(OBJDIR)/%.obj: %.c | $(OBJDIR)
	$(CC) -c -o$@ $(CFLAGS) $(SYSMOD_CFLAGS) $<
	@$(MAKEDEP) -o $@ -f $(DEPDIR)/$*.d $< $(INCLUDES) $(SYSMOD_CFLAGS)

$(SYSMOD_ASMOBJS): $(OBJDIR)/%.obj: %.asm | $(OBJDIR)
	$(CC) -c -o$@ $(CFLAGS) $(SYSMOD_CFLAGS) $<
	@$(MAKEDEP) -o $@ -f $(DEPDIR)/$*.d $< $(INCLUDES) $(SYSMOD_CFLAGS)

$(APPL_COBJS): $(OBJDIR)/%.obj: %.c | $(OBJDIR)
	$(CC) -c -o$@ $(CFLAGS) $(APPL_CFLAGS) $<
	@$(MAKEDEP) -o $@ -f $(DEPDIR)/$*.d $< $(INCLUDES) $(APPL_CFLAGS)

$(APPL_ASMOBJS): $(OBJDIR)/%.obj: %.asm | $(OBJDIR)
	$(CC) -c -o$@ $(CFLAGS) $(APPL_CFLAGS) $<
	@$(MAKEDEP) -o $@ -f $(DEPDIR)/$*.d $< $(INCLUDES) $(APPL_CFLAGS)

#
#  ジェネレータが生成したファイルのコンパイルルール
#  ジェネレータが生成したファイルは，アプリケーション・システムサービス・
#  カーネル のすべてのオプションを付けてコンパイルする．
#
OS_LCFG_CFLAGS = $(APPL_CFLAGS) $(SYSMOD_CFLAGS) $(KERNEL_CFLAGS)

$(CFG_COBJS) $(CFG1_OUT_COBJS): $(OBJDIR)/%.obj: %.c | $(OBJDIR)
	$(CC) -c -o$@ $(CFLAGS) $(OS_LCFG_CFLAGS) $<
	@$(MAKEDEP) -o $@ -f $(DEPDIR)/$*.d $< $(INCLUDES) $(OS_LCFG_CFLAGS)

$(CFG_ASMOBJS): $(OBJDIR)/%.obj: %.asm | $(OBJDIR)
	$(CC) -c -o$@ $(CFLAGS) $(OS_LCFG_CFLAGS) $<
	@$(MAKEDEP) -o $@ -f $(DEPDIR)/$*.d $< $(INCLUDES) $(OS_LCFG_CFLAGS)

#
#  デフォルトコンパイルルールを上書き
#
$(OBJDIR)/%.obj: %.c
	@echo "*** Default compile rules should not be used."
	$(CC) -c -o$@ $(CFLAGS) $<

$(OBJDIR)/%.obj: %.asm
	@echo "*** Default compile rules should not be used."
	$(CC) -c -o$@ $(CFLAGS) $<

#
#  依存関係ファイルのインクルード
#
-include $(DEPDIR)/*.d
