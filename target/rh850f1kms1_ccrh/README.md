# RH850/F1KM-S1 ターゲット (CC-RH / make ビルド)

Renesas **RH850/F1KM-S1 (R7F701684)** 向けの TOPPERS/ATK2 SC1 ターゲット
依存部．**Renesas CC-RH コンパイラ**と **Cygwin 上の GNU make** でビルド
する．

既存の [HSB RH850F1K ターゲット](../hsbrh850f1k_ccrh/README.md) を土台に，
F1KM-S1 のクロック構成・ログ出力 (RLIN32)・ハードウェアカウンタ (TAUB) へ
差し替えたもの．

| 項目 | 内容 |
|---|---|
| MCU | R7F701684 (RH850/F1KM-S1) |
| コア | RH850 G3KH (`CORETYPE = RH850G3KH`, `ARCH = V850E3V5`) |
| ツールチェイン | Renesas CC-RH V2.08.00 (`ccrh` / `rlink`) |
| ビルドディレクトリ | [`obj/obj_rh850f1kms1_ccrh/`](../../obj/obj_rh850f1kms1_ccrh/) |
| ログ出力 | RLIN32 (P10_14 = TX / P10_13 = RX)．115200bps, 8N1 |
| HW カウンタ | TAUB0 ch14 (差分) + ch15 (現在値)．625 kHz tick (1.6 us) |
| RAM 先頭 | `0xFEDE0000` |

## 1. ディレクトリ構成

HSB RH850F1K は `*_ccrh` (差分) と `*_gcc` (共通部) の 2 層オーバーレイ
だったが，本ターゲットは **1 ディレクトリで完結**する構成にしている．
GCC 版のターゲット依存部は無い．

| 層 | ディレクトリ | 内容 |
|---|---|---|
| ターゲット (MCU/ボード) | `target/rh850f1kms1_ccrh/` | 本ディレクトリ一式 |
| チップ (RH850/F1KM-S1) | `arch/v850_gcc/rh850_f1km.{c,h}`, `arch/v850_gcc/taub_hw_counter.c` | F1KM-S1 のクロック設定と TAUB ハードウェアカウンタ |
| チップ (共有) | `arch/v850_gcc/uart_rlin.{c,h}`, `v850.h`, `prc_*` | HSB RH850F1K と共用 |
| プロセッサ | `arch/v850_ccrh/` + `arch/v850_gcc/` | 変更なし (F1K と共用) |
| Compiler 抽象 | `arch/ccrh/` | 変更なし |

`arch/v850_ccrh/` (`start.asm`, `prc_support.asm` 等) と `arch/v850_gcc/`
のプロセッサ依存部は **F1K 版からそのまま流用**している．F1KM-S1 対応で
プロセッサ依存部に手を入れる必要はなかった．

## 2. ビルド

Cygwin の bash から:

```sh
export PATH="/cygdrive/c/Program Files (x86)/Renesas Electronics/CS+/CC/CC-RH/V2.08.00/bin:$PATH"
cd obj/obj_rh850f1kms1_ccrh
make -j4
```

### 最適化レベル

既定では他のビルドディレクトリと同じく最適化を行う
(`-g -g_line -Ospeed -Oinline_size`)．

実機でステップ実行して停止位置を追いたい場合は最適化を切る:

```sh
make OMIT_OPTIMIZATION=1 -j4
```

`-Onothing` では ccrh が `#pragma inline` を無視するため，`cfg1_out.c`
(pass1 のサイズ／オフセット測定専用で実行されないファイル) だけは
`OMIT_OPTIMIZATION` によらず常に最適化してコンパイルしている．そうしないと
インライン関数の実体がカーネル側シンボル (`kernel_tnum_hardcounter` 等)
を参照してしまい，`cfg1_out.elf` の単体リンクに失敗する．

なお CC-RH の評価版ライセンスが切れている環境では `-Ospeed` は警告
(`W0511187` / `W0511151`) とともに暗黙に `-Odefault` に落とされる．

生成物は HSB RH850F1K と同じ (`atk2-sc1.elf` / `.srec` / `.map` /
`Os_Lcfg.*` / `Os_Lcfg_asm.asm` / `asm_config.inc` / `offset.h` /
`libkernel.a` / `objs/`)．ビルドの仕組みは
[`../hsbrh850f1k_ccrh/README.md`](../hsbrh850f1k_ccrh/README.md) §3〜§4 と
共通．

**書き込み・実行は対象外**．生成した ELF / S レコードを CS+ 等で扱うこと．

## 3. HSB RH850F1K との差分

### クロック

