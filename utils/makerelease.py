#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  TOPPERS Software
#      Toyohashi Open Platform for Embedded Real-Time Systems
#
#  Copyright (C) 2006-2011 by Embedded and Real-Time Systems Laboratory
#              Graduate School of Information Science, Nagoya Univ., JAPAN
#
#  本ソフトウェアは TOPPERS ライセンスに従う．
#  詳細はオリジナルの Perl 版 utils/makerelease を参照．
#

"""個別パッケージのリリース tar.gz を作成するスクリプト．

`MANIFEST` (または引数で指定したファイル) を読んで，PACKAGE / VERSION
ディレクティブと収録ファイル一覧を集め，`RELEASE/<package>-<version>.tar.gz`
を生成する．
"""

import datetime
import os
import re
import subprocess
import sys

_state = {
    "package": None,
    "version": None,
    "e_package": False,
    "file_list": [],
    "file_set": set(),
    "prefix": None,
}


def gen_path(base, path):
    """`base + path` を計算しつつ `..` を畳む．"""
    while True:
        m = re.match(r'^\.\./(.*)$', path)
        if not m:
            break
        path = m.group(1)
        # base 末尾のディレクトリ 1 階層を削る
        base = re.sub(r'(/?)[^/]*/$', r'\1', base)
    return base + path


def read_file(filename):
    try:
        dirname_m = re.match(r'^(.*/)[^/]*$', filename)
        dirname = dirname_m.group(1) if dirname_m else ""
    except Exception:
        dirname = ""

    try:
        fp = open(filename, "r", encoding="utf-8", errors="surrogateescape")
    except OSError as e:
        sys.exit(f"Cannot open {filename}: {e}")

    with fp:
        for raw in fp:
            line = raw.rstrip("\r\n")
            line = re.sub(r'[ \t]*#.*$', "", line)
            if re.match(r'^[ \t]*$', line):
                continue

            m = re.match(r'^E_PACKAGE[ \t]+(.*)$', line)
            if m:
                if _state["package"]:
                    sys.exit("Duplicated E_PACKAGE directive.")
                _state["package"] = m.group(1)
                _state["e_package"] = True
                continue

            m = re.match(r'^PACKAGE[ \t]+(.*)$', line)
            if m:
                if _state["package"]:
                    if not _state["e_package"] and _state["package"] != m.group(1):
                        sys.exit("Inconsistent PACKAGE directive.")
                else:
                    _state["package"] = m.group(1)
                continue

            m = re.match(r'^VERSION[ \t]+(.*)$', line)
            if m:
                ver = m.group(1)
                if _state["version"]:
                    if not _state["e_package"] and _state["version"] != ver:
                        sys.exit("Inconsistent VERSION directive.")
                else:
                    if "%date" in ver:
                        today = datetime.date.today()
                        ver = ver.replace("%date", today.strftime("%Y%m%d"))
                    _state["version"] = ver
                continue

            m = re.match(r'^INCLUDE[ \t]+(.*)$', line)
            if m:
                read_file(gen_path(dirname, m.group(1)))
                continue

            # 普通のファイルエントリ
            entry = _state["prefix"] + "/" + dirname + line
            # `/foo/../` を畳む
            while True:
                new_entry = re.sub(r'/[^/]+/\.\./', '/', entry)
                if new_entry == entry:
                    break
                entry = new_entry
            if entry in _state["file_set"]:
                sys.exit(f"{entry} is duplicated.")
            _state["file_set"].add(entry)
            _state["file_list"].append(entry)


def main():
    cwd = os.getcwd()
    leaf = os.path.basename(cwd.rstrip(os.sep))
    _state["prefix"] = "./" + leaf

    arg1 = sys.argv[1] if len(sys.argv) >= 2 else "MANIFEST"
    arg1 = re.sub(r'^\./', '', arg1)

    read_file(arg1)

    if not _state["package"]:
        sys.exit("PACKAGE/E_PACKAGE directive not found.")
    if not _state["version"]:
        sys.exit("VERSION directive not found.")

    os.makedirs("RELEASE", exist_ok=True)
    archive_name = f"{_state['package']}-{_state['version']}.tar.gz"

    cmd = ["tar", "cvfz", f"RELEASE/{archive_name}", "-C", "..",
           *_state["file_list"]]
    rc = subprocess.run(cmd, check=False).returncode
    if rc != 0:
        sys.exit(rc)
    sys.stderr.write(f"== RELEASE/{archive_name} is generated. ==\n")


if __name__ == "__main__":
    main()
