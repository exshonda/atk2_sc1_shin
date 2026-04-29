# RA + FSP セットアップ手順 (clone 後の必須作業)

本ドキュメントは TOPPERS/ATK2 を **Renesas RA** ターゲットでビルドする
ために clone 後に必要な FSP 取込手順を説明する．対象は
`target/ek_ra6m5_llvm/` 等の **RA 系ターゲットすべて**．

> **役割分担**:
> - **ユーザ手作業必須** (生涯一度): Smart Configurator GUI で
>   `configuration.xml` を初回作成．本書 §3 の前段はこれが既にコミット
>   済の前提．未コミットの場合は [`../claude/phase2.md`](../claude/phase2.md)
>   §B を参照．
> - **clone 後の `rascc --generate` 実行**: ユーザが手で実行しても良いし，
>   Claude Code が Bash 経由で代行しても良い．いずれも同じコマンドを叩く
>   だけ．本書では人間が実行する形で書いているが，Claude が同コマンドを
>   `Bash` ツールで起動して構わない．

## 1. なぜ手作業が必要か

本リポジトリは Renesas FSP のソースツリー (`ra/`, `ra_cfg/`, `ra_gen/`)
を **コミットしていない**．代わりに **`configuration.xml` (Smart
Configurator のソース)** だけをコミットしている．clone した時点では FSP
ソースが存在しないためビルドできず，下記手順でローカル生成する必要がある．

理由:
- **配布サイズ削減**: FSP ソース全体は 50〜80 MB．多数のターゲット分を
  コミットすると リポジトリが肥大化する．
- **FSP バージョンアップ容易性**: `configuration.xml` を更新して `rascc
  --generate` を再実行するだけで，新バージョン FSP に切替可能．
- **ライセンス整合性**: ベンダ生成物を再配布せず，各ユーザが Renesas 提供
  ツールで取得する形にすることで配布範囲が明確．

`configuration.xml` は Smart Configurator が読込/書込みする設計上の真値
であり，Stack 構成・ピン割当・クロック設定等すべての情報を含む．

## 2. 必要なもの

| 項目 | バージョン | 備考 |
|---|---|---|
| **Renesas FSP + Smart Configurator** | **6.4.0** (2025-12 リリース) 推奨 | Renesas 公式から取得 |
| Renesas インストール先 | `C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/` (動作確認パス) | 任意の場所で可．後述の `RASCC` 環境変数で指定 |
| `rascc.exe` (コマンドライン版 Smart Configurator) | FSP 6.4.0 同梱 | `<install>/eclipse/rascc.exe` |
| arm-none-eabi-gcc 等のクロスツールチェーン | (本ドキュメントの対象外．プロジェクト README 参照) |  |

### 2.1 FSP のインストール (まだの場合)

