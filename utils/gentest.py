#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  TOPPERS Software
#      Toyohashi Open Platform for Embedded Real-Time Systems
#
#  Copyright (C) 2007-2012 by Embedded and Real-Time Systems Laboratory
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#
#  本ソフトウェアは TOPPERS ライセンスに従う．
#  詳細はオリジナルの Perl 版 utils/gentest を参照．
#

"""テストプログラム生成ツール．

テスト記述ファイル (擬似コード) から，TASK/ALM/CPUEXC/EXTSVC ハンドラの
C コードを生成する．`check_point()` `check_ercd()` `check_assert()` 等の
テストヘルパマクロを呼ぶ形式．
"""

import re
import sys

# 戻り値受取り変数の引数位置 (1-origin)
PARAMPOS = {
    "get_pri": 2,
    "get_inf": 1,
    "ref_tsk": 2,
    "ref_tex": 2,
    "ref_sem": 2,
    "ref_flg": 2,
    "ref_dtq": 2,
    "ref_pdq": 2,
    "ref_mbx": 2,
    "ref_mtx": 2,
    "ref_mpf": 2,
    "get_tim": 1,
    "get_utm": 1,
    "ref_cyc": 2,
    "ref_alm": 2,
    "get_tid": 1,
    "iget_tid": 1,
    "get_ipm": 1,
}

PARAMTYPE = {
    "get_pri": "PRI",
    "get_inf": "intptr_t",
    "ref_tsk": "T_RTSK",
    "ref_tex": "T_RTEX",
    "ref_sem": "T_RSEM",
    "ref_flg": "T_RFLG",
    "ref_dtq": "T_RDTQ",
    "ref_pdq": "T_RPDQ",
    "ref_mbx": "T_RMBX",
    "ref_mtx": "T_RMTX",
    "ref_mpf": "T_RMPF",
    "get_tim": "SYSTIM",
    "get_utm": "SYSUTM",
    "ref_cyc": "T_RCYC",
    "ref_alm": "T_RALM",
    "get_tid": "ID",
    "iget_tid": "ID",
    "get_ipm": "PRI",
}

# 状態
_task_code = {}        # tskid -> C コード文字列
_task_count = {}       # tskid -> int (subtask 数)
_task_count_var = {}   # tskid -> "task1_count" 等
_task_var = {}         # tskid -> dict[type] = varname

_state = {
    "tskid": None,
    "indentstr": "\t",
    "startflag": False,
    "endflag": False,
}


def gen_var_def(svc_call):
    """サービスコールから変数定義を抽出して _task_var に追加."""
    m = re.match(r'^([a-z_]+)\((.*)\)$', svc_call)
    if not m:
        return
    svcname = m.group(1)
    params = [p.strip() for p in m.group(2).split(",")]
    pos = PARAMPOS.get(svcname)
    if pos is None:
        return
    if pos > len(params):
        return
    varname = params[pos - 1]
    if varname.startswith("&"):
        varname = varname[1:]
    typename = PARAMTYPE[svcname]
    _task_var.setdefault(_state["tskid"], {})[typename] = varname


def gen_svc_call(svc_call, error_code_string):
    tskid = _state["tskid"]
    indent = _state["indentstr"]
    code = _task_code.setdefault(tskid, "")
    code += indent + f"ercd = {svc_call};\n"
    gen_var_def(svc_call)

    if error_code_string == "":
        code += indent + "check_ercd(ercd, E_OK);\n"
    elif re.match(r'^->\s*noreturn$', error_code_string):
        pass  # 何もしない
    else:
        m = re.match(r'^->\s*([A-Z_]*)$', error_code_string)
        err = m.group(1) if m else error_code_string
        code += indent + f"check_ercd(ercd, {err});\n"
    _task_code[tskid] = code


