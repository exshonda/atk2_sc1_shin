# -*- coding: utf-8 -*-
import os
import sys

# テストから cfg_py 配下のモジュールを import 出来るよう sys.path に追加
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
