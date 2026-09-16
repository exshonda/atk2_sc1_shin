# HSB RH850F1K ターゲット (CC-RH / make ビルド)

Renesas **RH850/F1K (R7F701581)** 搭載ボード「HSB RH850F1K」向けの
TOPPERS/ATK2 SC1 ターゲット依存部．**Renesas CC-RH コンパイラ**と
**Cygwin 上の GNU make** でビルドする．Linux 版 CC-RH があれば
**Linux 上でもそのままビルドできる** (§3)．

このターゲットの依存部ファイルは，TOPPERS/ATK2-SC1 1.4.2 の RH850 移植版
(`atk2_sc1_f1k`) からそのまま持ち込んでいる．本リポジトリ側での変更は
ビルド方式の近代化 (Makefile / cfg の Python 版対応) に限られ，カーネル・
プロセッサ依存部・ターゲット依存部のソースコードには手を入れていない．

| 項目 | 内容 |
|---|---|
| ボード | HSB RH850F1K |
| MCU | R7F701581 (RH850/F1K) |
| コア | RH850 G3KH (`CORETYPE = RH850G3KH`, `ARCH = V850E3V5`) |
| ツールチェイン | Renesas CC-RH V2.08.00 (`ccrh` / `rlink`) |
| ビルドディレクトリ | [`obj/obj_hsbrh850f1k_ccrh/`](../../obj/obj_hsbrh850f1k_ccrh/) |
| ログ出力 | RLIN3 ポート 1 (115200bps, 8N1, フロー制御なし) |
| HW カウンタ | TAUJ0 (差分タイマ) + TAUJ1 (現在値タイマ)．`TIMER_CLOCK_HZ = 16MHz` |

## 1. ディレクトリ構成 (2 層オーバーレイ)

RH850 依存部は **gcc 版を共通部，ccrh 版を差分**とする 2 層構成になって
いる．`INCLUDES` と `vpath` で ccrh 側を先に探索するため，同名ファイルが
あれば ccrh 版が優先される．

| 層 | ccrh 差分 | 共通部 (gcc 版) |
|---|---|---|
| AUTOSAR Compiler 抽象 | `arch/ccrh/` (`Compiler.h`, `Compiler_Cfg.h`, `stdint.h`, `tool_cfg1_out.h`, `kernel_inline_symbols.h`) | `arch/gcc/` は使用しない |
| プロセッサ (V850/RH850) | `arch/v850_ccrh/` (`start.asm`, `prc_support.asm`, `prc_tool.c`, `Makefile.prc`, `prc.tf`, `prc_asm.tf`, `prc_offset.tf`, `prc_def.csv`) | `arch/v850_gcc/` (`prc_config.c/h`, `prc_kernel.h`, `prc_common.tf`, `prc_check.tf`, `v850.h`, `rh850_f1k.c/h` 等) |
| ターゲット (ボード) | `target/hsbrh850f1k_ccrh/` (`Makefile.target`, `target.tf`, `target_asm.tf`, `target_check.tf`, `target_offset.tf`, `target_cfg1_out.h`) | `target/hsbrh850f1k_gcc/` (`target_config.c/h`, `tauj_hw_counter.c`, `uart_rlin.c`, `*.arxml` 等) |

`arch/ccrh/` のうち CS+ プロジェクト生成用のスクリプト
(`configure/`, `gcc2ccrh.rb`, `pre_cfg.py`, `post_cfg.py`, `post_atk2.py`,
`updatepath.py` 等) は，本リポジトリでは CS+ ビルドを対象外としたため
持ち込んでいない．

## 2. 必要なもの

| ツール | 動作確認バージョン | 入手先 / 備考 |
|---|---|---|
| Renesas CC-RH | **V2.08.00** (オリジナルは V2.02.00 で確認) | CS+ 同梱．既定の場所は `C:/Program Files (x86)/Renesas Electronics/CS+/CC/CC-RH/V2.08.00/bin`．Linux 版は `/usr/local/Renesas/CC-RH/V2.08.00/bin` で確認 |
| Cygwin (make, nm, cmp, diff, coreutils) | GNU Make 4.4.1 / GNU nm (binutils) 2.46 | <https://www.cygwin.com/>．Linux ではディストリビューションの make / binutils でよい |
| Python 3 | 3.7 以降 (Cygwin の Python 3.9 で確認) | cfg (`cfg/cfg_py/cfg.py`) と `utils/makedep.py` に必要 |

`nm` は **Cygwin (GNU binutils) のもの**を使う．CC-RH が生成する ELF を
そのまま読めるため，専用ツールは不要．

> **CC-RH の評価版ライセンスについて**
> 評価期間が切れた CC-RH V2 では `W0511187` / `W0511151` / `W0561017` の
> 警告が出て，`-Ospeed` が暗黙に `-Odefault` に変更される．ビルド自体は
> 完了しオブジェクトも生成されるが，最適化レベルが指定と異なる点に注意．

