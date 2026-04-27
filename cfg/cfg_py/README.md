# ATK2 cfg ツール Python 移植版 (`cfg_py`)

TOPPERS/ATK2 のコンフィギュレータ `cfg.exe` (C++ 1.9.4 系) の Python 完全
移植版．`make USE_PY_CFG=1` (デフォルト) で本実装が選択される．

## ファイル構成

```
cfg/cfg_py/
├── README.md                このファイル
├── cfg.py                   エントリポイント (CLI / pass dispatch)
├── gen_file.py              ファイル生成ヘルパ (cmp-mv 含む)
├── srecord.py               S-record パーサ
├── pass1.py / pass2.py      ASP3 用 (ITRON .cfg / .trb)．ATK2 では未使用
├── atk2_xml.py              ARXML パース + Object/Parameter 木
├── atk2_pass1.py            pass1: ARXML+CSV → cfg1_out.c
├── atk2_pass2.py            pass2: cfg1_out.exe + .tf → Os_Lcfg.c/h, Os_Cfg.h
├── atk2_pass3.py            pass3: srec/syms + .tf → 検証 / offset.h
├── atk2_bind.py             macro_processor 用 binding (XML → context)
├── tf_lexer.py              .tf 字句解析
├── tf_parser.py             .tf 構文解析 (AST 構築)
├── tf_ast.py                AST ノード定義
├── tf_eval.py               AST 評価器
├── tf_value.py              .tf 値型 (element / var_t)
├── tf_builtin.py            組込み関数 (EQ, FORMAT, FOREACH 補助等)
├── tf_engine.py             .tf 評価統合 API
└── tests/                   pytest による単体・統合テスト
```

## XSD ファイルが不要な理由

C++ 版 `cfg.exe` には以下の 2 つの XSD ファイルが同梱されていた:

| ファイル | サイズ | 役割 |
|---|---|---|
| `AUTOSAR_4-0-3_STRICT.xsd` | 約 3.2 MB | AUTOSAR R4.0.3 仕様の主スキーマ |
| `xml.xsd` | 約 4.7 KB | W3C XML 名前空間 (`xml:lang` 等) のスキーマ |

**Python 移植版ではいずれも不要**．

### C++ 版が XSD を必要とした理由

C++ 版は **Apache Xerces-C++ + Boost** という *スキーマ検証付きパーサ*
を使っていた．[`cfg_1.9.4_src/toppers/xml/xml_xerces.cpp`](.)
の処理フロー:

```cpp
parser->setFeature(XMLUni::fgXercesSchema, doSchema);              // スキーマ機能 ON
parser->setFeature(XMLUni::fgXercesSchemaFullChecking, ...);
parser->setFeature(XMLUni::fgXercesIdentityConstraintChecking, ...);
...
ostream << get_global_string("XML_SchemaLocation") << " "
        << "/" << get_global_string("XML_Schema");                 // = AUTOSAR_4-0-3_STRICT.xsd
parser->setProperty(XMLUni::fgXercesSchemaExternalSchemaLocation, str);
```

`kernel.ini` で `XML_Schema = AUTOSAR_4-0-3_STRICT.xsd` がデフォルト設定
されており，Xerces はこの XSD を読み込んで:

- ARXML が AUTOSAR 4.0.3 仕様に準拠しているかを検証
- 要素の出現順・必須属性・型を検査
- 違反があれば `fatal` エラーを発出

### `xml.xsd` も連鎖的に必要だった

`AUTOSAR_4-0-3_STRICT.xsd` の 3 行目:

```xml
<xsd:import namespace="http://www.w3.org/XML/1998/namespace"
            schemaLocation="xml.xsd"/>
```

Xerces はこの `<xsd:import>` を見て **同ディレクトリの `xml.xsd`** を
読みに行く．本来は W3C サーバから取得すべきものだが，オフラインビルド
のために TOPPERS 側でローカルコピーを同梱していた．

