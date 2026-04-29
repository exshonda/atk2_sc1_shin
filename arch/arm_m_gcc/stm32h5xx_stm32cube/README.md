# STM32H5xx チップ依存部 (`arm_m_gcc/stm32h5xx_stm32cube`)

TOPPERS/ATK2 の **STMicroelectronics STM32H5xx** ファミリ向けチップ依存部．
ARM-M 共通プロセッサ依存部 (`arm_m_gcc/common`) と組み合わせて使用する．

ベンダ提供の **STM32CubeH5 HAL Driver** を同梱しており，UART/GPIO/RCC/PWR
等の低レベルアクセスはこの HAL を経由する方針 (タイマだけは HAL を
経由せず直接レジスタ操作で実装している)．

## 1. 対応するチップ

- **動作確認済み**: STM32H563ZI (NUCLEO-H563ZI)
- 同シリーズ (STM32H523/H533/H562/H573 等) でも条件によっては動作する見込み．
  ピン配置・クロック構成はターゲット依存部側で調整する．

## 2. 開発環境と動作確認バージョン

| ツール | 動作確認バージョン |
|---|---|
| arm-none-eabi-gcc | 13.3.1 / 14.3.1 |
| GNU Make | 4.4.1 |
| STMicroelectronics STM32CubeH5 HAL | 同梱 (HAL Driver V1.5.x 相当) |

## 3. コンパイルオプション

`Makefile.chip` で付与する CPU/HAL オプション:

| オプション | 内容 |
|---|---|
| `-mcpu=cortex-m33` | Cortex-M33 を指定 |
| `-mthumb` | Thumb 命令を使用 |
| `-mlittle-endian` | リトルエンディアン (STM32H5xx の標準) |
| `-DSTM32H563xx` | HAL ヘッダがチップを識別するための定義 |
| `-DUSE_HAL_DRIVER` | HAL ドライバ使用 |
| `-DINIT_MSP` | スタートアップで MSP を初期化 (`arm_m_gcc/common/start.S` が参照) |

`-mfloat-abi` および `-mfpu` は `Makefile.prc` 側が `FPU_USAGE` に応じて
付与する．本層では指定しない．Cortex-M33 の場合の値は:

```
-mfpu=fpv5-sp-d16
-D__TARGET_FPU_FPV5_SP    (FPU 有効時のみ)
```

## 4. ヘッダ・ライブラリ検索パス

`Makefile.chip` で `INCLUDES` に追加するパス:

```
$(CHIPDIR)
$(CHIPDIR)/STM32H5xx_HAL_Driver/Inc
$(CHIPDIR)/CMSIS/Device/ST/STM32H5xx/Include
$(CHIPDIR)/CMSIS/Include
```

ここで `$(CHIPDIR) = $(SRCDIR)/arch/arm_m_gcc/stm32h5xx_stm32cube`．

## 5. HAL モジュール構成

`stm32h5xx_hal_conf.h` (ターゲット依存部に配置) で以下を有効化:

| HAL モジュール | 用途 |
|---|---|
| `HAL_RCC_MODULE_ENABLED` | クロック構成 (`systemclock_config.c`) |
| `HAL_PWR_MODULE_ENABLED` | 電源制御 (VOS, LDO/SMPS 切替) |
| `HAL_FLASH_MODULE_ENABLED` | Flash latency 設定 |
| `HAL_GPIO_MODULE_ENABLED` | GPIO 初期化 (USART, LED 等) |
| `HAL_CORTEX_MODULE_ENABLED` | NVIC, SysTick 等 |
| `HAL_UART_MODULE_ENABLED` | USART3 経由のシリアル |

**`HAL_TIM_MODULE_ENABLED` は意図的に無効化** している．TIM2 (フリーラン
カウンタ) と TIM5 (ワンショットアラーム) は `target_hw_counter.c` で
レジスタ直接アクセスにて実装しており，HAL を経由する必要がないため．

ビルド時に必要な HAL ソースファイル (`Makefile.chip` の `KERNEL_COBJS`):

```
stm32h5xx_hal.o
stm32h5xx_hal_rcc.o          stm32h5xx_hal_rcc_ex.o
stm32h5xx_hal_pwr.o          stm32h5xx_hal_pwr_ex.o
stm32h5xx_hal_flash.o
stm32h5xx_hal_gpio.o
stm32h5xx_hal_cortex.o
stm32h5xx_hal_uart.o         stm32h5xx_hal_uart_ex.o
```

## 6. システム初期化フロー

1. **`SystemInit()`** (CMSIS, `system_stm32h5xx.c`)  
   フラッシュベクタテーブルから呼ばれる最早の C コード．VTOR 設定，FPU
   有効化準備等 (FPU 本格有効化は `prc_initialize` が行う)．

2. **`SystemClock_Config()`** (`systemclock_config.c`, ターゲット依存部)  
   PLL を構成して SYSCLK = 250MHz を確立．具体的なクロック設定は
   ターゲット依存部 README を参照．

