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
#  $Id: pass1.py (converted from pass1.rb by Claude Code Sonnet 4.6) $
#

#
#		パス1の処理
#

import os
import sys
import re
import csv
import pickle

from gen_file import GenFile
from cfg import (
    CFG1_PREFIX, CFG1_OUT_C, CFG1_OUT_DB, CFG1_OUT_TIMESTAMP, CFG1_OUT_TARGET_H,
    NumStr, error_exit, error, warning,
    parse_error, parse_error_fatal, parse_warning,
    error_ercd, error_sapi, error_wrong, error_illegal,
    error_wrong_id, error_illegal_id, error_illegal_sym,
    search_file_path, error_flag
)


#
#  静的APIテーブルの読み込み
#
def _read_api_table_file(g):
    api_definition = g.setdefault("apiDefinition", {
        "INCLUDE": {"PARAM": [{"NAME": "file", "STRING_LITERAL": True}]}
    })
    for api_table_file_name in g.get("apiTableFileNames", []):
        api_phase = None
        m = re.match(r'^(.+):(\w+)$', api_table_file_name)
        if m:
            api_table_file_name = m.group(1)
            api_phase = m.group(2)

        if not os.path.exists(api_table_file_name):
            error_exit(f"'{api_table_file_name}' not found")
            continue

        lineno = 0
        with open(api_table_file_name, "r", encoding="utf-8") as f:
            for line in f:
                lineno += 1
                if re.match(r'^#', line):		# コメントをスキップ
                    continue
                fields = line.split()		# フィールドに分解
                if not fields:
                    continue

                api_name = fields.pop(0)	# API名の取り出し
                m2 = re.match(r'^(.+)\[(.+)\]$', api_name)
                if m2:
                    api_name = m2.group(1)
                    api_def = {"APINAME": api_name, "API": m2.group(2)}
                else:
                    api_def = {"APINAME": api_name, "API": api_name}
                if api_phase is not None:
                    api_def["PHASE"] = api_phase

                api_params = []
                for param in fields:
                    m3 = re.match(r'^(\W*)(\w+)(\W*)$', param)
                    if m3:
                        prefix = m3.group(1)
                        name = m3.group(2)
                        postfix = m3.group(3)
                        api_param = {"NAME": name}
                        if prefix == "#":					# オブジェクト識別名（定義）
                            api_param["ID_DEF"] = True
                        elif prefix == "%":					# オブジェクト識別名（参照）
                            api_param["ID_REF"] = True
                        elif prefix == ".":					# 符号無し整数定数式パラメータ
                            api_param["EXPTYPE"] = "unsigned_t"
                        elif prefix == "+":					# 符号付き整数定数式パラメータ
                            api_param["EXPTYPE"] = "signed_t"
                            api_param["SIGNED"] = True
                        elif prefix == "^":					# ポインタ整数定数式パラメータ
                            api_param["EXPTYPE"] = "uintptr_t"
                            api_param["INTPTR"] = True
                        elif prefix == "&":					# 一般整数定数式パラメータ
                            pass
                        elif prefix == "$":					# 文字列定数式パラメータ
                            api_param["STRING"] = True
                            api_param["EXPTYPE"] = "char *"
                        elif prefix == "":
                            pass
                        else:
                            error_exit(f"'{param}' is invalid in "
                                       f"'{api_table_file_name}:{lineno}'")
                        if postfix == "*":					# キーを決めるパラメータ
                            api_def["KEYPAR"] = name
                        elif postfix == "?":				# オプションパラメータ
                            api_param["OPTIONAL"] = True
                        elif postfix == "...":				# リストパラメータ
                            api_param["LIST"] = True
                        api_params.append(api_param)
                    elif param == "{":					# {
                        api_params.append({"BRACE": "{"})
                    elif param == "{?":					# {?
                        api_params.append({"BRACE": "{", "OPTBRACE": True})
                    elif param == "}":					# }
                        api_params.append({"BRACE": "}"})
                    else:
                        error_exit(f"'{param}' is invalid in "
                                   f"'{api_table_file_name}:{lineno}'")

                api_def["PARAM"] = api_params
                api_definition[api_name] = api_def


