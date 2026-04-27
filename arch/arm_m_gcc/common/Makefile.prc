#
#  TOPPERS ATK2
#      Toyohashi Open Platform for Embedded Real-Time Systems
#      Automotive Kernel Version 2
#
#  Copyright (C) 2008-2017 by Center for Embedded Computing Systems
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
#  Makefile のプロセッサ依存部（ARM Cortex-M 共通）
#

#
#  プロセッサ名，開発環境名の定義
#
PRC  = arm_m
TOOL = gcc

#
#  プロセッサ依存部ディレクトリ名の定義
#
PRCDIR = $(SRCDIR)/arch/$(PRC)_$(TOOL)/common

#
#  コンパイルオプション
#
INCLUDES := $(INCLUDES) -I$(PRCDIR) -I$(SRCDIR)/arch/$(TOOL)
COPTS    := $(COPTS) -fno-common -ffunction-sections -fdata-sections
LDFLAGS  := $(LDFLAGS) -Wl,--gc-sections
LIBS     := $(LIBS) -lgcc -lc -lnosys

#
#  FPU の設定
#
#  FPU_USAGE で 3 通りの動作モードを切り替える (ASP3 と同じ識別子):
#    FPU_NO_PRESERV     : FPU を有効にするが OS は s16-s31 を保存/復帰しない．
#                         FPU を使うのは特定のタスクのみ等の運用が前提．
#    FPU_NO_LAZYSTACKING: FPU を有効にし，OS が s16-s31 を保存/復帰する．
#                         例外入り口で HW が常に拡張フレームを積む．
#    FPU_LAZYSTACKING   : 同上+ HW Lazy Stacking 有効 (FPU 未使用 ISR では
#                         拡張フレームを実体化しないため遅延が小さい)．
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
#  --gc-sections を有効にしていると MAGIC_1/2/4 や TOPPERS_cfg_* シンボル
#  (誰からも参照されない) が削除され、cfg pass2 で「magic number is not
#  found in `cfg1_out.srec/.syms'」エラーになるため。
#
CFG1_OUT_LDFLAGS = -Wl,--no-gc-sections

#
#  カーネルに関する定義
#
KERNEL_DIR     := $(KERNEL_DIR) $(PRCDIR)
KERNEL_ASMOBJS := $(KERNEL_ASMOBJS) prc_support.o
KERNEL_COBJS   := $(KERNEL_COBJS) prc_config.o

#
#  GNU 開発環境のターゲットアーキテクチャの定義
#  チップ依存 Makefile.chip でオーバライド可能
#
GCC_TARGET ?= arm-none-eabi

#
#  スタートアップモジュールに関する定義
#
#  リンカスクリプトに STARTUP(start.o) と記述するため HIDDEN_OBJS に定義．
#  $(OBJDIR)/ を付与し，コンパイルルールも $(OBJDIR)/ 配下へ出力する．
#
HIDDEN_OBJS = start.o
HIDDEN_OBJS := $(addprefix $(OBJDIR)/, $(HIDDEN_OBJS))

$(HIDDEN_OBJS): $(OBJDIR)/%.o: %.S | $(OBJDIR)
	$(CC) -c -o $@ -MD -MP -MF $(DEPDIR)/$*.d $(CFLAGS) $(KERNEL_CFLAGS) $<

LDFLAGS := -nostdlib $(LDFLAGS)

#
#  依存関係の定義
#
cfg1_out.c: $(PRCDIR)/prc_def.csv
Os_Lcfg.timestamp: $(PRCDIR)/prc.tf
offset.h: $(PRCDIR)/prc_offset.tf

#
#  ジェネレータ関係の変数の定義
#
CFG_TABS := $(CFG_TABS) --cfg1-def-table $(PRCDIR)/prc_def.csv
