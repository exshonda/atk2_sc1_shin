#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  TOPPERS Configurator by Ruby
#
#  Copyright (C) 2015 by FUJI SOFT INCORPORATED, JAPAN
#  Copyright (C) 2015-2022 by Embedded and Real-Time Systems Laboratory
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
#  本ソフトウェアは，無保証で提供されているものである．上記著作権者お
#  よびTOPPERSプロジェクトは，本ソフトウェアに関して，特定の使用目的
#  に対する適合性も含めて，いかなる保証も行わない．また，本ソフトウェ
#  アの利用により直接的または間接的に生じたいかなる損害に関しても，そ
#  の責任を負わない．
#
#  $Id: cfg.py (converted from cfg.rb by Claude Code Sonnet 4.6) $
#

import os
import sys
import re
import pickle
import argparse

# Ensure cfg directory is in path for imports
_TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))
if _TOOL_ROOT not in sys.path:
    sys.path.insert(0, _TOOL_ROOT)

from gen_file import GenFile
from srecord import SRecord

#
#  定数定義
#
# 共通
VERSION = "1.7.0"

# cfg1_out関係
CFG1_PREFIX         = "TOPPERS_cfg_"
CFG1_MAGIC_NUM      = "TOPPERS_magic_number"
CFG1_SIZEOF_SIGNED  = "TOPPERS_sizeof_signed_t"
CFG1_SIZEOF_INTPTR  = "TOPPERS_sizeof_intptr_t"
CFG1_SIZEOF_CHARPTR = "TOPPERS_sizeof_char_ptr_t"
CFG1_OUT_C          = "cfg1_out.c"
CFG1_OUT_DB         = "cfg1_out.db"
CFG1_OUT_SREC       = "cfg1_out.srec"
CFG1_OUT_DUMP       = "cfg1_out.dump"
CFG1_OUT_SYMS       = "cfg1_out.syms"
CFG1_OUT_TIMESTAMP  = "cfg1_out.timestamp"
CFG1_OUT_TARGET_H   = "target_cfg1_out.h"

# cfg2_out関係
CFG2_OUT_DB = "cfg2_out.db"

# cfg3_out関係
CFG3_OUT_DB = "cfg3_out.db"

#
#  エラー発生有無フラグ
#
error_flag = False

# システムコンフィギュレーションファイルの構文解析時のエラー
_no_parse_error = 0


#
#  NumStrクラス（数値に文字列を付加したもの）の定義
#
class NumStr:
    def __init__(self, val, str_repr=None):
        self._val = int(val)
        self._str = str(val) if str_repr is None else str_repr

    # 数値情報を返す
    @property
    def val(self):
        return self._val

    # 文字列情報を返す
    @property
    def str(self):
        return self._str

    def __int__(self):
        return self._val

    def __str__(self):
        return self._str

    def __repr__(self):
        return f"[{self._val}(=0x{self._val:x}),{self._str!r}]"

    # 比較は数値情報で行う
    def __eq__(self, other):
        if isinstance(other, NumStr):
            return self._val == other._val
        return self._val == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, NumStr):
            return self._val < other._val
        return self._val < other

    def __le__(self, other):
        return self._val <= (other._val if isinstance(other, NumStr) else other)

    def __gt__(self, other):
        return self._val > (other._val if isinstance(other, NumStr) else other)

    def __ge__(self, other):
        return self._val >= (other._val if isinstance(other, NumStr) else other)

    # ハッシュのキーとして使う時の比較も数値情報で行う
    # ハッシュ値の定義も上書きする
    def __hash__(self):
        return hash(self._val)

    # 数値クラスと演算できるようにする
    def __and__(self, other):
        return self._val & (other._val if isinstance(other, NumStr) else other)

    def __rand__(self, other):
        return other & self._val

    def __or__(self, other):
        return self._val | (other._val if isinstance(other, NumStr) else other)

    def __ror__(self, other):
        return other | self._val

    def __xor__(self, other):
        return self._val ^ (other._val if isinstance(other, NumStr) else other)

    def __invert__(self):
        return ~self._val

    def __lshift__(self, other):
        return self._val << (other._val if isinstance(other, NumStr) else other)

    def __rshift__(self, other):
        return self._val >> (other._val if isinstance(other, NumStr) else other)

    def __add__(self, other):
        return self._val + (other._val if isinstance(other, NumStr) else other)

    def __radd__(self, other):
        return other + self._val

    def __sub__(self, other):
        return self._val - (other._val if isinstance(other, NumStr) else other)

    def __rsub__(self, other):
        return other - self._val

    def __mul__(self, other):
        return self._val * (other._val if isinstance(other, NumStr) else other)

    def __rmul__(self, other):
        return other * self._val

    def __floordiv__(self, other):
        return self._val // (other._val if isinstance(other, NumStr) else other)

    def __mod__(self, other):
        return self._val % (other._val if isinstance(other, NumStr) else other)

    def __bool__(self):
        return bool(self._val)

    def __index__(self):
        return self._val

    def to_s(self, base=10):
        if base == 16:
            return format(self._val, 'x')
        elif base == 2:
            return format(self._val, 'b')
        return str(self._val)

    # 二重引用符で囲まれた文字列の作成
    def quote(self):
        return quote_str(self._str)

    # 二重引用符で囲まれた文字列の展開
    def unquote(self):
        return unquote_str(self._str)


