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
#  $Id: pass2.py (converted from pass2.rb by Claude Code Sonnet 4.6) $
#

#
#		パス2の処理
#

import os
import sys
import re
import pickle

from gen_file import GenFile
from srecord import SRecord
from cfg import (
    CFG1_PREFIX, CFG1_OUT_DB, CFG2_OUT_DB,
    CFG1_MAGIC_NUM, CFG1_SIZEOF_SIGNED, CFG1_SIZEOF_INTPTR, CFG1_SIZEOF_CHARPTR,
    CFG1_OUT_SYMS, CFG1_OUT_SREC, CFG1_OUT_DUMP,
    NumStr, error_exit, error,
    read_symbol_file, define_symbol_value,
    make_trb_namespace, make_include_trb, error_flag
)


#
#  パス1の生成物の読み込み
#
class Cfg1Out:
    _symbol_address = {}
    _cfg1_srec = None

    #
    #  Sレコードファイルからシンボルの値を取り出す
    #
    @classmethod
    def get_symbol_value(cls, symbol, size, signed, g):
        if symbol in cls._symbol_address:
            return cls._cfg1_srec.get_value(cls._symbol_address[symbol], size, signed)
        return None

    #
    #  Sレコードファイルからシンボルの文字列を取り出す
    #
    @classmethod
    def get_symbol_string(cls, symbol, size_of_char_ptr, g):
        if symbol in cls._symbol_address:
            address = cls._cfg1_srec.get_value(cls._symbol_address[symbol],
                                               size_of_char_ptr, False)
            if address is not None:
                return cls._cfg1_srec.get_string(address)
        return None

    #
    #  パス1の生成物（静的API以外の部分）の読み込み
    #
    @classmethod
    def read(cls, g):
        # cfg1_out.symsの読み込み
        cls._symbol_address = read_symbol_file(CFG1_OUT_SYMS)

        # cfg1_out.srecまたはcfg1_out.dumpの読み込み
        if os.path.exists(CFG1_OUT_SREC):
            cls._cfg1_srec = SRecord(CFG1_OUT_SREC, "srec")
        else:
            cls._cfg1_srec = SRecord(CFG1_OUT_DUMP, "dump")

        # マジックナンバーの取得とエンディアンの設定
        if CFG1_MAGIC_NUM in cls._symbol_address:
            g["asmLabel"] = ""
            g["cfg1_prefix"] = CFG1_PREFIX
        elif "_" + CFG1_MAGIC_NUM in cls._symbol_address:
            g["asmLabel"] = "_"
            g["cfg1_prefix"] = "_" + CFG1_PREFIX
        else:
            error_exit(f"'{CFG1_MAGIC_NUM}' is not found in '{CFG1_OUT_SYMS}'")

        asm_label = g["asmLabel"]
        g.setdefault("globalVars", []).append("asmLabel")

        magic_data = cls._cfg1_srec.get_data(
            cls._symbol_address[asm_label + CFG1_MAGIC_NUM], 4)
        if magic_data == "12345678":
            g["endianLittle"] = False
        elif magic_data == "78563412":
            g["endianLittle"] = True
        else:
            error_exit(f"'{CFG1_MAGIC_NUM}' is invalid in "
                       f"'{CFG1_OUT_SREC}' or '{CFG1_OUT_DUMP}'")
        cls._cfg1_srec.endian_little = g["endianLittle"]
        g["globalVars"].append("endianLittle")

        # 固定出力した変数の取得
        g["sizeOfSigned"] = cls.get_symbol_value(
            asm_label + CFG1_SIZEOF_SIGNED, 4, False, g)
        g["sizeOfIntptr"] = cls.get_symbol_value(
            asm_label + CFG1_SIZEOF_INTPTR, 4, False, g)
        g["sizeOfCharPtr"] = cls.get_symbol_value(
            asm_label + CFG1_SIZEOF_CHARPTR, 4, False, g)

        cfg1_prefix = g["cfg1_prefix"]
        size_of_signed = g["sizeOfSigned"]
        size_of_intptr = g["sizeOfIntptr"]
        size_of_char_ptr = g["sizeOfCharPtr"]
        symbol_value_table = g.get("symbolValueTable", {})

        # 値取得シンボルの取得
        for symbol_name, symbol_data in symbol_value_table.items():
            sym = cfg1_prefix + symbol_name
            if "BOOL" in symbol_data:
                value = cls.get_symbol_value(sym, size_of_signed, True, g)
                if value is not None:
                    # C言語の真偽値をPythonの真偽値に変換して取り込む
                    symbol_data["VALUE"] = (value != 0)
            else:
                if "INTPTR" in symbol_data:
                    value = cls.get_symbol_value(sym, size_of_intptr,
                                                 "SIGNED" in symbol_data, g)
                else:
                    value = cls.get_symbol_value(sym, size_of_signed,
                                                 "SIGNED" in symbol_data, g)
                if value is not None:
                    symbol_data["VALUE"] = value

        # SILによるエンディアン定義のチェック
        big = symbol_value_table.get("SIL_ENDIAN_BIG", {})
        little = symbol_value_table.get("SIL_ENDIAN_LITTLE", {})
        if "VALUE" in big:
            if "VALUE" in little:
                error_exit("Both SIL_ENDIAN_BIG and SIL_ENDIAN_LITTLE are defined.")
            elif g["endianLittle"]:
                error_exit("Definition of SIL_ENDIAN_BIG seems to be wrong.")
        else:
            if "VALUE" in little:
                if not g["endianLittle"]:
                    error_exit("Definition of SIL_ENDIAN_LITTLE seems to be wrong.")
            else:
                pass					# 両方が未定義の場合のエラーチェックは，sil.hで実施する

        #
        #  コンフィギュレーション情報を格納するハッシュの初期化
        #
        g["cfgData"] = {}
        cls._objid_values = {}
        api_definition = g.get("apiDefinition", {})
        for api_name, api_def in api_definition.items():
            if "API" in api_def:
                api_sym = api_def["API"]
                if api_sym not in g["cfgData"]:
                    g["cfgData"][api_sym] = {}
            for api_param in api_def.get("PARAM", []):
                if "NAME" in api_param and "ID_DEF" in api_param:
                    if api_param["NAME"] not in cls._objid_values:
                        cls._objid_values[api_param["NAME"]] = {}
        g["globalVars"].append("cfgData")

    #
    #  パラメータの値を取り出す
    #
    #  生成スクリプト内で追加された静的APIの場合には，api_indexがNoneになる．
    #
    @classmethod
    def get_param_value(cls, param_name, param, api_index, index, api_param,
                        cfg_info, g):
        size_of_signed = g.get("sizeOfSigned")
        size_of_intptr = g.get("sizeOfIntptr")
        size_of_char_ptr = g.get("sizeOfCharPtr")
        cfg1_prefix = g.get("cfg1_prefix", CFG1_PREFIX)

        if "ID_DEF" in api_param:				# オブジェクト識別名（定義）
            value = cls._objid_values[param_name][param]
        elif "ID_REF" in api_param:			# オブジェクト識別名（参照）
            if param in cls._objid_values.get(param_name, {}):
                value = cls._objid_values[param_name][param]
            else:
                api_def = g["apiDefinition"][cfg_info["APINAME"]]
                prefix = "E_NOEXS" if "KEYPAR" in api_def else "E_ID"
                error(f"{prefix}: '{param}' in {cfg_info['APINAME']} is not defined",
                      f"{cfg_info['_FILE_']}:{cfg_info['_LINE_']}:")
                value = None
        elif "STRING" in api_param:			# 文字列パラメータ
            if api_index is not None:
                symbol = f"{cfg1_prefix}valueof_{param_name}_{api_index}{index}"
                return cls.get_symbol_string(symbol, size_of_char_ptr, g)
            else:
                return param
        elif "EXPTYPE" in api_param:			# 整数定数式パラメータ
            if api_index is not None:
                symbol = f"{cfg1_prefix}valueof_{param_name}_{api_index}{index}"
                if "INTPTR" in api_param:
                    value = cls.get_symbol_value(symbol, size_of_intptr,
                                                 "SIGNED" in api_param, g)
                else:
                    value = cls.get_symbol_value(symbol, size_of_signed,
                                                 "SIGNED" in api_param, g)
            else:
                if isinstance(param, NumStr):
                    return param
                else:
                    return NumStr(param)
        else:									# 一般定数式パラメータ
            return param
        return NumStr(value, param) if value is not None else None

    #
    #  指定したフェーズのためのパス1の生成物の読み込み
    #
    @classmethod
    def read_phase(cls, phase, g):
        cfg_file_info = g.get("cfgFileInfo", [])
        api_definition = g.get("apiDefinition", {})
        cfg1_prefix = g.get("cfg1_prefix", CFG1_PREFIX)
        input_objid = g.get("inputObjid", {})

        #
        #  オブジェクトIDの割当て
        #
        # 割り当てたオブジェクトIDは，_objid_valuesに保持する．_objid_valuesは，
        # 2重のdict（dictのdict）である．
        #
        # 具体的には，_objid_valuesは，オブジェクトIDのパラメータ名（例えば，セ
        # マフォIDであれば"semid"．これを保持する変数名は，obj_param_nameとする）
        # をキーとし，そのオブジェクトIDの割当て表（これを保持する変数名は，
        # objid_listとする）を値とするdictである．オブジェクトIDの割当て表は，
        # オブジェクト名（これを保持する変数名は，obj_nameとする）をキーとし，
        # そのID番号（これを保持する変数名は，objid_numberとする）を値とするdict
        # である．
        #
        # 例えば，セマフォSEM1のID番号が1の場合には，次のように設定される．
        #   _objid_values["semid"]["SEM1"] == 1
        #

        # ID番号割り当ての前処理
        for cfg_info in cfg_file_info:
            # 静的API以外は読み飛ばす
            if "APINAME" not in cfg_info:
                continue
            api_def = api_definition[cfg_info["APINAME"]]
            # 異なるフェーズの静的APIは読み飛ばす
            if api_def.get("PHASE") != phase:
                continue
            api_index = cfg_info.get("INDEX")
            if api_index is not None:
                # シンボルファイルに静的APIのインデックスが存在しなければ読み飛
                # ばす（ifdef等で消えた静的API）
                symbol = f"{cfg1_prefix}static_api_{api_index}"
                if symbol not in cls._symbol_address:
                    continue
            for api_param in api_def.get("PARAM", []):
                if "NAME" in api_param and "ID_DEF" in api_param:
                    obj_param_name = api_param["NAME"]
                    obj_name = cfg_info.get(obj_param_name)
                    if obj_name in input_objid:
                        # ID番号入力ファイルに定義されていた場合
                        cls._objid_values[obj_param_name][obj_name] = \
                            input_objid[obj_name]
                    else:
                        cls._objid_values[obj_param_name][obj_name] = None

        # ID番号の割当て処理
        for obj_param_name, objid_list in cls._objid_values.items():
            # 未使用のID番号のリスト（使用したものから消していく）
            unused = list(range(1, len(objid_list) + 1))

            # 割り当て済みのID番号の処理
            for obj_name, objid_num in objid_list.items():
                if obj_name in input_objid:
                    val = input_objid[obj_name]
                    if val in unused:
                        # 未使用のID番号のリストから削除
                        unused.remove(val)
                    else:
                        # ID番号入力ファイルで指定された値が不正
                        error_exit(f"value of '{obj_name}' in ID input file is illegal")

            # ID番号の割当て
            for obj_name in objid_list:
                if objid_list[obj_name] is None:
                    # 以下で，_objid_valuesを書き換えている
                    objid_list[obj_name] = unused.pop(0)

        #
        #  静的APIデータをコンフィギュレーションデータ（cfgData）に格納
        #
        for cfg_info in cfg_file_info:
            # 静的API以外は読み飛ばす
            if "APINAME" not in cfg_info:
                continue
            api_def = api_definition[cfg_info["APINAME"]]
            # 異なるフェーズの静的APIは読み飛ばす
            if api_def.get("PHASE") != phase:
                continue
            api_sym = api_def["API"]
            api_index = cfg_info.get("INDEX")
            if api_index is not None:
                # シンボルファイルに静的APIのインデックスが存在しなければ読み飛
                # ばす（ifdef等で消えた静的API）
                symbol = f"{cfg1_prefix}static_api_{api_index}"
                if symbol not in cls._symbol_address:
                    continue

            # パラメータの値をハッシュ形式に格納
            params = {}
            for api_param in api_def.get("PARAM", []):
                if "NAME" not in api_param:
                    continue
                param_name = api_param["NAME"]
                if param_name not in cfg_info:		# パラメータがない場合
                    continue
                param_data = cfg_info[param_name]
                if "LIST" in api_param:
                    params[param_name] = []
                    for i, p in enumerate(param_data, 1):
                        params[param_name].append(
                            cls.get_param_value(param_name, p, api_index,
                                                f"_{i}", api_param, cfg_info, g))
                else:
                    params[param_name] = cls.get_param_value(
                        param_name, param_data, api_index, "", api_param, cfg_info, g)

            # ドメインIDを追加
            if "DOMAIN" in cfg_info:
                params["domain"] = g["domainId"][cfg_info["DOMAIN"]]
            # クラスIDを追加
            if "CLSIDX" in cfg_info and cfg_info["CLSIDX"] in g.get("classId", {}):
                params["class"] = g["classId"][cfg_info["CLSIDX"]]

            # API名，ファイル名，行番号を追加
            params["apiname"] = cfg_info["APINAME"]
            params["_file_"] = cfg_info["_FILE_"]
            params["_line_"] = cfg_info["_LINE_"]

            # 登録キーを決定する
            if "KEYPAR" in api_def:
                key_param = params[api_def["KEYPAR"]]
                key = int(key_param)
                if key in g["cfgData"].get(api_sym, {}):
                    # 登録キーの重複
                    error(f"E_OBJ: {api_def['KEYPAR']} '{key_param}' "
                          f"is duplicated in {cfg_info['APINAME']}",
                          f"{cfg_info['_FILE_']}:{cfg_info['_LINE_']}:")
            else:
                key = len(g["cfgData"].get(api_sym, {})) + 1
            g["cfgData"].setdefault(api_sym, {})[key] = params

    #
    #  ID番号の割当て結果の上書き
    #
    @classmethod
    def set_objid_list(cls, obj_param_name, objid_list):
        cls._objid_values[obj_param_name] = objid_list

    #
    #  ID番号出力ファイルの生成
    #
    @classmethod
    def output_id(cls, file_name):
        id_out = GenFile(file_name)
        for obj_param_name, objid_list in cls._objid_values.items():
            for obj_name, objid_num in objid_list.items():
                id_out.add(f"{obj_name} {objid_num}")


