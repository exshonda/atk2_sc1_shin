# -*- coding: utf-8 -*-
#
#  TOPPERS Configurator by Ruby
#
#  Copyright (C) 2015-2022 by Embedded and Real-Time Systems Laboratory
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#  Copyright (C) 2015 by FUJI SOFT INCORPORATED, JAPAN
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
#  $Id: srecord.py (converted from SRecord.rb by Claude Code Sonnet 4.6) $
#

import re
import sys


#
#		Sレコードファイル処理クラス
#

#
#  モトローラSレコード形式またはobjdumpコマンドによるダンプ形式のファ
#  イルの内容を変数に読み込み，要求された番地のデータを返す．
#
#  @dumpDataは，先頭番地をキーとし，その番地からのデータ（16進ダンプ形
#  式の文字列）を値とするハッシュである．連続する番地のデータは，1つに
#  まとめて格納する．
#
class SRecord:
    def __init__(self, file_name, fmt="srec"):
        self._dump_data = {}
        self.endian_little = True

        try:
            prev_address = 0
            prev_data = ""
            with open(file_name, "r", encoding="latin-1") as f:
                for line in f:
                    line = line.rstrip("\r\n")
                    # ファイルからデータを読み込む
                    if fmt == "srec":
                        address, data = self._read_line_srec(line)
                    elif fmt == "dump":
                        address, data = self._read_line_dump(line)
                    else:
                        print(f"Unknown file format: {fmt}", file=sys.stderr)
                        sys.exit(1)
                    if address is not None:
                        # データを格納する
                        if address == prev_address + len(prev_data) // 2:
                            prev_data += data
                        else:
                            if prev_data:
                                self.set_data(prev_address, prev_data)
                            prev_address = address
                            prev_data = data
            if prev_data:
                self.set_data(prev_address, prev_data)
        except (OSError, IOError) as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    # 行の読み込み（モトローラSレコード形式）
    def _read_line_srec(self, line):
        # データレコードにより分岐
        rec_type = line[:2] if len(line) >= 2 else ""
        if rec_type == "S1":
            # データ長（アドレス分[2byte]+チェックサム分1byteを減算）
            length = int(line[2:4], 16) - 2 - 1
            # アドレス（4文字=2byte）
            address = int(line[4:8], 16)
            # データ（この時点では文字列で取っておく）
            data = line[8:8 + length * 2]
        elif rec_type == "S2":
            # データ長（アドレス分[3byte]+チェックサム分1byteを減算）
            length = int(line[2:4], 16) - 3 - 1
            # アドレス（6文字=3byte）
            address = int(line[4:10], 16)
            # データ（この時点では文字列で取っておく）
            data = line[10:10 + length * 2]
        elif rec_type == "S3":
            # データ長（アドレス分[4byte]+チェックサム分1byteを減算）
            length = int(line[2:4], 16) - 4 - 1
            # アドレス（8文字=4byte）
            address = int(line[4:12], 16)
            # データ（この時点では文字列で取っておく）
            data = line[12:12 + length * 2]
        else:
            return None, ""
        return address, data

    # 行の読み込み（objdumpコマンドによるダンプ形式）
    def _read_line_dump(self, line):
        data = ""
        m = re.match(r'^ ([0-9a-f]+) (.*)$', line)
        if m:
            address = int(m.group(1), 16)
            rest = m.group(2)
            while True:
                m2 = re.match(r'^([0-9a-f]+) (.*)$', rest)
                if not m2:
                    break
                data += m2.group(1)
                rest = m2.group(2)
        else:
            return None, ""
        return address, data

    # データ取得
    def get_data(self, address, size):
        end_address = address + size
        for block, block_data in self._dump_data.items():
            block_end = block + len(block_data) // 2
            if block <= address and end_address <= block_end:
                offset = (address - block) * 2
                return block_data[offset:offset + size * 2]
        return None

    # データ書込み
    def set_data(self, address, data):
        if not data:
            return
        end_address = address + len(data) // 2
        to_delete = []
        for block, block_data in self._dump_data.items():
            end_block = block + len(block_data) // 2
            if end_block < address or end_address < block:
                # 重なりがない
                pass
            elif address < block:
                # 新規データの方が先頭番地が小さい
                # ここでは endAddress >= block が成立している
                offset = (end_address - block) * 2
                data = data + block_data[offset:]
                to_delete.append(block)
            else:
                # 登録済みデータの方が先頭番地が小さいか同じ
                offset = (address - block) * 2
                address = block
                block_data = block_data[:offset] + data + block_data[offset + len(data):]
                data = block_data
                to_delete.append(block)
        for k in to_delete:
            del self._dump_data[k]
        self._dump_data[address] = data

    # データのコピー
    def copy_data(self, from_address, to_address, size):
        copy_list = {}
        end_address = from_address + size
        for block, block_data in self._dump_data.items():
            end_block = block + len(block_data) // 2
            if end_block <= from_address or end_address <= block:
                # 重なりがない
                continue
            # 重なっている部分を抽出
            copy_from = max(block, from_address)
            copy_to = to_address + (copy_from - from_address)
            copy_size = min(end_block, end_address) - copy_from
            copy_list[copy_to] = self.get_data(copy_from, copy_size)
        for addr, d in copy_list.items():
            if d:
                self.set_data(addr, d)

    # 値としてのデータ取得
    def get_value(self, address, size, signed):
        target_data = self.get_data(address, size)
        if target_data is None:
            return None
        if self.endian_little:
            # リトルエンディアンの場合，バイトオーダーを逆にする
            reversed_data = ""
            # 後ろから2文字ずつ抜き出し，並び替える
            tmp = target_data
            while tmp:
                reversed_data += tmp[-2:]
                tmp = tmp[:-2]
            return_val = int(reversed_data, 16)
        else:
            return_val = int(target_data, 16)
        # 負の数の処理
        if signed and (return_val & (1 << (size * 8 - 1))) != 0:
            return_val -= (1 << (size * 8))
        return return_val

    # 文字列としてのデータ取得
    def get_string(self, address):
        result = ""
        data = self.get_data(address, 1)
        while data is not None:
            char_val = int(data, 16)
            if char_val == 0:
                break
            result += chr(char_val)
            address += 1
            data = self.get_data(address, 1)
        return result