#
#  Stringクラスの拡張（二重引用符で囲まれた文字列の作成／展開）
#

#
#  二重引用符で囲まれた文字列の作成
#
def quote_str(s):
    result = ""
    for c in s:
        if c == "'":
            result += "\\'"
        elif c == '"':
            result += '\\"'
        elif c == '\0':
            result += '\\0'
        elif c == '\a':
            result += '\\a'
        elif c == '\b':
            result += '\\b'
        elif c == '\f':
            result += '\\f'
        elif c == '\n':
            result += '\\n'
        elif c == '\r':
            result += '\\r'
        elif c == '\t':
            result += '\\t'
        elif c == '\v':
            result += '\\v'
        elif c == '\\':
            result += '\\\\'
        else:
            result += c
    return '"' + result + '"'


#
#  二重引用符で囲まれた文字列の展開
#
def unquote_str(s):
    m = re.match(r'^"(.*)"$', s, re.DOTALL)
    if not m:
        return s
    src = m.group(1)
    result = ""
    i = 0
    while i < len(src):
        if src[i] == '\\' and i + 1 < len(src):
            c = src[i + 1]
            i += 2
            if c in 'aA':
                result += '\a'
            elif c in 'bB':
                result += '\b'
            elif c in 'fF':
                result += '\f'
            elif c in 'nN':
                result += '\n'
            elif c in 'rR':
                result += '\r'
            elif c in 'tT':
                result += '\t'
            elif c in 'vV':
                result += '\v'
            elif c in 'xX':
                hex_m = re.match(r'[0-9a-fA-F]{1,2}', src[i:])
                if hex_m:
                    result += chr(int(hex_m.group(), 16))
                    i += len(hex_m.group())
            elif c in '01234567':
                oct_m = re.match(r'[0-7]{1,3}', src[i-1:])
                if oct_m:
                    result += chr(int(oct_m.group(), 8))
                    i += len(oct_m.group()) - 1
            elif c == '\\':
                result += '\\'
            else:
                result += c
        else:
            result += src[i]
            i += 1
    return result


#
#  エラー／警告表示関数
#
# 一般的なエラー表示（処理を中断）
def error_exit(message, location=""):
    if location:
        location += " "
    sys.exit(f"{location}error: {message}")


# 一般的なエラー表示（処理を継続）
def error(message, location=""):
    global error_flag
    if location:
        location += " "
    print(f"{location}error: {message}", file=sys.stderr)
    error_flag = True


# 一般的な警告表示
def warning(message, location=""):
    if location:
        location += " "
    print(f"{location}warning: {message}", file=sys.stderr)


#
#  静的API処理時のエラー／警告表示関数
#
# 静的API処理時のエラー／警告を短く記述できるように，メッセージ中の%ま
# たは%%で始まる記述を以下のように展開する．
#	%label → #{params[:label]}
#	%%label → label `#{params[:label]}'
#
# エラー／警告メッセージの展開
def expand_message(message, params):
    result = message
    for m in re.finditer(r'%%(\w+)', result):
        param = m.group(1)
        val = str(params.get(param, params.get(param, "")))
        result = result.replace(f"%%{param}", f"{param} `{val}'", 1)
    for m in re.finditer(r'%(\w+)', result):
        param = m.group(1)
        val = str(params.get(param, ""))
        result = result.replace(f"%{param}", val, 1)
    return result


