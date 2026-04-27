# ARM Cortex-M 共通プロセッサ依存部 (`arm_m_gcc/common`)

TOPPERS/ATK2 の **ARMv7-M / ARMv8-M (Cortex-M3/M4/M33)** 系プロセッサ向け
共通依存部．現在 NUCLEO-H563ZI (Cortex-M33) で動作確認済み．

TOPPERS/ASP3 の同層 (`asp3/arch/arm_m_gcc/common`) の構造を踏襲しつつ，
ATK2 の SC1 用に合わせて再実装している．

## 1. 対応するアーキテクチャ

- ARMv8-M Cortex-M33 (動作確認済み: NUCLEO-H563ZI)
- ARMv7-M Cortex-M4 / Cortex-M33 (NoFP)（理論上対応．未検証）

ARMv6-M (Cortex-M0/M0+) は本ポートでは対応していない (BASEPRI が無いため
別実装が必要)．

## 2. 開発環境と動作確認バージョン

| ツール | 動作確認バージョン |
|---|---|
| arm-none-eabi-gcc | 13.3.1 (msys2) / 14.3.1 (STM32CubeIDE 2.1.1 同梱) |
| arm-none-eabi-binutils (objcopy/objdump/nm/ld/ar) | 2.42 系 |
| GNU Make | 4.4.1 |

## 3. コンパイルオプション

`Makefile.prc` で付与する基本オプション:

| オプション | 内容 |
|---|---|
| `-fno-common` | 不定義シンボルを共通領域に置かない |
| `-ffunction-sections -fdata-sections` | 関数/データを個別セクションに配置 |
| `-Wl,--gc-sections` | 未参照セクションをリンク時に除去 |
| `-nostdlib` | デフォルトのスタートアップを使わない (ATK2 自身の `start.S` を使用) |
| `-lgcc -lc -lnosys` | gcc ランタイム / 標準 C / 空 syscall |

CPU/FPU オプション (チップ依存部 `Makefile.chip` で `-mcpu=cortex-m33 -mthumb`，
`Makefile.prc` で `FPU_USAGE` に応じて `-mfloat-abi` / `-mfpu` を付与):

```
-mcpu=cortex-m33 -mthumb
[FPU 有効時]  -mfloat-abi=softfp -mfpu=fpv5-sp-d16
[FPU 無効時]  -mfloat-abi=soft
```

`-mfloat-abi=softfp` は ABI を soft 互換に保ったまま FPU 命令を生成させる
モード．デフォルトはこれだが `FPU_ABI=hard` で上書き可能．

## 4. FPU の利用方法

`Makefile.target` で `FPU_USAGE` を以下のいずれかに設定する．未指定なら
soft float (`-mfloat-abi=soft`) でビルドし FPU 命令は発行しない．

| `FPU_USAGE` | 定義される CDEF | 意味 |
|---|---|---|
| `FPU_NO_PRESERV` | `TOPPERS_FPU_ENABLE`, `TOPPERS_FPU_NO_PRESERV` | FPU を有効にするが OS は s16-s31 を保存/復帰しない．FPU を使うのは特定タスクのみ等の運用が前提． |
| `FPU_NO_LAZYSTACKING` | `TOPPERS_FPU_ENABLE`, `TOPPERS_FPU_NO_LAZYSTACKING`, `TOPPERS_FPU_CONTEXT` | FPU 有効．Lazy Stacking 無効．OS が s16-s31 を保存/復帰．例外入口で HW が常に拡張フレームを積む． |
| `FPU_LAZYSTACKING` | `TOPPERS_FPU_ENABLE`, `TOPPERS_FPU_LAZYSTACKING`, `TOPPERS_FPU_CONTEXT` | FPU 有効．HW Lazy Stacking 有効．FPU 未使用 ISR では拡張フレームを実体化しないため遅延が小さい．**推奨設定**． |
| (未指定) | (なし) | soft float． |

`prc_initialize()` で `CPACR.CP10/CP11 = 0b11` (Full Access) と
`FPCCR = FPCCR_INIT` を設定する．`FPCCR_INIT` は `arm_m.h` で
`FPU_USAGE` に対応した値が選択される．

## 5. 使用するシステムリソース

### CPU 例外 / システムハンドラ

| 例外 | 用途 | 優先度 |
|---|---|---|
| Reset (1) | スタートアップ (`start.S`) | (HW 固定) |
| NMI (2) | 既定ハンドラ | 既定 |
| HardFault (3) | 既定ハンドラ | 既定 |
| MemManage (4) | 既定ハンドラ | 既定 |
| BusFault (5) | 既定ハンドラ | 既定 |
| UsageFault (6) | 既定ハンドラ | 既定 |
| SVCall (11) | `svc_handler` (do_dispatch → Handler モード復帰用) | 0xE0 |
| PendSV (14) | `pendsv_handler` (遅延ディスパッチャ) | 0xFF (最低) |
| SysTick (15) | (本ポートでは未使用) | — |

PendSV を最低優先度に設定することで，全 ISR 処理完了後に tail-chain で
ディスパッチが走る．