#
#  ドメイン関連の処理
#
def _domain_proc(g):
    #
    #  ドメインデータ（domData）を生成
    #
    domain_id = g.get("domainId", {})
    dom_data = {}
    for domain_name, domain_val in domain_id.items():
        domid = NumStr(domain_val, domain_name)
        dom_data[domain_val] = {"domid": domid}
    g["domData"] = dom_data
    g.setdefault("globalVars", []).append("domData")


#
#  クラス関連の処理
#
def _class_proc(g, include_directories):
    #
    #  クラス定義ファイルを実行する
    #
    ns = make_trb_namespace(g, include_directories)
    ns.update(g)
    ns["IncludeTrb"] = make_include_trb(ns, include_directories)

    for class_file_name in g.get("classFileNames", []):
        ns["IncludeTrb"](class_file_name)

    #
    #  クラスのリストの加工
    #
    cls_data = ns.get("clsData", g.get("clsData", {}))
    for _, params in cls_data.items():
        bitmap = 0
        for prcid in params["affinityPrcList"]:
            bitmap |= (1 << (prcid - 1))
        params["affinityPrcBitmap"] = bitmap
    g["clsData"] = cls_data

    #
    #  クラス記述がエラーの場合に以降のエラーを防ぐために使用するクラス
    #
    first_key = next(iter(cls_data)) if cls_data else 0
    g["TCLS_ERROR"] = NumStr(first_key, "")

    #
    #  クラスID情報（classId）の生成
    #
    class_id = {}
    cfg1_prefix = g.get("cfg1_prefix", CFG1_PREFIX)
    size_of_signed = g.get("sizeOfSigned")
    for cfg_info in g.get("cfgFileInfo", []):
        if "CLSSTR" in cfg_info:
            symbol = f"{cfg1_prefix}clsid_{cfg_info['CLSIDX']}"
            value = Cfg1Out.get_symbol_value(symbol, size_of_signed, True, g)
            if value is not None:
                if value in cls_data:
                    class_id[cfg_info["CLSIDX"]] = NumStr(value, cfg_info["CLSSTR"])
                else:
                    error(f"E_ID: illegal class '{cfg_info['CLSSTR']}'",
                          f"{cfg_info['_FILE_']}:{cfg_info['_LINE_']}:")
                    # 以降のエラーの抑止
                    class_id[cfg_info["CLSIDX"]] = g["TCLS_ERROR"]
    g["classId"] = class_id
    g.setdefault("globalVars", []).append("classId")