# 静的API処理時の警告
def warning_api(params, message):
    warning(expand_message(message, params),
            f"{params.get('_file_', '')}:{params.get('_line_', '')}:")


# 静的API処理時のエラー
def error_ercd(error_code, params, message):
    prefix = "" if error_code is None else f"{error_code}: "
    error(expand_message(prefix + message, params),
          f"{params.get('_file_', '')}:{params.get('_line_', '')}:")


# 静的API処理時のエラー（静的API名付き）
def error_sapi(error_code, params, message, objid=None, objlabel=False):
    suffix = " in %apiname"
    if objid is not None:
        suffix += f" of %%{objid}" if objlabel else f" of %{objid}"
    error_ercd(error_code, params, message + suffix)


# パラメータのエラー
def error_wrong(error_code, params, symbol, wrong, objid=None, objlabel=False):
    error_sapi(error_code, params, f"%%{symbol} is {wrong}", objid, objlabel)


# パラメータ不正のエラー
def error_illegal(error_code, params, symbol, objid=None, objlabel=False):
    error_sapi(error_code, params, f"illegal %%{symbol}", objid, objlabel)


# 過去のバージョンと互換性のための関数
def error_api(params, message):
    error_ercd(None, params, message)


def error_wrong_id(error_code, params, symbol, objid, wrong):
    error_wrong(error_code, params, symbol, wrong, objid)


def error_wrong_sym(error_code, params, symbol, symbol2, wrong):
    error_wrong(error_code, params, symbol, wrong, symbol2, True)


def error_illegal_id(error_code, params, symbol, objid):
    error_illegal(error_code, params, symbol, objid)


def error_illegal_sym(error_code, params, symbol, symbol2):
    error_illegal(error_code, params, symbol, symbol2, True)


# システムコンフィギュレーションファイルの構文解析時のエラー
def parse_error(cfg_file, message):
    global _no_parse_error
    error(message, f"{cfg_file.get_file_name()}:{cfg_file.get_line_no()}:")
    _no_parse_error += 1
    if _no_parse_error >= 10:
        sys.exit("too many errors emitted, stopping now")


def parse_error_fatal(cfg_file, message):
    error_exit(message, f"{cfg_file.get_file_name()}:{cfg_file.get_line_no()}:")


# システムコンフィギュレーションファイルの構文解析時の警告
def parse_warning(cfg_file, message):
    warning(message, f"{cfg_file.get_file_name()}:{cfg_file.get_line_no()}:")


#
#  シンボルファイルの読み込み
#
#  以下のメソッドは，GNUのnmが生成するシンボルファイルに対応している．
#  別のツールに対応する場合には，このメソッドを書き換えればよい．
#
def read_symbol_file(symbol_file_name):
    try:
        symbol_address = {}
        with open(symbol_file_name, "r", encoding="utf-8") as f:
            for line in f:
                # スペース区切りで分解
                fields = line.split()
                # 3列になっていない行は除外
                if len(fields) == 3:
                    symbol_address[fields[2]] = int(fields[0], 16)
        return symbol_address
    except (OSError, IOError) as e:
        sys.exit(str(e))


#
#  値取得シンボルをグローバル変数として定義する
#
def define_symbol_value(symbol_value_table, g):
    for symbol_name, symbol_data in symbol_value_table.items():
        if "VALUE" in symbol_data:
            g[symbol_name] = symbol_data["VALUE"]
            if "NUMSTRVAR" in symbol_data:
                g[symbol_data["NUMSTRVAR"]] = NumStr(symbol_data["VALUE"],
                                                     symbol_data["EXPR"])


#
#  インクルードパスからファイルを探す
#
def search_file_path(file_name, include_directories):
    if os.path.exists(file_name):
        # 指定したファイルパスに存在する
        return file_name
    if file_name.startswith("."):
        # 相対パスを指定していて見つからなかった場合，存在しないものとする
        #（意図しないファイルが対象となることを防止）
        return None
    # 各インクルードパスからファイル存在チェック
    for inc_dir in include_directories:
        path = inc_dir + "/" + file_name
        # 見つかったら相対パスを返す
        if os.path.exists(path):
            return path
    return None