依存関係:

```
cfg.exe
  └─ Xerces で AUTOSAR_4-0-3_STRICT.xsd をロード
       └─ <xsd:import> 経由で xml.xsd をロード
            └─ xml:lang 等の W3C 標準属性を解決
```

### Python 版がスキーマを読まない理由

Python 版は **`xml.etree.ElementTree` (標準ライブラリ)** という
*非検証パーサ* を使っている．[`atk2_xml.py`](atk2_xml.py):

```python
import xml.etree.ElementTree as ET
...
tree = ET.parse(path)              # well-formed チェックのみ
```

`xml.etree.ElementTree` は:

- XML として **構文的に正しいか** (well-formed) のみチェック
- スキーマ (XSD) を読まない
- 構造の妥当性は呼び出し側コードが要素・属性を辿ったときに暗黙にチェック

その結果，

- `AUTOSAR_4-0-3_STRICT.xsd` を必要としない (検証しないので不要)
- その依存である `xml.xsd` も連鎖的に不要

### 妥当性検査がなくなるわけではない

XSD 検証を省いても，ATK2 cfg の意味検査機能は **C++ 版とほぼ等価**:

| 検査項目 | C++ 版での実装 | Python 版での実装 |
|---|---|---|
| XML well-formedness | Xerces (XML パース時) | `xml.etree.ElementTree` (同) |
| AUTOSAR スキーマ準拠 | Xerces + AUTOSAR XSD | (実装せず) |
| 型 (`INT`/`STRING`/`REF`/...) チェック | `--api-table` 比較 (`cfg1_out.cpp:validate_type`) | `atk2_xml.py:validate_type` |
| 多重度 (`0..1`/`1..1`/`*`) チェック | `cfg1_out.cpp:validate_multiplicity` | `atk2_xml.py:validate_multiplicity` |
| 参照整合性 (`REF` ターゲット存在) | factory.cpp で名前解決 | `atk2_xml.py` の参照解決処理 |
| 重複オブジェクト名 | factory.cpp | `atk2_xml.py` |

ATK2 で扱う ARXML はユーザが手書きするか `utils/abrex/abrex.py` で
YAML から生成するもので，仕様外の構造になる経路が限られている．
本格的な XSD 検証が必要なケース (= 他ツール出力の妥当性確認等) では，
別途 `xmllint --schema` 等の外部ツールを使うのが現実的．

### 比較サマリ

| 項目 | C++ 版 (Xerces + XSD) | Python 版 (ET) |
|---|---|---|
| 必要ファイル | `cfg.exe` + `AUTOSAR_4-0-3_STRICT.xsd` + `xml.xsd` | `cfg.py` 一式 (XSD 不要) |
| 配布サイズ | 約 36 MB | 約 200 KB |
| 依存ランタイム | Windows 32-bit ネイティブ | Python 3.7+ (stdlib のみ) |
| パーサ種別 | スキーマ検証付き | well-formed のみ |
| ATK2 でのビルド速度 | (基準) | 数倍速い (XSD ロード/検証なし) |
| 出力一致性 | (基準) | バイト一致 (検証済) |

## 動作確認状況

- pass1 / pass2 / pass3 すべて C++ 版と同等の出力を生成
  (`cfg1_out.c`, `Os_Lcfg.c/h`, `Os_Cfg.h`, `offset.h`, `cfg2_out.tf`)
- 最終リンク後の `atk2-sc1.exe` の `objdump -d` 結果は C++ 版と完全一致
- 単体テスト・統合テストは [`tests/`](tests/) 配下に整備済

```sh
pip install pytest
cd cfg/cfg_py
pytest -v
```

## 必要なパッケージ

| パッケージ | 用途 | 備考 |
|---|---|---|
| (なし) | `cfg.py` 本体 | Python 標準ライブラリのみで動作 |
| `pytest` | 単体テスト実行 | `pip install pytest` (任意) |