def parse_line(line, infile):
    # バックスラッシュ継続行を結合
    while line.endswith("\\"):
        line = line[:-1]
        try:
            extra = next(infile).rstrip("\r\n")
        except StopIteration:
            break
        extra = re.sub(r'^\s*\*\s*', "", extra)
        extra = re.sub(r'\s*//.*$', "", extra)
        extra = re.sub(r'\s*\.\.\..*$', "", extra)
        line += extra

    # 行頭が `..` ならスキップ
    if line.startswith(".."):
        return

    # `==` で始まるセクション開始
    m = re.match(r'^==\s*((TASK|ALM|CPUEXC|EXTSVC)[0-9]*)(.*)$', line)
    if m:
        _state["startflag"] = True
        tskid = m.group(1)
        rest = m.group(3)

        m_tex = re.match(r'^-TEX(.*)$', rest)
        if m_tex:
            tskid = tskid + "-TEX"
            rest = m_tex.group(1)

        m_count = re.match(r'^-([0-9]+)(.*)$', rest)
        if m_count:
            tskcount = int(m_count.group(1))
            line3 = m_count.group(2)
            _state["indentstr"] = "\t\t"

            if tskid not in _task_count:
                _task_count[tskid] = 0
                # tskid -> count 変数名
                m_t = re.match(r'^TASK([0-9]*)$', tskid)
                m_tex2 = re.match(r'^TASK([0-9]*)-TEX$', tskid)
                m_alm = re.match(r'^ALM([0-9]*)$', tskid)
                m_cpu = re.match(r'^CPUEXC([0-9]*)$', tskid)
                m_ext = re.match(r'^EXTSVC([0-9]*)$', tskid)
                if m_t:
                    countvar = f"task{m_t.group(1)}_count"
                elif m_tex2:
                    countvar = f"tex_task{m_tex2.group(1)}_count"
                elif m_alm:
                    countvar = f"alarm{m_alm.group(1)}_count"
                elif m_cpu:
                    countvar = f"cpuexc{m_cpu.group(1)}_count"
                elif m_ext:
                    countvar = f"extsvc{m_ext.group(1)}_count"
                else:
                    countvar = ""
                _task_count_var[tskid] = countvar

            if tskcount == _task_count[tskid] + 1:
                code = _task_code.setdefault(tskid, "")
                if tskcount > 1:
                    code += "\n" + _state["indentstr"] + "check_point(0);\n\n"
                _task_count[tskid] = tskcount
                code += f"\tcase {tskcount}:"
                _task_code[tskid] = code
            elif tskcount != _task_count[tskid] and not line3.startswith("-"):
                sys.stderr.write(f"Subtask count error: {tskid}-{tskcount}\n")
        else:
            _state["indentstr"] = "\t"

        _state["tskid"] = tskid
        return

    if not _state["startflag"]:
        return

    # END
    m = re.match(r'^([0-9]+):\s*END$', line)
    if m:
        check_no = m.group(1)
        code = _task_code.setdefault(_state["tskid"], "")
        code += "\n" + _state["indentstr"] + f"check_finish({check_no});\n"
        _task_code[_state["tskid"]] = code
        _state["endflag"] = True
        return

    # `<n>:` プレフィックスがあれば check_point を打って残りを処理
    m = re.match(r'^([0-9]+):\s*(.*)', line)
    if m:
        check_no = m.group(1)
        line = m.group(2)
        code = _task_code.setdefault(_state["tskid"], "")
        code += "\n" + _state["indentstr"] + f"check_point({check_no});\n"
        _task_code[_state["tskid"]] = code

    indent = _state["indentstr"]
    code = _task_code.setdefault(_state["tskid"], "")

    if (m := re.match(r'^(assert\(.*\))$', line)):
        code += indent + f"check_{m.group(1)};\n"
    elif (m := re.match(r'^(state(_i)?\(.*\))$', line)):
        code += indent + f"check_{m.group(1)};\n"
    elif (m := re.match(r'^call\((.*)\)$', line)) or \
         (m := re.match(r'^DO\((.*)\)$', line)):
        code += "\n" + indent + f"{m.group(1)};\n"
    elif re.match(r'^MISSING$', line):
        pass
    elif (m := re.match(r'^RETURN((\(.*\))?)$', line)):
        code += "\n" + indent + f"return{m.group(1)};\n"
    elif (m := re.match(r'^GOTO\((.*)\)$', line)):
        code += "\n" + indent + f"goto {m.group(1)};\n"
    elif (m := re.match(r'^LABEL\((.*)\)$', line)):
        # ラベル直前のインデントは 1 段浅く
        ind = indent.rstrip("\t") if indent.endswith("\t") else indent
        code += "\n" + ind + f"{m.group(1)}:"
    elif (m := re.match(
            r'^([a-z_]+\(.*\))\s*(->\s*[A-Za-z_]*)?\s*$', line)):
        svc_call = m.group(1)
        err_str = m.group(2) or ""
        code += "\n"
        _task_code[_state["tskid"]] = code
        gen_svc_call(svc_call, err_str)
        return
    else:
        sys.stderr.write(f"Error: {line}\n")

    _task_code[_state["tskid"]] = code