#
#  指定した生成スクリプト（trbファイル）を検索してloadする
#
def make_include_trb(namespace, include_directories):
    def include_trb(file_name):
        file_path = search_file_path(file_name, include_directories)
        if file_path is None:
            error_exit(f"'{file_name}' not found")
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        exec(compile(code, file_path, 'exec'), namespace)
    return include_trb


#
#  インクルードディレクティブ（#include）の生成
#
def generate_includes(gen_file, cfg_file_info):
    for cfg_info in cfg_file_info:
        if "DIRECTIVE" in cfg_info:
            gen_file.add(cfg_info["DIRECTIVE"])


def make_trb_namespace(g, include_directories):
    import builtins
    ns = {
        "__builtins__": builtins,
        "GenFile": GenFile,
        "NumStr": NumStr,
        "error_exit": error_exit,
        "error": error,
        "warning": warning,
        "error_ercd": error_ercd,
        "error_sapi": error_sapi,
        "error_wrong": error_wrong,
        "error_illegal": error_illegal,
        "error_api": error_api,
        "error_wrong_id": error_wrong_id,
        "error_wrong_sym": error_wrong_sym,
        "error_illegal_id": error_illegal_id,
        "error_illegal_sym": error_illegal_sym,
        "warning_api": warning_api,
        "generate_includes": generate_includes,
        "GenerateIncludes": lambda gf: generate_includes(gf, g.get("cfgFileInfo", [])),
    }
    ns["IncludeTrb"] = make_include_trb(ns, include_directories)
    ns.update(g)
    return ns


#
#  パス3の処理
#
def pass3(g, include_directories, trb_file_names, omit_output_db):
    #
    #  パス2から引き渡される情報をファイルから読み込む
    #
    with open(CFG2_OUT_DB, "rb") as f:
        saved = pickle.load(f)
    g.update(saved)
    #
    #  値取得シンボルをグローバル変数として定義する
    #
    define_symbol_value(g.get("symbolValueTable", {}), g)
    #
    #  生成スクリプト（trbファイル）を実行する
    #
    ns = make_trb_namespace(g, include_directories)
    ns.update(g)
    ns["IncludeTrb"] = make_include_trb(ns, include_directories)
    for trb_file_name in trb_file_names:
        ns["IncludeTrb"](trb_file_name)
    g.update({k: v for k, v in ns.items()
              if k in g.get("globalVars", [])})
    #
    #  パス4に引き渡す情報をファイルに生成
    #
    if not omit_output_db:
        save_vars = {v: g[v] for v in g.get("globalVars", []) if v in g}
        with open(CFG3_OUT_DB, "wb") as f:
            pickle.dump(save_vars, f)


#
#  パス4の処理
#
def pass4(g, include_directories, trb_file_names):
    #
    #  パス3から引き渡される情報をファイルから読み込む
    #
    with open(CFG3_OUT_DB, "rb") as f:
        saved = pickle.load(f)
    g.update(saved)
    #
    #  値取得シンボルをグローバル変数として定義する
    #
    define_symbol_value(g.get("symbolValueTable", {}), g)
    #
    #  生成スクリプト（trbファイル）を実行する
    #
    ns = make_trb_namespace(g, include_directories)
    ns.update(g)
    ns["IncludeTrb"] = make_include_trb(ns, include_directories)
    for trb_file_name in trb_file_names:
        ns["IncludeTrb"](trb_file_name)


#
#  生成スクリプト（trbファイル）向けの関数
#
def symbol_func(rom_symbol, asm_label, symbol, cont_flag=False):
    if rom_symbol is not None and (asm_label + symbol) in rom_symbol:
        return rom_symbol[asm_label + symbol]
    elif cont_flag:
        return None
    else:
        error_exit(f"E_SYS: symbol '{symbol}' not found")


def bcopy_func(rom_image, from_address, to_address, size):
    if rom_image is not None:
        rom_image.copy_data(from_address, to_address, size)


def bzero_func(rom_image, address, size):
    if rom_image is not None:
        rom_image.set_data(address, "00" * size)


