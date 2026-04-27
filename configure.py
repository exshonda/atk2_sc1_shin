#!/usr/bin/env python3
#
#  TOPPERS ATK2
#      Toyohashi Open Platform for Embedded Real-Time Systems
#      Automotive Kernel Version 2
#
#  Copyright (C) 2001-2003 by Embedded and Real-Time Systems Laboratory
#                              Toyohashi Univ. of Technology, JAPAN
#  Copyright (C) 2006-2017 by Center for Embedded Computing Systems
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#  Copyright (C) 2025 by Center for Embedded Computing Systems
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#
#  上記著作権者は，以下の(1)〜(4)の条件を満たす場合に限り，本ソフトウェ
#  ア（本ソフトウェアを改変したものを含む．以下同じ）を使用・複製・改
#  変・再配布（以下，利用と呼ぶ）することを無償で許諾する．
#
#  本ソフトウェアは，無保証で提供されているものである．
#
"""TOPPERS ATK2 configure script (Python 3 版).

Perl 版 configure を Python に書き換えたもの。
sample/ 配下のテンプレートファイル中の @(VAR) を変数置換し、
Makefile やアプリケーションソースを生成する。
"""

import argparse
import os
import re
import shutil
import sys


# テンプレート内の @(VAR) を検出
TEMPLATE_VAR_RE = re.compile(r'@\(([A-Za-z_]+)\)')


def get_objext():
    """オブジェクトファイル名拡張子（cygwin/MSYS で 'exe'）。"""
    plat = sys.platform.lower()
    if plat.startswith("cygwin") or plat.startswith("msys"):
        return "exe"
    return ""


def find_in_path(progname, *fallback_dirs):
    """PATH と fallback ディレクトリから実行ファイルを検索。"""
    found = shutil.which(progname)
    if found:
        return found
    for d in fallback_dirs:
        cand = os.path.join(d, progname)
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return ""