#
#  値取得シンボルテーブルの読み込み
#
def _read_symval_table(g):
    symbol_value_table = g.setdefault("symbolValueTable", {})
    for symval_file_name in g.get("symvalTableFileNames", []):
        if not os.path.exists(symval_file_name):
            error_exit(f"'{symval_file_name}' not found")
            continue

        with open(symval_file_name, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            lineno = 0
            for record in reader:
                lineno += 1
                if not record or record[0].startswith("#"):
                    continue
                while len(record) < 5:
                    record.append(None)

                symbol = {}

                # 変数名
                if record[0] is None:
                    error_exit(f"invalid variable name in "
                               f"'{symval_file_name}:{lineno}'")
                m = re.match(r'^(.+)\[(.+)\]$', record[0])
                if m:
                    variable = m.group(1)
                    symbol["NUMSTRVAR"] = m.group(2)
                else:
                    variable = record[0]

                # 式
                if not record[1]:
                    symbol["EXPR"] = variable
                else:
                    symbol["EXPR"] = record[1]

                # 式の型
                if record[2]:
                    if re.match(r'^[bB]', record[2]):		# 真偽値
                        symbol["BOOL"] = True
                    elif re.match(r'^[iI]', record[2]):		# ポインタ整数値
                        symbol["INTPTR"] = True
                    elif re.match(r'^[uU]', record[2]):		# 符号無し整数値
                        pass								# 何も設定しない
                    else:									# 符号付き整数値
                        symbol["SIGNED"] = True

                # コンパイル条件
                if record[3]:
                    symbol["CONDITION"] = record[3]

                # 条件が成立しない時の式
                if record[4]:
                    symbol["ELSE_EXPR"] = record[4]

                symbol_value_table[variable] = symbol


#
#  システムコンフィギュレーションファイルからの読み込みクラス
#
class ConfigFile:
    def __init__(self, file_name):
        self._file_name = file_name
        self._line_no = 0
        self._within_comment = False
        try:
            self._file = open(file_name, "r", encoding="utf-8", errors="replace")
        except (OSError, IOError) as e:
            sys.exit(str(e))

    def close(self):
        self._file.close()

    def get_next_line(self, within_api):
        line = self._file.readline()
        if line == "":
            return None
        self._line_no += 1
        line = line.rstrip("\n\r")

        if self._within_comment:
            m = re.search(r'\*/', line)
            if m:
                line = line[m.end():]
                self._within_comment = False
            else:
                line = ""

        if not self._within_comment:
            line = re.sub(r'/\*.*?\*/', "", line)
            if re.match(r'^\s*#', line):
                if within_api:
                    parse_error(self,
                                "preprocessor directive must not be within static API")
                    line = ""
            elif re.search(r'/\*', line):
                line = re.sub(r'/\*.*$', "", line)
                self._within_comment = True
            elif re.search(r'//', line):
                line = re.sub(r'//.*$', "", line)

        return line

    def get_file_name(self):
        return self._file_name

    def get_line_no(self):
        return self._line_no


#
#  システムコンフィギュレーションファイルのパーサークラス
#
class CfgParser:
    _last_api_index = 0
    _last_class_index = 0
    _current_domain = None
    _current_class_index = None
    _nest_dc = []

    def __init__(self):
        self._line = ""
        self._skip_comma = False		# 次が,であれば読み飛ばす

    #
    #  文字列末まで読む
    #
    def _parse_string(self, cfg_file):
        string = ""
        while True:
            m = re.match(r'^([^"]*\\\\)(.*)', self._line, re.DOTALL)
            if m:
                string += m.group(1)
                self._line = m.group(2)
                continue
            m = re.match(r'^([^"]*\\")(.*)', self._line, re.DOTALL)
            if m:
                string += m.group(1)
                self._line = m.group(2)
                continue
            m = re.match(r'^([^"]*")(.*)', self._line, re.DOTALL)
            if m:
                string += m.group(1)
                self._line = m.group(2)
                return string
            string += self._line + "\n"
            self._line = cfg_file.get_next_line(True)
            if self._line is None:
                parse_error_fatal(cfg_file, "unterminated string meets end-of-file")

    #
    #  文字末まで読む
    #
    def _parse_char(self, cfg_file):
        string = ""
        while True:
            m = re.match(r"^([^']*\\\\)(.*)", self._line, re.DOTALL)
            if m:
                string += m.group(1)
                self._line = m.group(2)
                continue
            m = re.match(r"^([^']*\\')(.*)", self._line, re.DOTALL)
            if m:
                string += m.group(1)
                self._line = m.group(2)
                continue
            m = re.match(r"^([^']*')(.*)", self._line, re.DOTALL)
            if m:
                string += m.group(1)
                self._line = m.group(2)
                return string
            string += self._line + "\n"
            self._line = cfg_file.get_next_line(True)
            if self._line is None:
                parse_error_fatal(cfg_file, "unterminated char meets end-of-file")

    #
    #  改行と空白文字を読み飛ばす
    #
    def _skip_space(self, cfg_file, within_api=True):
        while True:
            if self._line is None:				# ファイル末であればリターン
                return
            self._line = self._line.lstrip()	# 先頭の空白を削除
            if self._line:						# 空行でなければリターン
                return
            self._line = cfg_file.get_next_line(within_api)	# 次の行を読む

    #
    #  パラメータを1つ読む
    #
    # _lineの先頭からパラメータを1つ読んで，それを文字列で返す．読んだパ
    # ラメータは，_lineからは削除する．パラメータの途中で行末に達した時は，
    # cfg_fileから次の行を取り出す．ファイル末に達した時は，Noneを返す．
    #
    def _parse_param(self, cfg_file):
        param = ""							# 読んだ文字列
        paren_level = 0						# 括弧のネストレベル
        skip_comma = self._skip_comma
        self._skip_comma = False

        self._skip_space(cfg_file)			# 改行と空白文字を読み飛ばす
        if self._line is None:				# ファイル末であればエラー終了
            parse_error_fatal(cfg_file,
                              "unexpected end-of-file within a static API")

        while True:
            if self._line is None:
                break
            if paren_level == 0:
                m = re.match(r'^(\s*,)(.*)', self._line, re.DOTALL)
                if m:								# ,
                    self._line = m.group(2)
                    if param == "" and skip_comma:
                        skip_comma = False
                        return self._parse_param(cfg_file)	# 再帰呼び出し
                    return param.strip()
                m = re.match(r'^(\s*\{)(.*)', self._line, re.DOTALL)
                if m:								# {
                    if param:
                        return param.strip()
                    self._line = m.group(2)
                    return "{"
                m = re.match(r'^(\s*\()(.*)', self._line, re.DOTALL)
                if m:								# (
                    param += m.group(1)
                    self._line = m.group(2)
                    paren_level += 1
                    continue
                m = re.match(r'^(\s*([})]))(.*)', self._line, re.DOTALL)
                if m:								# }か)
                    if param:
                        return param.strip()
                    self._line = m.group(3)
                    if m.group(2) == "}":
                        self._skip_comma = True
                    return m.group(2)
                m = re.match(r'^(\s*")(.*)', self._line, re.DOTALL)
                if m:								# "
                    self._line = m.group(2)
                    param += m.group(1) + self._parse_string(cfg_file)
                    continue
                m = re.match(r"^(\s*')(.*)", self._line, re.DOTALL)
                if m:								# '
                    self._line = m.group(2)
                    param += m.group(1) + self._parse_char(cfg_file)
                    continue
                m = re.match(r"^(\s*[^,{}()\"'\s]+)(.*)", self._line, re.DOTALL)
                if m:								# その他の文字列
                    param += m.group(1)
                    self._line = m.group(2)
                    continue
                param += " "					# 行末
                self._line = cfg_file.get_next_line(True)
            else:
                # 括弧内の処理
                m = re.match(r'^(\s*\()(.*)', self._line, re.DOTALL)
                if m:								# "("
                    param += m.group(1)
                    self._line = m.group(2)
                    paren_level += 1
                    continue
                m = re.match(r'^(\s*\))(.*)', self._line, re.DOTALL)
                if m:								# ")"
                    param += m.group(1)
                    self._line = m.group(2)
                    paren_level -= 1
                    continue
                m = re.match(r'^(\s*")(.*)', self._line, re.DOTALL)
                if m:								# "
                    self._line = m.group(2)
                    param += m.group(1) + self._parse_string(cfg_file)
                    continue
                m = re.match(r"^(\s*')(.*)", self._line, re.DOTALL)
                if m:								# '
                    self._line = m.group(2)
                    param += m.group(1) + self._parse_char(cfg_file)
                    continue
                m = re.match(r"^(\s*[^()\"'\s]+)(.*)", self._line, re.DOTALL)
                if m:								# その他の文字列
                    param += m.group(1)
                    self._line = m.group(2)
                    continue
                param += " "					# 行末
                self._line = cfg_file.get_next_line(True)
        return param.strip()

    def _get_param(self, api_param, param, cfg_file):
        from cfg import unquote_str
        if param == "":
            if "OPTIONAL" not in api_param:
                parse_error(cfg_file, "unexpected ','")
            return param
        if "ID_DEF" in api_param or "ID_REF" in api_param:
            if not re.match(r'^[A-Za-z_]\w*$', param):
                parse_error(cfg_file, f"'{param}' is illegal object ID")
            return param
        if "STRING_LITERAL" in api_param:
            return unquote_str(param)
        return param

    def _parse_api(self, cfg_file, api_name, api_definition):
        # 静的APIの読み込み
        static_api = {}
        too_few_params = False
        skip_until_brace = 0

        self._skip_space(cfg_file)					# 改行と空白文字を読み飛ばす
        if self._line is None:						# ファイル末であればエラー終了
            parse_error_fatal(cfg_file,
                              "unexpected end-of-file within a static API")

        m = re.match(r'^\((.*)', self._line, re.DOTALL)
        if m:
            self._line = m.group(1)
            static_api["APINAME"] = api_name
            static_api["_FILE_"] = cfg_file.get_file_name()
            static_api["_LINE_"] = cfg_file.get_line_no()
            api_def = api_definition[api_name]
            param = self._parse_param(cfg_file)

            for api_param in api_def["PARAM"]:
                if param is None:
                    return static_api
                if skip_until_brace > 0:
                    if "BRACE" in api_param:
                        if api_param["BRACE"] == "{":
                            skip_until_brace += 1
                        elif api_param["BRACE"] == "}":
                            skip_until_brace -= 1
                elif "OPTIONAL" in api_param:
                    if not re.match(r'^([{})])$', param):
                        store_param = self._get_param(api_param, param, cfg_file)
                        if store_param:
                            static_api[api_param["NAME"]] = store_param
                        param = self._parse_param(cfg_file)
                elif "LIST" in api_param:
                    static_api[api_param["NAME"]] = []
                    while not re.match(r'^([{})])$', param):
                        static_api[api_param["NAME"]].append(
                            self._get_param(api_param, param, cfg_file))
                        param = self._parse_param(cfg_file)
                        if param is None:
                            break
                elif "OPTBRACE" in api_param:
                    if param == api_param["BRACE"]:
                        param = self._parse_param(cfg_file)
                        if param is None:
                            break
                    else:
                        if param == "":
                            param = self._parse_param(cfg_file)
                            if param is None:
                                break
                        elif not re.match(r'^([})])$', param):
                            parse_error(cfg_file,
                                        f"'{{...}}' expected before {param}")
                        skip_until_brace += 1
                elif "BRACE" not in api_param:
                    if not re.match(r'^([{})])$', param):
                        static_api[api_param["NAME"]] = self._get_param(
                            api_param, param, cfg_file)
                        param = self._parse_param(cfg_file)
                    elif not too_few_params:
                        parse_error(cfg_file,
                                    f"too few parameters before '{param}'")
                        too_few_params = True
                elif param == api_param["BRACE"]:
                    param = self._parse_param(cfg_file)
                    too_few_params = False
                else:
                    parse_error(cfg_file,
                                f"'{api_param['BRACE']}' expected before {param}")
                    # )かファイル末まで読み飛ばす
                    while True:
                        param = self._parse_param(cfg_file)
                        if param is None or param == ")":
                            break
                    break

            # 期待されるパラメータをすべて読んだ後の処理
            if param != ")":
                while True:
                    param = self._parse_param(cfg_file)
                    if param is None:
                        return static_api		# ファイル末であればリターン
                    if param == ")":
                        break
                parse_error(cfg_file, "too many parameters before ')'")
        else:
            parse_error(cfg_file, f"syntax error: {self._line}")
            self._line = ""
        return static_api

    def _parse_open_brace(self, cfg_file, closure):
        # {の読み込み
        self._skip_space(cfg_file)				# 改行と空白文字を読み飛ばす
        m = re.match(r'^\{(.*)', self._line, re.DOTALL)
        if m:
            self._line = m.group(1)
        else:
            parse_error(cfg_file, f"'{{' expected after {closure}")

    def parse_file(self, cfg_file_name, g):
        cfg_files = [ConfigFile(cfg_file_name)]
        self._line = ""
        api_definition = g.get("apiDefinition", {})
        cfg_file_info = g.setdefault("cfgFileInfo", [])
        dependency_files = g.setdefault("dependencyFiles", [])
        domain_id = g.setdefault("domainId", {"TDOM_KERNEL": -1, "TDOM_NONE": -2})
        input_objid = g.get("inputObjid", {})
        support_domain = g.get("supportDomain", False)
        support_class = g.get("supportClass", False)
        include_directories = g.get("includeDirectories", [])

        while True:
            cfg_file = cfg_files[-1]
            self._skip_space(cfg_file, False)
            if self._line is None:
                # ファイル末の処理
                cfg_files.pop().close()
                if not cfg_files:
                    break					# パース処理終了
                self._line = ""				# 元のファイルに戻って続ける
            elif re.match(r'^;', self._line):
                # ;は読み飛ばす
                self._line = self._line[1:]
            elif re.match(r'^#', self._line):
                # プリプロセッサディレクティブを読む
                m = re.match(r'^#(include|ifdef|ifndef|if|endif|else|elif)\b',
                             self._line)
                if m:
                    directive = {
                        "DIRECTIVE": self._line.strip(),
                        "_FILE_": cfg_file.get_file_name(),
                        "_LINE_": cfg_file.get_line_no(),
                    }
                    cfg_file_info.append(directive)
                else:
                    parse_error(cfg_file,
                                f"unknown preprocessor directive: {self._line}")
                self._line = ""
            elif re.match(r'^([A-Z_][A-Z0-9_]*)\b', self._line):
                m = re.match(r'^([A-Z_][A-Z0-9_]*)\b(.*)', self._line, re.DOTALL)
                api_name = m.group(1)
                self._line = m.group(2)

                if api_name == "KERNEL_DOMAIN":
                    if not support_domain:
                        parse_warning(cfg_file, "'KERNEL_DOMAIN' is not supported")
                    if CfgParser._current_domain is not None:
                        parse_error(cfg_file, "'DOMAIN' must not be nested")
                    CfgParser._current_domain = "TDOM_KERNEL"
                    self._parse_open_brace(cfg_file, api_name)
                    CfgParser._nest_dc.append("domain")

                elif api_name == "DOMAIN":
                    if not support_domain:
                        parse_warning(cfg_file, "'DOMAIN' is not supported")
                    if CfgParser._current_domain is not None:
                        parse_error(cfg_file, "'DOMAIN' must not be nested")
                    domid = self._parse_param(cfg_file)
                    domid = re.sub(r'^\((.+)\)$', r'\1', domid, flags=re.DOTALL).strip()
                    if not re.match(r'^[A-Za-z_]\w*$', domid):
                        parse_error(cfg_file, f"'{domid}' is illegal domain ID")
                    else:
                        if domid not in domain_id:
                            if domid in input_objid:
                                domain_id[domid] = input_objid[domid]
                                if domain_id[domid] > 32:
                                    parse_error_fatal(cfg_file,
                                                      f"domain ID for '{domid}' is too large")
                            else:
                                domain_id[domid] = None
                        CfgParser._current_domain = domid
                    self._parse_open_brace(cfg_file, api_name)
                    CfgParser._nest_dc.append("domain")

                elif api_name == "CLASS":
                    if not support_class:
                        parse_warning(cfg_file, "'CLASS' is not supported")
                    if CfgParser._current_class_index is not None:
                        parse_error(cfg_file, "'CLASS' must not be nested")
                    CfgParser._last_class_index += 1
                    CfgParser._current_class_index = CfgParser._last_class_index
                    classid = {
                        "CLSSTR": re.sub(r'^\((.+)\)$', r'\1',
                                         self._parse_param(cfg_file),
                                         flags=re.DOTALL).strip(),
                        "CLSIDX": CfgParser._current_class_index,
                        "_FILE_": cfg_file.get_file_name(),
                        "_LINE_": cfg_file.get_line_no(),
                    }
                    cfg_file_info.append(classid)
                    self._parse_open_brace(cfg_file, api_name)
                    CfgParser._nest_dc.append("class")

                elif api_name in api_definition:
                    # 静的APIを1つ読む
                    static_api = self._parse_api(cfg_file, api_name, api_definition)
                    if not static_api:
                        # ファイル末か文法エラー
                        pass
                    elif static_api.get("APINAME") == "INCLUDE":
                        # INCLUDEの処理
                        include_file_path = search_file_path(
                            static_api["file"], include_directories)
                        if include_file_path is None:
                            err = {
                                "DIRECTIVE": f"#error '{static_api['file']}' not found.",
                                "_FILE_": cfg_file.get_file_name(),
                                "_LINE_": cfg_file.get_line_no(),
                            }
                            cfg_file_info.append(err)
                        else:
                            dependency_files.append(include_file_path)
                            cfg_files.append(ConfigFile(include_file_path))
                    else:
                        # 静的APIの処理
                        if CfgParser._current_domain is not None:
                            static_api["DOMAIN"] = CfgParser._current_domain
                        if CfgParser._current_class_index is not None:
                            static_api["CLSIDX"] = CfgParser._current_class_index
                        CfgParser._last_api_index += 1
                        static_api["INDEX"] = CfgParser._last_api_index
                        cfg_file_info.append(static_api)

                    # ";"を読む
                    self._skip_space(cfg_file, False)		# 改行と空白文字を読み飛ばす
                    m2 = re.match(r'^;(.*)', self._line, re.DOTALL)
                    if m2:
                        self._line = m2.group(1)
                    else:
                        parse_error(cfg_file, "';' expected after static API")
                else:
                    parse_error(cfg_file, f"unknown static API: {api_name}")

            elif re.match(r'^\}', self._line):
                # }の処理
                m = re.match(r'^\}(.*)', self._line, re.DOTALL)
                if CfgParser._nest_dc:
                    kind = CfgParser._nest_dc.pop()
                    if kind == "domain":
                        CfgParser._current_domain = None
                    elif kind == "class":
                        CfgParser._current_class_index = None
                else:
                    parse_error_fatal(cfg_file, "unexpected '}'")
                self._line = m.group(1)
            else:
                parse_error(cfg_file, f"syntax error: {self._line}")
                self._line = ""


#
#  cfg1_out.cの生成
#
def _generate_cfg1_out_c(g):
    cfg1_out = GenFile(CFG1_OUT_C)
    cfg_file_info = g.get("cfgFileInfo", [])
    symbol_value_table = g.get("symbolValueTable", {})
    api_definition = g.get("apiDefinition", {})
    domain_id = g.get("domainId", {})

    cfg1_out.append(f"/* {CFG1_OUT_C} */\n"
                    "#define TOPPERS_CFG1_OUT\n"
                    "#include \"kernel/kernel_int.h\"\n")

    # インクルードディレクティブ（#include）の生成
    for cfg_info in cfg_file_info:
        if "DIRECTIVE" in cfg_info:
            cfg1_out.add(f"#line {cfg_info['_LINE_']} \"{cfg_info['_FILE_']}\"")
            cfg1_out.add(cfg_info["DIRECTIVE"])

    cfg1_out.add("""
#ifdef INT64_MAX
  typedef int64_t signed_t;
  typedef uint64_t unsigned_t;
#else
  typedef int32_t signed_t;
  typedef uint32_t unsigned_t;
#endif
""")
    cfg1_out.add(f"#include \"{CFG1_OUT_TARGET_H}\"")
    cfg1_out.add("")
    from cfg import CFG1_MAGIC_NUM, CFG1_SIZEOF_SIGNED, CFG1_SIZEOF_INTPTR, CFG1_SIZEOF_CHARPTR
    cfg1_out.add(f"const uint32_t {CFG1_MAGIC_NUM} = 0x12345678;")
    cfg1_out.add(f"const uint32_t {CFG1_SIZEOF_SIGNED} = sizeof(signed_t);")
    cfg1_out.add(f"const uint32_t {CFG1_SIZEOF_INTPTR} = sizeof(intptr_t);")
    cfg1_out.add(f"const uint32_t {CFG1_SIZEOF_CHARPTR} = sizeof(char *);")

    # 値取得シンボルの処理
    for symbol_name, symbol_data in symbol_value_table.items():
        if "BOOL" in symbol_data:
            typ = "signed_t"
        elif "INTPTR" in symbol_data:
            typ = "uintptr_t"
        elif "SIGNED" in symbol_data:
            typ = "signed_t"
        else:
            typ = "unsigned_t"
        if "CONDITION" in symbol_data:
            cfg1_out.add(f"#if {symbol_data['CONDITION']}")
        cfg1_out.add(f"const {typ} {CFG1_PREFIX}{symbol_name} = "
                     f"({typ})({symbol_data['EXPR']});")
        if "ELSE_EXPR" in symbol_data:
            cfg1_out.add("#else")
            cfg1_out.add(f"const {typ} {CFG1_PREFIX}{symbol_name} = "
                         f"({typ})({symbol_data['ELSE_EXPR']});")
        if "CONDITION" in symbol_data:
            cfg1_out.add("#endif")
    cfg1_out.add()

    # ドメインIDの定義の生成
    for domain_name, domain_val in domain_id.items():
        if isinstance(domain_val, int) and domain_val > 0:
            cfg1_out.add(f"#define {domain_name} {domain_val}")
    cfg1_out.add()

    # 静的API／プリプロセッサディレクティブの処理
    for cfg_info in cfg_file_info:
        if "DIRECTIVE" in cfg_info:
            # 条件ディレクティブを出力
            if re.match(r'^#(ifdef|ifndef|if|endif|else|elif)\b',
                        cfg_info["DIRECTIVE"]):
                cfg1_out.add(f"#line {cfg_info['_LINE_']} \"{cfg_info['_FILE_']}\"")
                cfg1_out.add2(cfg_info["DIRECTIVE"])
        elif "CLSSTR" in cfg_info:
            # クラスIDを出力
            cfg1_out.add(f"#line {cfg_info['_LINE_']} \"{cfg_info['_FILE_']}\"")
            cfg1_out.add2(f"const signed_t {CFG1_PREFIX}clsid_{cfg_info['CLSIDX']}"
                          f" = (signed_t)({cfg_info['CLSSTR']});")
        elif "APINAME" in cfg_info:
            api_def = api_definition[cfg_info["APINAME"]]
            api_index = cfg_info["INDEX"]
            cfg1_out.add(f"#line {cfg_info['_LINE_']} \"{cfg_info['_FILE_']}\"")
            cfg1_out.add(f"const unsigned_t {CFG1_PREFIX}static_api_{api_index}"
                         f" = {api_index};")

            for api_param in api_def["PARAM"]:
                if "NAME" not in api_param:
                    continue
                param_name = api_param["NAME"]
                if param_name not in cfg_info:		# パラメータがない場合
                    continue
                param_data = cfg_info[param_name]

                if "ID_DEF" in api_param:
                    cfg1_out.add(f"#define {param_data}\t(<>)")
                elif "EXPTYPE" in api_param:
                    if "LIST" in api_param:
                        for i, p in enumerate(param_data, 1):
                            cfg1_out.add(f"#line {cfg_info['_LINE_']} "
                                         f"\"{cfg_info['_FILE_']}\"")
                            cfg1_out.add(f"const {api_param['EXPTYPE']} "
                                         f"{CFG1_PREFIX}valueof_"
                                         f"{param_name}_{api_index}_{i} = "
                                         f"({api_param['EXPTYPE']})({p});")
                    else:
                        cfg1_out.add(f"#line {cfg_info['_LINE_']} "
                                     f"\"{cfg_info['_FILE_']}\"")
                        cfg1_out.add(f"const {api_param['EXPTYPE']} "
                                     f"{CFG1_PREFIX}valueof_"
                                     f"{param_name}_{api_index} = "
                                     f"({api_param['EXPTYPE']})({param_data});")
            cfg1_out.add()


def Pass1(g):
    #
    #  タイムスタンプファイルの指定
    #
    g["timeStampFileName"] = CFG1_OUT_TIMESTAMP

    #
    #  値取得シンボルテーブルへの固定登録
    #
    g.setdefault("symbolValueTable", {
        "CHAR_BIT":  {"EXPR": "CHAR_BIT"},
        "SCHAR_MAX": {"EXPR": "SCHAR_MAX", "SIGNED": True},
        "SCHAR_MIN": {"EXPR": "SCHAR_MIN", "SIGNED": True},
        "UCHAR_MAX": {"EXPR": "UCHAR_MAX"},
        "CHAR_MAX":  {"EXPR": "CHAR_MAX",  "SIGNED": True},
        "CHAR_MIN":  {"EXPR": "CHAR_MIN",  "SIGNED": True},
        "SHRT_MAX":  {"EXPR": "SHRT_MAX",  "SIGNED": True},
        "SHRT_MIN":  {"EXPR": "SHRT_MIN",  "SIGNED": True},
        "USHRT_MAX": {"EXPR": "USHRT_MAX"},
        "INT_MAX":   {"EXPR": "INT_MAX",   "SIGNED": True},
        "INT_MIN":   {"EXPR": "INT_MIN",   "SIGNED": True},
        "UINT_MAX":  {"EXPR": "UINT_MAX"},
        "LONG_MAX":  {"EXPR": "LONG_MAX",  "SIGNED": True},
        "LONG_MIN":  {"EXPR": "LONG_MIN",  "SIGNED": True},
        "ULONG_MAX": {"EXPR": "ULONG_MAX"},
        "SIL_ENDIAN_BIG": {
            "EXPR": "true", "BOOL": True,
            "CONDITION": "defined(SIL_ENDIAN_BIG)"
        },
        "SIL_ENDIAN_LITTLE": {
            "EXPR": "true", "BOOL": True,
            "CONDITION": "defined(SIL_ENDIAN_LITTLE)"
        },
    })

    #
    #  静的APIテーブルへの固定登録
    #
    g.setdefault("apiDefinition", {
        "INCLUDE": {"PARAM": [{"NAME": "file", "STRING_LITERAL": True}]}
    })

    #
    #  静的APIテーブルの読み込み
    #
    _read_api_table_file(g)

    #
    #  値取得シンボルテーブルの読み込み
    #
    _read_symval_table(g)

    #
    #  システムコンフィギュレーションファイルの読み込み
    #
    g["cfgFileInfo"] = []
    g["dependencyFiles"] = list(g.get("configFileNames", []))
    g["domainId"] = {"TDOM_KERNEL": -1, "TDOM_NONE": -2}

    for cfg_file_name in g.get("configFileNames", []):
        CfgParser().parse_file(cfg_file_name, g)

    from cfg import error_flag as ef
    if ef:						# エラー発生時はabortする
        sys.exit(1)

    #
    #  ドメインIDの割当て処理
    #
    next_domain_id = 1
    domain_id = g["domainId"]
    for domain_name in list(domain_id.keys()):
        if domain_id[domain_name] is None:
            while next_domain_id in domain_id.values():
                next_domain_id += 1
            domain_id[domain_name] = next_domain_id
            if next_domain_id > 32:
                error_exit("too large number of user domains")
            next_domain_id += 1

    #
    #  オブジェクト識別名の重複のチェック
    #
    object_names = list(domain_id.keys())
    api_definition = g["apiDefinition"]
    cfg_file_info = g["cfgFileInfo"]
    for cfg_info in cfg_file_info:
        if "APINAME" in cfg_info:
            api_def = api_definition[cfg_info["APINAME"]]
            for api_param in api_def["PARAM"]:
                if "ID_DEF" in api_param:
                    obj_name = cfg_info.get(api_param["NAME"])
                    if obj_name in object_names:
                        error(
                            f"E_OBJ: {api_def.get('KEYPAR', '')} "
                            f"'{obj_name}' is duplicated in {cfg_info['APINAME']}",
                            f"{cfg_info['_FILE_']}:{cfg_info['_LINE_']}:")
                    object_names.append(obj_name)

    #
    #  cfg1_out.cの生成
    #
    _generate_cfg1_out_c(g)

    #
    #  依存関係の出力
    #
    dep_file_name = g.get("dependencyFileName")
    if dep_file_name is not None:
        if dep_file_name == "":
            dep_out = sys.stdout
        else:
            try:
                dep_out = open(dep_file_name, "w", encoding="utf-8")
            except (OSError, IOError) as e:
                sys.exit(str(e))
        dep_out.write(f"{CFG1_OUT_TIMESTAMP}:")
        for fn in g.get("dependencyFiles", []):
            dep_out.write(f" {fn}")
        dep_out.write("\n")
        if dep_file_name:
            dep_out.close()

    #
    #  パス2以降に引き渡す情報の定義
    #
    g["globalVars"] = [
        "globalVars",
        "apiDefinition",
        "symbolValueTable",
        "cfgFileInfo",
        "domainId",
    ]

    #
    #  パス2に引き渡す情報をファイルに生成
    #
    if not g.get("omitOutputDb"):
        save_vars = {v: g[v] for v in g["globalVars"] if v in g}
        with open(CFG1_OUT_DB, "wb") as f:
            pickle.dump(save_vars, f)