| 項目 | HSB RH850F1K | RH850/F1KM-S1 |
|---|---|---|
| Main OSC | 16 MHz | **20 MHz** |
| PLL | `PLLE/PLLS/PLLC`，M=1/N=0x3B | **`PLL1E/PLL1S/PLL1C`，M=2/N=48 (VCO 480MHz → 120MHz)** |
| CPU クロック源 | CPLLOUT | **CPLL1OUT (PLL1)** |
| RLIN + TAUB クロック | RLIN は MainOSC，`CKSC_ILIN*` = 0xfff8a400/a800 | **PPLLCLK2，`CKSC_IPERI2S_*` = 0xfff8a300/a380 (RLIN と TAUB 共通)** |
| Sub OSC | あり (`EnableSubOSC()`) | **無し** |

> **C_ISO_PERI2 は RLIN と TAUB の共通ドメイン**
>
> F1K では RLIN 用 (C_ISO_LIN) と周辺用が別ドメインだったが，F1KM-S1 では
> `CKSC_IPERI2S_CTL` (0xfff8a300) / `CKSC_IPERI2D_CTL` (0xfff8a380) の
> 1 組で RLIN3n と TAUB0/TAUB1 の両方が決まる．**TAUB 用に別のレジスタを
> 設定してはならない**．移植元のコードには 0xfff8a280 を
> `CKSC_IPERI2S_CTL` とする定義も残っているが，そちらはどこからも使われて
> おらず，保護書き込みを行うと失敗する (`UC_PROTREGERROR`)．
> `arch/v850_gcc/rh850_f1km.h` では `CKSC_ILIN*` を 0xfff8a300/a380 への
> 別名として残してある．

### 保護コマンドレジスタ

F1KM-S1 は `CLMA2` ではなく `CLMA3`，ポート保護は `PPCMD0/8/9/10/11` のみ
(F1K は `PPCMD0/1/2/8/9/10/11/12/18/20`)．`PNO_*` の番号も詰め直して
いるので，`write_protected_reg()` のテーブルは F1KM 専用
(`arch/v850_gcc/rh850_f1km.c`)．

### ログ出力

| | HSB RH850F1K | RH850/F1KM-S1 |
|---|---|---|
| チャネル | RLIN31 (`RLIN3x_USE_PORT1`) | **RLIN32 (`RLIN3x_USE_PORT2`)** |
| 端子 | P10_12 / P10_11 | **P10_14 / P10_13** |
| 割込み番号 | 122 | **166** |
| ボーレート設定 | LINCLK 16 MHz，LWBR=0x00 / LBRP01=8 | **PCLK 40 MHz，LWBR=0xf2 / LBRP01=10** |

### ハードウェアカウンタ

| | HSB RH850F1K | RH850/F1KM-S1 |
|---|---|---|
| タイマ | TAUJ0 ch0 / ch1 (32bit) | **TAUB0 ch14 / ch15 (16bit)** |
| ベースアドレス | 0xFFE50000 | **0xFFE30000** |
| プリスケーラ | 分周なし | **64 分周 (`CK0 = 6`)** |
| tick | 16 MHz (62.5 ns) | **625 kHz (1.6 us)** |
| `OsCounterMaxAllowedValue` | 0x1FFFFFFF | **32000** |
| `OsCounterMinCycle` / `TicksPerBase` | 1000 / 10 | **1 / 1** |
| 差分タイマ割込み番号 | 80 (`TAUFJ0I0_INTNO`) | **156 (`TAUB0I0_INTNO` + 14)** |

**TAUB は 16bit カウンタ**なので，`TAUBCDR` / `TAUBCNT` へは 16bit
アクセス (`sil_wrh_mem` / `sil_reh_mem`) を，`TAUBTS` / `TAUBTT`
(16 チャネル分) へも 16bit アクセスを使っている (TAUJ 版は 32bit / 8bit)．

最大値が 32000 ティック (51.2 ms) なので，他ターゲットのような約 1 秒の
周期アラームは設定できない．`target_test.h` の `COUNTER_MIN_CYCLE` は
約 50 ms (31250 ティック) にしている．

## 4. 既知の制限

実機 (RH850/F1KM-S1) 上でサンプルプログラムの動作を確認済み．

- **CS+ でのビルドは非対応**．`configure.py` も非対応．make でビルドした
  ELF を CS+ でダウンロード／デバッグする運用．
- **書き込み・実行は make の対象外** (`make flash` 相当のターゲットはない)．
- RAM 先頭は `0xFEDE0000` 固定 (`Makefile.target` の `-start` オプション)．
  RAM 容量の異なる F1KM 品種を使う場合は要修正．
- LED 出力 (`hsbrh850f1k_led_output()`) はボード依存のため移植していない．

## 5. 参考

- ターゲット依存部ドキュメント: [`target_user.txt`](target_user.txt)
- プロセッサ依存部: [`../../arch/v850_ccrh/prc_user.txt`](../../arch/v850_ccrh/prc_user.txt), [`../../arch/v850_gcc/prc_user.txt`](../../arch/v850_gcc/prc_user.txt)
- RH850/F1KM: <https://www.renesas.com/ja/products/microcontrollers-microprocessors/rh850-automotive-mcus/rh850f1km-s1-automotive-general-purpose-microcontroller>