def convert(infile, outfile, vartable):
    """テンプレート infile から @(VAR) を置換して outfile に書き出す。"""
    sys.stderr.write(f"configure: Generating {outfile} from {infile}.\n")
    if os.path.isfile(outfile):
        sys.stderr.write(
            f"configure: {outfile} exists.  Save as {outfile}.bak.\n")
        os.replace(outfile, outfile + ".bak")

    try:
        with open(infile, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        sys.stderr.write(f"configure: can't open {infile}: {e}\n")
        sys.exit(1)

    text = TEMPLATE_VAR_RE.sub(lambda m: vartable.get(m.group(1), ""), text)

    try:
        with open(outfile, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as e:
        sys.stderr.write(f"configure: can't open {outfile}: {e}\n")
        sys.exit(1)


def generate(file_, mandatory, templatedir, target, vartable):
    """テンプレートを探して generate する。

    まず "<templatedir>/<file>.<target>" を探し、なければ
    "<templatedir>/<file>" を探す。mandatory=False ならどちらも無ければスキップ。
    """
    target_specific = os.path.join(templatedir, f"{file_}.{target}")
    if os.path.isfile(target_specific):
        convert(target_specific, file_, vartable)
        return

    generic = os.path.join(templatedir, file_)
    if mandatory or os.path.isfile(generic):
        convert(generic, file_, vartable)


def list_targets(srcdir):
    """インストール済みターゲット一覧。"""
    target_root = os.path.join(srcdir, "target")
    if not os.path.isdir(target_root):
        return []
    return sorted(
        name for name in os.listdir(target_root)
        if os.path.isdir(os.path.join(target_root, name)) and name[:1].isalnum()
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="TOPPERS ATK2 configure script (Python 3 版)",
        add_help=True,
    )
    # default は None にして「ユーザが明示指定したか」を判定可能にする
    parser.add_argument("-T", dest="target",       default=None,
                        help="ターゲット名（必須）")
    parser.add_argument("-A", dest="applname",     default=None,
                        help="アプリケーションプログラム名 (default: sample1)")
    parser.add_argument("-C", dest="cfgname",      default=None,
                        help="コンフィギュレーションファイル名（拡張子なし）")
    parser.add_argument("-H", dest="omit_hw_counter", action="store_true",
                        help="ハードウェアカウンタを無効化")
    parser.add_argument("-a", dest="appldir",      default="",
                        help="アプリケーションディレクトリ名")
    parser.add_argument("-U", dest="applobjs",     default="",
                        help="他のアプリケーションプログラムファイル (.o)")
    parser.add_argument("-L", dest="kernel_lib",   default="",
                        help="カーネルライブラリ libkernel.a のディレクトリ")
    parser.add_argument("-f", dest="kernel_funcobjs", action="store_true",
                        help="カーネルを関数単位でコンパイル")
    parser.add_argument("-D", dest="srcdir",       default=None,
                        help="カーネル等のソースのディレクトリ")
    parser.add_argument("-l", dest="srclang",      default="c",
                        choices=["c", "c++"], help="プログラミング言語")
    parser.add_argument("-t", dest="templatedir",  default=None,
                        help="テンプレートディレクトリ (default: <srcdir>/sample)")
    parser.add_argument("-m", dest="makefile",     default="Makefile",
                        help="テンプレート Makefile 名")
    parser.add_argument("-d", dest="dbgenv",       default="",
                        help="実行環境の名称")
    parser.add_argument("-r", dest="enable_trace", action="store_true",
                        help="トレースログ記録のサンプルコードを使用")
    parser.add_argument("-s", dest="enable_sys_timer", action="store_true",
                        help="システムタイマを使用")
    parser.add_argument("-S", dest="enable_serial", action="store_true",
                        help="シリアル通信を有効化")
    parser.add_argument("-p", dest="perl",         default=None,
                        help="perl のパス名")
    parser.add_argument("-g", dest="cfg",          default=None,
                        help="ジェネレータ (cfg) のパス名")
    parser.add_argument("-o", dest="copts",        default="",
                        help="共通コンパイルオプション (COPTS)")
    parser.add_argument("-O", dest="cdefs",        default="",
                        help="共通シンボル定義 (CDEFS)")
    parser.add_argument("-k", dest="ldflags",      default="",
                        help="共通リンカオプション (LDFLAGS)")
    return parser.parse_args()


def main():
    args = parse_args()

    # ソースディレクトリの決定
    pwd = os.getcwd()
    if args.srcdir:
        srcdir = args.srcdir
        srcabsdir = srcdir if os.path.isabs(srcdir) else os.path.abspath(srcdir)
    else:
        script_dir = os.path.dirname(sys.argv[0])
        if script_dir:
            srcdir = script_dir
            srcabsdir = (srcdir if os.path.isabs(srcdir)
                         else os.path.abspath(os.path.join(pwd, srcdir)))
        else:
            srcdir = pwd
            srcabsdir = pwd

    # -T 必須
    if not args.target:
        sys.stderr.write("configure: -T option is mandatory\n")
        sys.stderr.write("Installed targets are:\n")
        for name in list_targets(srcdir):
            sys.stderr.write(f"\t{name}\n")
        sys.exit(1)

    # -A / -C のデフォルト処理（None のままだとシリアル有効判定に使えるので保持）
    applname_explicit = args.applname is not None
    cfgname_explicit = args.cfgname is not None
    applname = args.applname if applname_explicit else "sample1"
    cfgname = args.cfgname if cfgname_explicit else applname

    # Perl 版: $enable_serial = $opt_S ? $opt_S : !($opt_A || $opt_C);
    # → -S 指定 ⇒ True / -A も -C も無ければ True / どちらか指定なら False
    enable_serial = args.enable_serial or not (applname_explicit or cfgname_explicit)
    cfg_serial = "CFGNAME := $(CFGNAME) target_serial" if enable_serial else ""

    # cfg のパス
    cfg_path = "/cfg/cfg/cfg"
    cfg = args.cfg if args.cfg else "$(SRCDIR)" + cfg_path
    cfgfile = args.cfg if args.cfg else srcdir + cfg_path
    templatedir = args.templatedir if args.templatedir else os.path.join(srcdir, "sample")
    perl = args.perl if args.perl else find_in_path(
        "perl", "/usr/local/bin", "/usr/bin")
    objext = get_objext()

    # 変数テーブル
    vartable = {
        "TARGET":           args.target,
        "APPLNAME":         applname,
        "CFGNAME":          cfgname,
        "OMIT_HW_COUNTER":  "true" if args.omit_hw_counter else "",
        "APPLDIR":          args.appldir,
        "APPLOBJS":         args.applobjs,
        "KERNEL_LIB":       args.kernel_lib,
        "KERNEL_FUNCOBJS":  "true" if args.kernel_funcobjs else "",
        "SRCDIR":           srcdir,
        "SRCABSDIR":        srcabsdir,
        "SRCLANG":          args.srclang,
        "DBGENV":           ("TOPPERS_" + args.dbgenv) if args.dbgenv else "",
        "ENABLE_TRACE":     "true" if args.enable_trace else "",
        "ENABLE_SYS_TIMER": "true" if args.enable_sys_timer else "",
        "CFG_SERIAL":       cfg_serial,
        "PERL":             perl,
        "CFG":              cfg,
        "OBJEXT":           objext,
        "COPTS":            args.copts,
        "CDEFS":            args.cdefs,
        "LDFLAGS":          args.ldflags,
    }

    # ターゲットディレクトリチェック
    target_dir = os.path.join(srcdir, "target", args.target)
    if not os.path.isdir(target_dir):
        sys.stderr.write(f"configure: {target_dir} not exist\n")
        sys.exit(1)

    # ファイル生成
    generate(args.makefile,      True,  templatedir, args.target, vartable)
    generate(applname + ".c",    False, templatedir, args.target, vartable)
    generate(applname + ".cpp",  False, templatedir, args.target, vartable)
    generate(applname + ".h",    False, templatedir, args.target, vartable)
    generate(cfgname + ".arxml", False, templatedir, args.target, vartable)
    if applname == "sample1":
        generate("Rte_Type.h",   False, templatedir, args.target, vartable)

    # cfg 存在チェック（警告のみ）
    cfg_exec = cfgfile if not objext else cfgfile + "." + objext
    if not (os.path.isfile(cfg_exec) and os.access(cfg_exec, os.X_OK)):
        sys.stderr.write(
            "Executable file of the configurator (cfg) is not found.\n")


if __name__ == "__main__":
    main()