3. **`prc_initialize()`** (`arm_m_gcc/common/prc_config.c`)  
   PendSV/SVCall/SysTick 優先度設定，ベクタテーブル登録，FPU 有効化
   (`FPU_USAGE` に応じた `CPACR` / `FPCCR` 設定)．

4. **`target_initialize()`** (ターゲット依存部 `target_config.c`)  
   GPIO/USART3/TIM2/TIM5 等の HW 初期化．

## 7. ファイル構成

```
arch/arm_m_gcc/stm32h5xx_stm32cube/
├── README.md                       このファイル
├── Makefile.chip                   Makefile チップ依存部 (HAL 列挙含む)
├── chip_config.h                   チップ依存設定 (target_config.h から取込)
├── CMSIS/
│   ├── Include/                    CMSIS Core ヘッダ (cmsis_gcc.h 等)
│   └── Device/ST/STM32H5xx/Include/ STM32H5xx チップ別ヘッダ
└── STM32H5xx_HAL_Driver/
    ├── Inc/                        HAL ヘッダ (stm32h5xx_hal_*.h)
    └── Src/                        HAL 実装 (stm32h5xx_hal_*.c)
```

`stm32h5xx_hal_conf.h` (HAL モジュール選択) はチップ層ではなくターゲット
依存部 (`target/nucleo_h563zi_gcc/stm32fcube/`) に配置している．これは
HAL の有効/無効選択がボードごとに変わり得るため．

## 8. 使用しないリソース

以下は HAL に含まれているがチップ依存部としては有効化しない:

- DMA: 未使用 (タイマ含めポーリング/割込みベース)
- I2C/SPI/CAN/USB/Ethernet: 未使用
- ADC/DAC/TIM (HAL 経由): 未使用
- LPUART/USB-OTG: 未使用

必要になった時点で `stm32h5xx_hal_conf.h` の該当モジュールを有効化し，
`Makefile.chip` の `KERNEL_COBJS` に対応 `.o` を追加する．

## 9. ターゲット依存部での設定項目

チップ依存部を使用するターゲット依存部 (例: `target/nucleo_h563zi_gcc/`)
は以下の項目を提供する必要がある:

- `stm32h5xx_hal_conf.h` (HAL モジュール選択)
- `system_stm32h5xx.c` の `SystemInit()` 実装 (テンプレートは ST 提供)
- `systemclock_config.c` で `SystemClock_Config()` を実装
- リンカスクリプト (Flash/SRAM レイアウト)
- ボード固有の GPIO/ペリフェラル初期化 (`target_config.c`)
- **TrustZone セキュリティ状態の宣言** (下記 §9.1)

### 9.1 TrustZone (TZEN オプションバイト) と EXC_RETURN

STM32H5 は ARMv8-M Cortex-M33 + TrustZone 拡張持ち．デバイスの動作状態は
**OFS1.TZEN オプションバイト**で決まる:

| TZEN | 状態 | 説明 |
|---|---|---|
| **0** | TrustZone 無効化 (Non-Secure 単一) | **STM32H5 出荷時デフォルト**．`Flash CR.PROG` 等の通常書込みでフラッシュへアクセス．本ポートの想定 |
| 1 | TrustZone 有効 (Secure / Non-Secure 分割) | 専用書込み手順 + secure/non-secure 別バイナリ．本ポートでは未対応 |

ATK2 例外復帰時の `EXC_RETURN` 値は実行状態に依存する．本チップ層を使う
ターゲット依存部 (`target/<target>/Makefile.target`) は **必ず**
下記いずれか 1 つを define すること:

- `TOPPERS_TZ_NS` : TZEN=0 (デフォルト) で運用するターゲット
   → 例外復帰 `EXC_RETURN = 0xFFFFFFBC` (Non-Secure)
- `TOPPERS_TZ_S`  : TZEN=1 で Secure ビルドにするターゲット
   → 例外復帰 `EXC_RETURN = 0xFFFFFFFD` (Secure ES=S=1)

定義例:

```make
# target/nucleo_h563zi_gcc/Makefile.target
CDEFS := $(CDEFS) -DTOPPERS_TZ_NS
```

両方未定義／両方定義は `arch/arm_m_gcc/common/arm_m.h` でビルド時 `#error`．

`nucleo_h563zi_gcc` (本ポートの基準ターゲット) は TZEN=0 想定で
`-DTOPPERS_TZ_NS` を `Makefile.target` で定義している．

## 10. 既知の制限

- TrustZone (TZEN=1, Secure 側) は未対応．本ポートは TZEN=0 (Non-Secure
  単一) のみ動作確認．`-DTOPPERS_TZ_S` 切替は arm_m.h レベルでは
  サポートしているが，HAL や Smart Configurator 設定はそれに合わせて
  調整が必要．
- HAL_TIM は無効化．TIM 駆動のアラームを HAL 経由で行いたい場合は
  別途対応が必要．
- バックアップドメイン / RTC は未使用．

## 11. バージョン履歴

- 2026-04: NUCLEO-H563ZI 用に新規追加．STM32CubeH5 HAL Driver v1.5.x 系を
  同梱．TIM/UART/GPIO/RCC/PWR/FLASH/CORTEX のみ有効．