def Pass2(g):
    #
    #  パス1から引き渡される情報をファイルから読み込む
    #
    with open(CFG1_OUT_DB, "rb") as f:
        saved = pickle.load(f)
    g.update(saved)

    #
    #  パス1の生成物（静的API以外の部分）を読み込む
    #
    Cfg1Out.read(g)

    from cfg import error_flag as ef
    if ef:					# エラー発生時はabortする
        sys.exit(1)

    #
    #  値取得シンボルをグローバル変数として定義する
    #
    define_symbol_value(g.get("symbolValueTable", {}), g)

    #
    #  ドメイン関連の処理
    #
    if g.get("supportDomain"):
        _domain_proc(g)

    #
    #  クラス関連の処理
    #
    if g.get("supportClass"):
        _class_proc(g, g.get("includeDirectories", []))

    #
    #  生成スクリプト（trbファイル）を実行する
    #
    Cfg1Out.read_phase(None, g)

    include_dirs = g.get("includeDirectories", [])
    ns = make_trb_namespace(g, include_dirs)
    ns.update(g)

    def symbol(sym, cont_flag=False):
        from cfg import symbol_func
        return symbol_func(g.get("romSymbol"), g.get("asmLabel", ""), sym, cont_flag)

    def peek(addr, size, signed=False):
        from cfg import peek_func
        return peek_func(g.get("romImage"), addr, size, signed)

    def bcopy(from_addr, to_addr, size):
        from cfg import bcopy_func
        bcopy_func(g.get("romImage"), from_addr, to_addr, size)

    def bzero(addr, size):
        from cfg import bzero_func
        bzero_func(g.get("romImage"), addr, size)

    ns["SYMBOL"] = symbol
    ns["PEEK"] = peek
    ns["BCOPY"] = bcopy
    ns["BZERO"] = bzero
    ns["Cfg1Out"] = Cfg1Out
    ns["IncludeTrb"] = make_include_trb(ns, include_dirs)

    for trb_file_name in g.get("trbFileNames", []):
        phase = None
        m = re.match(r'^(.+):(\w+)$', trb_file_name)
        if m:
            trb_file_name = m.group(1)
            Cfg1Out.read_phase(m.group(2), g)
            ns.update(g)
        ns["IncludeTrb"](trb_file_name)

    g.update({k: v for k, v in ns.items()
              if not k.startswith("__") and k not in ("GenFile", "NumStr")})

    #
    #  ID番号出力ファイルの生成
    #
    id_out = g.get("idOutputFileName")
    if id_out:
        Cfg1Out.output_id(id_out)

    #
    #  パス3に引き渡す情報をファイルに生成
    #
    if not g.get("omitOutputDb"):
        save_vars = {v: g[v] for v in g.get("globalVars", []) if v in g}
        with open(CFG2_OUT_DB, "wb") as f:
            pickle.dump(save_vars, f)