def peek_func(rom_image, address, size, signed=False):
    if rom_image is not None:
        return rom_image.get_value(address, size, signed)
    return None


def main():
    global error_flag

    #
    #  オプションの処理
    #
    parser = argparse.ArgumentParser(
        prog="cfg.py",
        usage="cfg.py [options] CONFIG-FILE")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-k", "--kernel", metavar="KERNEL")
    parser.add_argument("-p", "--pass", dest="pass_num", metavar="NUM", required=True)
    parser.add_argument("-I", "--include-directory", dest="include_directories",
                        action="append", default=[], metavar="DIRECTORY")
    parser.add_argument("-T", "--trb-file", dest="trb_file_names",
                        action="append", default=[], metavar="TRB-FILE")
    parser.add_argument("-C", "--class-file", dest="class_file_names",
                        action="append", default=[], metavar="TRB-FILE")
    parser.add_argument("--api-table", dest="api_table_file_names",
                        action="append", default=[], metavar="API-TABLE-FILE")
    parser.add_argument("--symval-table", dest="symval_table_file_names",
                        action="append", default=[], metavar="SYMVAL-TABLE-FILE")
    # ATK2 互換: --cfg1-def-table は --symval-table と等価．
    # cfg1_out.c に取り込む `name,"c-expr"` 形式の csv．複数指定可．
    parser.add_argument("--cfg1-def-table", dest="cfg1_def_table_file_names",
                        action="append", default=[],
                        metavar="CFG1-DEF-TABLE-FILE")
    # ATK2 互換: --ini-file kernel.ini (静的 API 定義の補助 ini)．
    parser.add_argument("--ini-file", dest="ini_file_names",
                        action="append", default=[], metavar="INI-FILE")
    parser.add_argument("--rom-image", dest="rom_image_file_name", metavar="DUMP-FILE")
    parser.add_argument("--rom-symbol", dest="rom_symbol_file_name", metavar="SYMS-FILE")
    # ATK2 互換: --symbol-table は --rom-symbol のエイリアス
    parser.add_argument("--symbol-table", dest="symbol_table_file_name",
                        metavar="SYMS-FILE")
    # ATK2 pass2: cfg1_out.srec/syms を読まないモード
    parser.add_argument("--omit-symbol", dest="omit_symbol",
                        action="store_true", default=False)
    # ATK2 pass2: 外部 ID 出力フラグ
    parser.add_argument("--external-id", dest="external_id",
                        action="store_true", default=False)
    parser.add_argument("--id-input-file", dest="id_input_file_name", metavar="ID-FILE")
    parser.add_argument("--id-output-file", dest="id_output_file_name", metavar="ID-FILE")
    parser.add_argument("-M", "--print-dependencies", dest="dependency_file_name",
                        nargs="?", const="", metavar="DEPEND-FILE")
    parser.add_argument("-O", "--omit-output-db", action="store_true", default=False)
    parser.add_argument("--enable-domain", action="store_true", default=False)
    parser.add_argument("--enable-class", action="store_true", default=False)
    parser.add_argument("config_files", nargs="*", metavar="CONFIG-FILE")

    args = parser.parse_args()

    #
    #  オプションのチェック
    #
    pass_num = args.pass_num
    if pass_num not in ("1", "2", "3", "4"):
        sys.exit(f"pass number '{pass_num}' is not valid")

    # パス1では，静的APIテーブルは必須
    if pass_num == "1" and not args.api_table_file_names:
        sys.exit("'--api-table' option must be specified in pass 1")

    # パス1以外では，生成スクリプト（trbファイル）が必須
    if pass_num != "1" and not args.trb_file_names:
        sys.exit("'--trb-file' must be specified except in pass 1")

    #
    #  カーネルオプションの処理
    #
    support_domain = args.enable_domain
    support_class = args.enable_class
    if args.kernel:
        if re.match(r'^hrp', args.kernel):
            support_domain = True
        elif re.match(r'^fmp', args.kernel):
            support_class = True
        elif re.match(r'^hrmp', args.kernel):
            support_domain = True
            support_class = True
        elif args.kernel == "atk2":
            # ATK2 (AUTOSAR OS) は専用ドライバへ分岐する．
            #   pass1 → atk2_pass1: ARXML + CSV → cfg1_out.c
            #   pass2 → atk2_pass2: ARXML + cfg1_out.{srec,syms} + .tf
            #                       → Os_Lcfg.{c,h} / Os_Cfg_tmp.h / cfg2_out.tf
            #   pass3 → atk2_pass3: ARXML + ROM/syms + .tf → offset.h / check
            if pass_num == "1":
                from atk2_pass1 import run as _atk2_pass1_run
                _atk2_pass1_run(args)
            elif pass_num == "2":
                from atk2_pass2 import run as _atk2_pass2_run
                _atk2_pass2_run(args)
            elif pass_num == "3":
                from atk2_pass3 import run as _atk2_pass3_run
                _atk2_pass3_run(args)
            else:
                sys.exit(f"unknown pass {pass_num} for --kernel atk2")
            if error_flag:
                sys.exit(1)
            GenFile.output()
            if args.id_output_file_name:
                open(args.id_output_file_name, "w").close()
            sys.exit(0)

    #
    #  ID番号入力ファイルの取り込み
    #
    input_objid = {}
    if args.id_input_file_name:
        try:
            with open(args.id_input_file_name, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        input_objid[parts[0]] = int(parts[1])
        except (OSError, IOError) as e:
            sys.exit(str(e))

    #
    #  指定されたシンボルファイルの読み込み
    #
    rom_symbol = None
    if args.rom_symbol_file_name:
        if os.path.exists(args.rom_symbol_file_name):
            rom_symbol = read_symbol_file(args.rom_symbol_file_name)
        else:
            error_exit(f"'{args.rom_symbol_file_name}' not found")

    #
    #  指定されたSレコードファイルの読み込み
    #
    rom_image = None
    if args.rom_image_file_name:
        if os.path.exists(args.rom_image_file_name):
            if args.rom_image_file_name.endswith(".srec"):
                rom_image = SRecord(args.rom_image_file_name, "srec")
            else:
                rom_image = SRecord(args.rom_image_file_name, "dump")
        else:
            error_exit(f"'{args.rom_image_file_name}' not found")

    g = {
        "inputObjid": input_objid,
        "configFileNames": args.config_files,
        "includeDirectories": args.include_directories,
        "trbFileNames": args.trb_file_names,
        "classFileNames": args.class_file_names,
        "apiTableFileNames": args.api_table_file_names,
        "symvalTableFileNames": args.symval_table_file_names,
        "supportDomain": support_domain,
        "supportClass": support_class,
        "omitOutputDb": args.omit_output_db,
        "idOutputFileName": args.id_output_file_name,
        "dependencyFileName": args.dependency_file_name,
        "romSymbol": rom_symbol,
        "romImage": rom_image,
        "asmLabel": "",
        "timeStampFileName": None,
        "globalVars": [],
    }

    asm_label = g["asmLabel"]

    def symbol(sym, cont_flag=False):
        return symbol_func(g.get("romSymbol"), g.get("asmLabel", ""), sym, cont_flag)

    def bcopy(from_addr, to_addr, size):
        bcopy_func(g.get("romImage"), from_addr, to_addr, size)

    def bzero(addr, size):
        bzero_func(g.get("romImage"), addr, size)

    def peek(addr, size, signed=False):
        return peek_func(g.get("romImage"), addr, size, signed)

    g["SYMBOL"] = symbol
    g["PEEK"] = peek
    g["BCOPY"] = bcopy
    g["BZERO"] = bzero

    #
    #  パスに従って各処理を実行
    #
    if pass_num == "1":
        from pass1 import Pass1
        Pass1(g)
    elif pass_num == "2":
        from pass2 import Pass2
        Pass2(g)
    elif pass_num == "3":
        pass3(g, args.include_directories, args.trb_file_names, args.omit_output_db)
    elif pass_num == "4":
        pass4(g, args.include_directories, args.trb_file_names)

    # エラー発生時はabortする
    if error_flag:
        sys.exit(1)

    #
    #  作成したすべてのファイルを出力する
    #
    GenFile.output()

    #
    #  タイムスタンプファイルの生成
    #
    if g.get("timeStampFileName"):
        open(g["timeStampFileName"], "w").close()


if __name__ == "__main__":
    main()