### CPU レジスタ

| レジスタ | 用途 |
|---|---|
| `MSP` | 非タスクコンテキスト (例外/ISR) のスタック |
| `PSP` | タスクコンテキストのスタック |
| `BASEPRI` | OS 割込みマスク (CPU lock) |
| `PRIMASK` | 全割込みマスク (DisableAllInterrupts) |
| `CONTROL.SPSEL` | Thread モードでの SP 選択 (常に PSP=1 に設定) |
| `CONTROL.FPCA` | FPU 有効時のコンテキスト要否フラグ |

### スタートアップでの初期化

`start.S` は Reset ハンドラとして動作し，以下を行う:

1. `MSP` を初期化 (`__StackTop` シンボル)
2. `.data` セクションをフラッシュから RAM へコピー
3. `.bss` セクションをゼロクリア
4. `SystemInit()` を呼び出し (チップ依存部のクロック/FPU 初期化)
5. `cpsid i` で全割込み禁止状態にしてから C ランタイム (`__libc_init_array`)
6. `main()` を呼び出し

## 6. ディスパッチャ構造

ASP3 のディスパッチャ実装に倣い，以下のとおり実装している:

- **タスクコンテキストからのディスパッチ**: `do_dispatch(p_runtsk, p_schedtsk, &p_runtsk)`
  - `prc_config.h` の `dispatch()` マクロ経由で呼ばれる
  - `do_dispatch` が r4-r11 と LR と PSP を TCB に保存し `dispatcher_0` へ
  - `dispatcher_0` が次タスクの TCB.pc を判定:
    - EXC_RETURN 値ならば `svc #0` で Handler モードへ橋渡し → `svc_handler` で復帰
    - それ以外 (新規タスクの `start_r` または `do_dispatch` の戻り番地) は
      `dispatcher_1` で Thread モードのまま `pop {r4-r11}; bx r2`

- **割込み出口でのディスパッチ**: PendSV (`pendsv_handler`)
  - `interrupt_entry` で `p_runtsk != p_schedtsk` を検出時 PendSV をペンディング
  - PendSV ハンドラで EXC_RETURN ケースは通常の例外リターン，それ以外は
    偽の例外フレームを PSP に積んで例外リターンで Thread モードへ復帰

- **割込みエントリ**: `interrupt_entry`
  - ベクタテーブルから直接呼ばれる
  - `r4-r11` を MSP に退避 (AAPCS 上 C ISR が破壊するため)
  - `callevel_stat` を更新し ISR テーブルから C2ISR を呼び出し
  - 出口で `r4-r11` を復帰

## 7. ターゲット依存部での設定項目

ターゲット依存部 (またはチップ依存部) で以下のマクロを定義する:

| マクロ | 内容 |
|---|---|
| `TMIN_INTNO` / `TMAX_INTNO` / `TNUM_INT` | 割込み番号の最小/最大/個数 |
| `TBITW_IPRI` | 割込み優先度のビット幅 (STM32H5xx は 4) |
| `INIT_MSP` | 定義時はスタートアップで `MSP` を初期化 |

## 8. 主要ファイル一覧

```
arch/arm_m_gcc/common/
├── README.md                このファイル
├── Makefile.prc             Makefile プロセッサ依存部 (FPU_USAGE 処理含む)
├── arm_m.h                  ARMv7-M/v8-M ハードウェア資源定義
├── start.S                  リセットベクタ + スタートアップ
├── prc_support.S            ディスパッチャ / interrupt_entry / svc_handler /
│                            pendsv_handler / フック呼出スタック切替
├── prc_config.c             prc_initialize / x_config_int / NVIC 設定
├── prc_config.h             プロセッサ依存 API インライン関数とマクロ
│                            (CPU lock, dispatch マクロ, activate_context 他)
├── prc_insn.h               プロセッサ命令インライン関数 (msr/mrs 等)
├── prc_kernel.h             カーネル内部ヘッダ
├── prc_sil.h                SIL 用ヘッダ
├── prc_def.csv              cfg ツール用 offset テーブル定義
├── prc_offset.tf            offset.h 生成テンプレート
├── prc.tf                   pass2 で取り込むプロセッサ依存テンプレート
├── prc_check.tf             pass3 (チェック) 用テンプレート
├── prc_cfg1_out.h           cfg1_out.exe リンク用スタブ
├── prc_rename.h             内部識別名のリネーム
├── prc_unrename.h           リネーム解除
└── Platform_Types.h         AUTOSAR Platform 型
```

## 9. 既知の制限

- ARMv6-M (Cortex-M0/M0+) は未対応．
- TrustZone (Cortex-M33 Secure) は未対応．Non-Secure のみで動作．
- カスタムアイドル処理 (`TOPPERS_CUSTOM_IDLE`) は未実装．

## 10. バージョン履歴

- 2026-04: NUCLEO-H563ZI 用に ARMv8-M Cortex-M33 + FPU 対応を新規実装．
  ASP3 の同層を参考にディスパッチャを再構築 (`do_dispatch` ベース)．