def output_task(tskid, out):
    if _task_count.get(tskid):
        out.write(f"\nstatic uint_t\t{_task_count_var[tskid]} = 0;\n")

    if (m := re.match(r'^TASK([0-9]*)$', tskid)):
        out.write("\nvoid\n")
        out.write(f"task{m.group(1)}(intptr_t exinf)\n")
    elif (m := re.match(r'^TASK([0-9]*)-TEX$', tskid)):
        out.write("\nvoid\n")
        out.write(f"tex_task{m.group(1)}(TEXPTN texptn, intptr_t exinf)\n")
    elif (m := re.match(r'^ALM([0-9]*)$', tskid)):
        out.write("\nvoid\n")
        out.write(f"alarm{m.group(1)}_handler(intptr_t exinf)\n")
    elif (m := re.match(r'^CPUEXC([0-9]*)$', tskid)):
        out.write("\nvoid\n")
        out.write(f"cpuexc{m.group(1)}_handler(void *p_excinf)\n")
    elif (m := re.match(r'^EXTSVC([0-9]*)$', tskid)):
        out.write("\nER_UINT\n")
        out.write(f"extsvc{m.group(1)}_routine(intptr_t par1, intptr_t par2,"
                  " intptr_t par3,\n")
        out.write("\t\t\t\t\t\t\t\tintptr_t par4, intptr_t par5, ID cdmid)\n")

    out.write("{\n")
    out.write("\tER\t\tercd;\n")
    for typename, varname in _task_var.get(tskid, {}).items():
        sep = "\t\t" if len(typename) < 4 else "\t"
        out.write(f"\t{typename}{sep}{varname};\n")

    if _task_count.get(tskid):
        out.write(f"\n\tswitch (++{_task_count_var[tskid]}) {{\n")
    out.write(_task_code.get(tskid, ""))
    if _task_count.get(tskid):
        out.write("\n\t\tcheck_point(0);\n")
        out.write("\t}\n")
    else:
        out.write("\n")
    out.write("\tcheck_point(0);\n")
    if re.match(r'^EXTSVC[0-9]*$', tskid):
        out.write("\treturn(E_SYS);\n")
    out.write("}\n")


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: gentest.py <input>")

    infile_path = sys.argv[1]
    try:
        fp = open(infile_path, "r", encoding="utf-8", errors="surrogateescape")
    except OSError as e:
        sys.exit(f"Cannot open {infile_path}: {e}")

    with fp as f:
        for raw in f:
            if _state["endflag"]:
                break
            line = raw.rstrip("\r\n")
            line = re.sub(r'^\s*\*\s*', "", line)
            line = re.sub(r'\s*//.*$', "", line)
            line = re.sub(r'\s*\.\.\..*$', "", line)
            if not line:
                continue
            parse_line(line, f)

    out = sys.stdout
    for tskid in sorted(_task_code.keys()):
        output_task(tskid, out)


if __name__ == "__main__":
    main()