1. Renesas 公式サイトで [Renesas Smart Configurator for RA](https://www.renesas.com/en/software-tool/flexible-software-package-fsp) もしくは [FSP Releases](https://github.com/renesas/fsp/releases) のいずれかから FSP 6.4.0 を取得．
   - **standalone Smart Configurator パッケージ** (推奨．軽量．本ドキュメントが想定): `setup_fsp_v6_4_0_rasc_v2025-12.exe`
   - e² studio 同梱版でも可．その場合 `rascc.exe` のパスは e² studio インストールディレクトリ内．
2. インストーラを実行．既定インストール先は `C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/`．
3. インストール後，下記が存在することを確認:
   - `<install>/eclipse/rascc.exe`
   - `<install>/internal/projectgen/ra/packs/Renesas.RA.6.4.0.pack` 他

### 2.2 rascc.exe のパスを通す (任意．Makefile に直書きでも可)

PowerShell:
```powershell
[Environment]::SetEnvironmentVariable('RASCC', 'C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rascc.exe', 'User')
```

または bash (msys2):
```sh
export RASCC="C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rascc.exe"
echo 'export RASCC="C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rascc.exe"' >> ~/.bashrc
```

## 3. 手順 (各ターゲット 1 回ずつ実施)

### 3.1 EK-RA6M5 ターゲットの場合

```sh
# (msys2 bash / PowerShell / cmd 何でも可．以下は msys2 例)
cd /c/home/proj/edge-ai/embcode/atk2_ra6m5/work/atk2_sc1_shin

# RASCC 未設定なら絶対パスで指定
RASCC="C:/Renesas/RA/sc_v2025-12_fsp_v6.4.0/eclipse/rascc.exe"

"$RASCC" \
    --generate \
    --device R7FA6M5BH3CFC \
    --compiler LLVMARM \
    target/ek_ra6m5_llvm/fsp/configuration.xml
```

実行が成功すると下記が `target/ek_ra6m5_llvm/` 配下に **新規作成** される:

```
target/ek_ra6m5_llvm/
├── ra/                       FSP ソース (約 60 MB)
│   └── fsp/
│       ├── inc/
│       └── src/bsp/, r_*/...
├── ra_cfg/
│   └── fsp_cfg/              bsp_cfg.h, bsp_clock_cfg.h ほか
└── ra_gen/
    ├── common_data.{c,h}
    ├── hal_data.{c,h}
    ├── pin_data.c
    └── vector_data.{c,h}
```

これらは `.gitignore` で git の追跡から除外されている．

### 3.2 他のターゲットを追加した場合

`target/<TARGET>/fsp/configuration.xml` がコミットされていれば，同じ手順で生成可能:

```sh
"$RASCC" --generate --device <DEVICE_PARTNUMBER> --compiler LLVMARM \
    target/<TARGET>/fsp/configuration.xml
```

`<DEVICE_PARTNUMBER>` 例:
- EK-RA6M5: `R7FA6M5BH3CFC`
- EK-RA6M4: `R7FA6M4AF3CFB`
- EK-RA4M2: `R7FA4M2AD3CFP`
- EK-RA8M1: `R7FA8M1AHECBD`

## 4. 検証

下記が満たされていることを確認:

- [ ] `target/<TARGET>/fsp/ra/fsp/inc/fsp_version.h` が存在し，
      `FSP_VERSION_MAJOR (6U)` `FSP_VERSION_MINOR (4U)` が定義されている．
- [ ] `target/<TARGET>/fsp/ra_cfg/fsp_cfg/bsp/bsp_cfg.h` が存在し，
      内部に `BSP_MCU_GROUP_*` および `BSP_MCU_*` の `#define` が含まれる．
- [ ] `target/<TARGET>/fsp/ra_gen/vector_data.c` が存在し，
      `g_interrupt_event_link_select[]` 配列が定義されている．
- [ ] `git status` で生成物が untracked にも staged にも現れない (gitignore 効果)．

## 5. ターゲットの構成変更 / FSP バージョンアップ

`configuration.xml` を編集 (Smart Configurator GUI 経由が安全) または別バージョン
の FSP に切替えた場合:

1. **GUI 編集の場合**: Smart Configurator (`rasc.exe` または e² studio) で
   `configuration.xml` を開いて編集 → `Generate Project Content` クリック．
2. **バージョン切替の場合**: 新バージョン FSP の `rascc.exe` で `--generate`
   再実行．`configuration.xml` の `<raConfiguration version="...">` を新版に
   合わせて手で書き換える必要がある場合あり．
3. 変更後，`configuration.xml` の差分を git にコミット．`ra/` `ra_cfg/`
   `ra_gen/` は引き続き untracked．

## 6. CI / 共同開発のヒント

- CI で本リポジトリをビルドする場合は，CI 起動時に同じ `rascc --generate` を
  実行する step を入れる．
- `configuration.xml` と生成物の整合チェックは:
  ```sh
  rascc --generate ... target/<TARGET>/fsp/configuration.xml
  git diff --exit-code target/<TARGET>/fsp/ra_cfg/ target/<TARGET>/fsp/ra_gen/
  ```
  生成物は untracked なので git diff には出ない．代わりに
  `git status target/<TARGET>/` で `untracked but expected` なファイルを
  確認するルールにする．

## 7. トラブルシューティング

| 症状 | 原因 / 対処 |
|---|---|
| `Cannot invoke "org.eclipse.core.runtime.IPath.append(String)" because the return value of "...getVersionedCMSISZoneResourceLocation(...)" is null` | `configuration.xml` のメタデータ不足．Smart Configurator GUI で 1 回開いて再保存し，再 `--generate` |
| `rascc.exe: command not found` | Renesas FSP がインストールされていない or パスが違う．§2.1 参照 |
| `--device R7FA6M5BH3CFC` の値が違う | `target/<TARGET>/fsp/configuration.xml` の `<device>` タグの値と一致させる．grep で確認可能 |
| 生成後にビルド時 `bsp_cfg.h: No such file or directory` | 生成物の場所が違う．`target/<TARGET>/fsp/ra_cfg/fsp_cfg/bsp/bsp_cfg.h` の存在を確認 |
| GitHub Actions / Linux 環境で実行したい | Renesas FSP は Windows 専用ではないが，`rascc.exe` は Windows 版のみ公式提供．Linux で動かす場合は Wine か e² studio Linux 版同梱の rascc を使う．具体的なサポートは Renesas 側の判断 |
| FSP 6.4.0 でなく 6.1.0 を使いたい | 任意の FSP 6.x で動作する想定．`configuration.xml` の `<raConfiguration version="...">` の値が一致するインストール版を使う．chip 層 Makefile.chip は FSP 6.x 共通 |

## 付録 A. configuration.xml の中身 (概要)

`<raConfiguration version="x.y.z">` 直下に以下が並ぶ:

- `<board id="..."/>` — 選択ボード ID (例: `board.ra6m5ek`)
- `<device id="R7FA6M5BH3CFC"/>` — 部品番号
- `<core>CM33</core>` — CPU コア
- `<package>...</package>` — パッケージ
- `<peripherals/>` — 各ペリフェラルの設定 (クロック，ピン)
- `<modules>...<module .../></modules>` — Stack 構成 (ATK2 では r_ioport, r_sci_uart, r_gpt 等)

各値は Smart Configurator GUI で編集するのが安全．直接編集すると schema 不整合
になりうるが，version 表記の更新程度なら手で OK．