## 3. ビルド

Cygwin の bash から:

```sh
export PATH="/cygdrive/c/Program Files (x86)/Renesas Electronics/CS+/CC/CC-RH/V2.08.00/bin:$PATH"
cd obj/obj_hsbrh850f1k_ccrh
make -j4
```

Linux (Linux 版 CC-RH をインストール済) の場合は `ccrh` / `rlink` が
`PATH` にあればよい:

```sh
export PATH="/usr/local/Renesas/CC-RH/V2.08.00/bin:$PATH"
cd obj/obj_hsbrh850f1k_ccrh
make -j4
```

> **標準ライブラリ (`rhs4n.lib`) の指定 — 環境変数 `HLNK_DIR` は不要**
> `rlink` は `-library=` の相対パスをカレントディレクトリと環境変数
> `HLNK_DIR` からしか探さない．オリジナルの `-library=lib\v850e3v5\rhs4n.lib`
> は Windows で `HLNK_DIR` に CC-RH のインストールルートが設定されている
> ことに依存していた (Linux では `HLNK_DIR` が無く，`\` を区切り文字とも
> 解釈しないため `F0563300:Cannot open file` で止まる)．
> 現在の `arch/v850_ccrh/Makefile.prc` は `PATH` 上の `ccrh` から
> インストールルート (`CCRH_ROOT`) を求め，`rhs4n.lib` の**絶対パス**を
> `-library=` に渡すので，Windows / Linux とも `HLNK_DIR` を設定する必要は
> ない．Cygwin では `cygpath -w` で Windows 形式
> (`C:\Program Files (x86)\...\rhs4n.lib`) に変換し，空白を含むので `""` で
> 囲んで渡す．`ccrh` を `PATH` に置かない場合や別の場所に入れた場合は
> `make CCRH_ROOT=/opt/Renesas/CC-RH/V2.08.00` のように明示する
> (`ccrh` が見つからないと make は `ccrh not found in PATH` で停止する)．

主な生成物 (ビルドディレクトリ直下):

| ファイル | 内容 |
|---|---|
| `atk2-sc1.elf` | ロードモジュール (ELF) |
| `atk2-sc1.srec` | S レコード (`rlink -form=stype`) |
| `atk2-sc1.map` / `atk2-sc1.syms` | リンクマップ / シンボル一覧 |
| `Os_Lcfg.c` / `Os_Lcfg.h` / `Os_Cfg.h` | cfg pass2 生成の C ソース・ヘッダ |
| `Os_Lcfg_asm.asm` | cfg pass2 生成の割込みベクタテーブル (EIINTTBL) |
| `asm_config.inc` | cfg pass2 生成のアセンブラ用 `.set` 定義 |
| `offset.h` | cfg pass3 生成のオフセット定義 (`prc_support.asm` が参照) |
| `libkernel.a` | カーネルライブラリ (`rlink -form=library=u`) |
| `objs/*.obj`, `objs/*.d` | 中間オブジェクトと依存関係ファイル |

その他のターゲット:

```sh
make clean        # 生成物の削除
make cleankernel  # libkernel.a とカーネルのオブジェクトのみ削除
```

**書き込み・実行は make の対象外**．生成した `atk2-sc1.elf` /
`atk2-sc1.srec` を CS+ 等で書き込むこと．

### CS+ プロジェクト (ダウンロード・デバッグ用)

[`obj/obj_hsbrh850f1k_ccrh/cs/hsbrh850f1l.mtpj`](../../obj/obj_hsbrh850f1k_ccrh/cs/hsbrh850f1l.mtpj)
は `atk2_sc1_f1k` から持ち込んだ CS+ プロジェクトファイル．デバイスは
`R7F701581`，ロードモジュールは 1 つ上のディレクトリの `atk2-sc1.elf` を
参照している．**ビルドは make で済ませた前提**で，CS+ はダウンロードと
デバッグにのみ使う想定 (ファイル名の `f1l` は移植元からの名残)．

本リポジトリではこのプロジェクト経由の動作は未確認．またエミュレータに
ついては §6 の制限も参照のこと．

## 4. ビルド方式の近代化 (オリジナルからの差分)

`atk2_sc1_f1k/obj/ccrh_make/Makefile` からの主な変更点:

| 項目 | オリジナル | 本リポジトリ |
|---|---|---|
| cfg | `cfg/cfg/cfg` (C++ ビルド済バイナリ) | `cfg/cfg_py/cfg.py` (Python 版, `USE_PY_CFG=1` が既定)．`USE_PY_CFG=0` で従来のバイナリに切替可 |
| 中間生成物 | ビルドディレクトリ直下に `*.obj` を散乱 | `objs/` 配下に集約 (`OBJDIR` / `DEPDIR`) |
| 依存関係生成 | `make depend` + `utils/makedep_ccrh` (Perl．**実体が存在せず機能していなかった**) | 各コンパイル後に `utils/makedep.py` が `objs/*.d` を自動生成．`make depend` は廃止 |
| 並列ビルド | 非対応 | `Os_Lcfg.timestamp` を軸に order-only 依存を整備して `make -j` 対応 |
| タイムスタンプ | `touch -r Os_Lcfg.c Os_Lcfg.timestamp` | `: > $@` |
| CS+ プロジェクト | `arch/ccrh/configure` で生成 | 非対応 (make のみ) |
| `configure` | Perl 版 `configure` で Makefile 生成 | 非対応．`obj/obj_hsbrh850f1k_ccrh/Makefile` を直接コミット |

### なぜ `ccrh -MMD` ではなく `utils/makedep.py` なのか

CC-RH V2 にも `-MMD -MP -MF= -MT=` はあるが，出力される依存先のパスが
**Windows 形式の絶対パス (バックスラッシュ区切り)** になるため Cygwin の
make が解決できない．さらにパスに非 ASCII 文字が含まれる場合は CP932 で
出力され，Shift_JIS の 2 バイト目に `0x5C` (バックスラッシュ) が現れる
ケースがあるので，文字列置換による変換も安全に行えない．

そこで `utils/makedep.py` が，Makefile が与えたのと同じ相対パス表現のまま
`#include` を再帰的に辿って `.d` を生成する．アセンブリソースの
`$include (file)` 形式にも対応しているので，`prc_support.asm` が
`offset.h` / `asm_config.inc` / `v850asm.inc` に依存することも正しく追跡
される．

## 5. cfg (ジェネレータ) 側の対応

RH850/CC-RH 構成を通すために，Python 版 cfg (`cfg/cfg_py/`) に以下を
修正した．いずれも他ターゲットにも効く一般的な不具合である．

| 修正 | 内容 |
|---|---|
| `atk2_bind.py`: シンボル名のアンダースコア | CC-RH は C シンボルに `_` を前置する (`_TOPPERS_cfg_TNUM_INT`)．`read_symbol_file()` で前置なしの別名も登録し，`TNUM_INT` 等が pass2 で解決できるようにした |
| `atk2_xml.py`: `valueof_*` マクロ名 | pass1 が出力する `TOPPERS_cfg_valueof_*` のシンボル名を **tfname リネーム後**に組み立てるよう順序を修正．従来はフルパス (`/AUTOSAR/EcucDefs/Os/OsIsr...`) が名前に入りコンパイルエラーになっていた (INTNO/INTPRI をマクロで書く構成でのみ顕在化) |
| `atk2_bind.py`: FLOAT 値の文字列化 | `OsSecondsPerTick` (`6.25e-08`) を `%f` 既定精度で丸めていたため `0.000000` となり，`OS_TICKS2NS_*` 等が 0 になっていた．`Decimal` で指数表現を展開するよう修正 (EK-RA6M5 の `4.0e-08` も同様に修正される) |

また，カーネル共通部の `kernel/kernel_rename.{h,def}` /
`kernel_unrename.h` に，`p_runisr` / `sus_os_cnt` / `sus_all_cnt` の
リネームと `TOPPERS_LABEL_ASM` 用のアンダースコア付きリネームが欠落して
いたため，`atk2_sc1_f1k` のものに戻した (V850 のアセンブリはこれらを
`_kernel_*` の形で参照する)．

## 6. 既知の差分・制限

- **CS+ でのビルドは非対応**．`arch/ccrh/configure/` 一式は持ち込んで
  いない．ダウンロード・デバッグ用のプロジェクトファイル
  (`obj/obj_hsbrh850f1k_ccrh/cs/`) のみ同梱している (§3 参照)．
- **`configure.py` は本ターゲットに非対応**．ビルドディレクトリの
  Makefile を直接使う．
- **書き込み・実行は未対応** (`make flash` 相当のターゲットはない)．
- 生成される `Os_Lcfg.c` は，C++ 版 cfg の出力とコメント内のタブ 1 個
  だけ差がある (`62U\t\t/*` vs `62U\t\t\t/*`)．値・コードは一致する．
- E1 エミュレータは Windows 11 のドライバの都合で使用できず，E2 Lite は
  RH850/F1K 非対応 (F1KH 以降のみ) のため，実機デバッグ手段は別途検討が
  必要．

## 7. 参考

- オリジナルのターゲット依存部ドキュメント: [`target_user.txt`](target_user.txt)
- プロセッサ依存部ドキュメント: [`../../arch/v850_ccrh/prc_user.txt`](../../arch/v850_ccrh/prc_user.txt), [`../../arch/v850_gcc/prc_user.txt`](../../arch/v850_gcc/prc_user.txt)
- RH850/F1K: <https://www.renesas.com/ja/products/microcontrollers-microprocessors/rh850-automotive-mcus/rh850f1k-automotive-general-purpose-microcontroller>
