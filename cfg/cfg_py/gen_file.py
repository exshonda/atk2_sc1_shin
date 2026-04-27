# -*- coding: utf-8 -*-
#
#  TOPPERS Configurator by Ruby
#
#  Copyright (C) 2015,2016 by Embedded and Real-Time Systems Laboratory
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#  Copyright (C) 2015 by FUJI SOFT INCORPORATED, JAPAN
#  Copyright (C) 2016 by APTJ Co., Ltd., JAPAN
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
#  $Id: gen_file.py (converted from GenFile.rb by Claude Code Sonnet 4.6) $
#

import os
import sys


#
#		ファイル作成クラス
#

#
# ファイルに書こうとした内容を変数に蓄積し，プログラムの終了時（output
# メソッドが呼ばれた時）にファイルに出力する．既にファイルが存在し，差
# 分がない場合は出力しない（タイムスタンプを更新しない）．
#
class GenFile:
    _file_data_hash = {}

    def __init__(self, file_name):
        self._file_name = file_name
        if file_name not in GenFile._file_data_hash:
            GenFile._file_data_hash[file_name] = ""

    # ファイルデータの末尾に文字列を追加する
    def append(self, code=""):
        GenFile._file_data_hash[self._file_name] += code

    # ファイルデータに1行追加する
    def add(self, code=""):
        GenFile._file_data_hash[self._file_name] += code + "\n"

    # ファイルデータに1行追加する(改行2回)
    def add2(self, code=""):
        self.add(code + "\n")

    # コメントヘッダを追加する
    def comment_header(self, comment):
        self.add("/*")
        for line in comment.split("\n"):
            self.add(" *  " + line)
        self.add2(" */")

    # ファイルデータを表示する
    def print_content(self):
        print(GenFile._file_data_hash[self._file_name])

    # 全ファイルを出力する
    @classmethod
    def output(cls):
        for file_name, file_data in cls._file_data_hash.items():
            # 既にファイルが存在し，差分がない場合は出力しない
            #（タイムスタンプを更新しない）
            if os.path.exists(file_name):
                with open(file_name, "r", encoding="utf-8") as f:
                    existing = f.read()
                if existing == file_data:
                    continue
            with open(file_name, "w", encoding="utf-8") as f:
                print(f"[{os.path.basename(sys.argv[0])}] Generated {file_name}")
                f.write(file_data)
