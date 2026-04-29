/*
 *  TOPPERS ATK2 - R7FA6M5BH (EK-RA6M5) Linker Script
 *
 *  R7FA6M5BH: 2MB Flash @ 0x00000000, 512KB SRAM @ 0x20000000
 *
 *  セクション配置:
 *    .vectors  - ATK2 cfg pass2 が出力する kernel_vector_table (Flash 先頭)
 *                FSP 同梱 startup.c の __VECTOR_TABLE は本層では使用しない
 *    .text     - コード (Flash)
 *    .rodata   - 読み取り専用データ (Flash)
 *    .data     - 初期化済みデータ (Flash → SRAM コピー)
 *    .bss      - ゼロ初期化データ (SRAM)
 *    /DISCARD/ - FSP system.c が置く可能性のある .fixed_vectors (= __VECTOR_TABLE)
 *                を破棄．ATK2 が独自に kernel_vector_table を出すため．
 *
 *  Phase 2 段階では Option Setting Memory (OFS0/OFS1/OSIS 等の
 *  bsp_linker.c が要求するセクション) は含まない．Phase 3 で
 *  KERNEL_COBJS に bsp_linker.o を追加するタイミングで .option_setting_*
 *  セクションを追加する．
 */

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x00000000, LENGTH = 2048K
    SRAM  (xrw) : ORIGIN = 0x20000000, LENGTH = 512K

    /*
     *  Option Setting Memory (RA6M5 Hardware Manual 6.2)
     *  CPU リセット後にハードウェアが直接読出す固定アドレス領域．
     *  bsp_linker.c が `.option_setting_*` セクションへ初期値を配置する．
     *  アドレスは fsp/memory_regions.lld の生成値と一致させる．
     */
    OFS0    (r) : ORIGIN = 0x0100A100, LENGTH = 4
    DUALSEL (r) : ORIGIN = 0x0100A110, LENGTH = 4
    OFS1    (r) : ORIGIN = 0x0100A180, LENGTH = 4
    BANKSEL (r) : ORIGIN = 0x0100A190, LENGTH = 4
    BPS     (r) : ORIGIN = 0x0100A1C0, LENGTH = 16
    PBPS    (r) : ORIGIN = 0x0100A1E0, LENGTH = 16
}

/*
 *  スタートアップ・エントリポイント
 *
 *  GNU ld の STARTUP(start.o) ディレクティブは ld.lld 非対応．
 *  代わりに obj/obj_ek_ra6m5/Makefile の link コマンドで
 *  $(HIDDEN_OBJS) (= objs/start.o) を明示的に渡す．
 */
ENTRY(_kernel_start)

/* SRAM 末尾 = 初期 MSP (リセット時の初期スタックポインタ) */
_estack    = ORIGIN(SRAM) + LENGTH(SRAM);
__StackTop = ORIGIN(SRAM) + LENGTH(SRAM);

SECTIONS
{
    /*
     *  ARM ベクタテーブル
     *  ATK2 cfg pass2 が Os_Lcfg.c に出す kernel_vector_table[] が
     *  .vectors セクションに配置される (VTOR 値はリセット時 0x00000000)．
     */
    .vectors :
    {
        KEEP(*(.vectors))
    } > FLASH

    /*
     *  コードセクション
     */
    .text :
    {
        *(.text)
        *(.text.*)
        *(.glue_7)
        *(.glue_7t)
    } > FLASH

    .rodata :
    {
        *(.rodata)
        *(.rodata.*)
        KEEP(*(.empty.*))
    } > FLASH

    .ARM.extab : { *(.ARM.extab* .gnu.linkonce.armextab.*) } > FLASH
    __exidx_start = .;
    .ARM.exidx : { *(.ARM.exidx* .gnu.linkonce.armexidx.*) } > FLASH
    __exidx_end = .;

    /*
     *  初期化済みデータ (Flash に格納, SRAM にコピー)
     */
    . = ALIGN(4);
    __idata_start = LOADADDR(.data);

    .data :
    {
        __data_start = .;
        *(.data)
        *(.data.*)
        . = ALIGN(4);
        __data_end = .;
    } > SRAM AT > FLASH

    __idata_end = __idata_start + SIZEOF(.data);

    /*
     *  ゼロ初期化データ
     */
    . = ALIGN(8);
    .bss :
    {
        __bss_start = .;
        /*
         *  g_main_stack を BSS 先頭に配置．FSP system.c が SystemInit
         *  内部で `__set_MSPLIM(&g_main_stack[0])` を実行する．
         *  ここで g_main_stack を BSS 先頭にすると MSPLIM = __bss_start
         *  (低位アドレス) となり，ATK2 の MSP (kernel_ostkpt) より
         *  必ず低位を保てて stack-overflow 偽検出を防げる．
         */
        KEEP(*(.bss.g_main_stack))
        *(.bss)
        *(.bss.*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > SRAM

    /*
     *  start.S 用シンボルエイリアス
     */
    PROVIDE(BSS_START   = __bss_start);
    PROVIDE(BSS_END     = __bss_end);
    PROVIDE(DATA_START  = __data_start);
    PROVIDE(DATA_END    = __data_end);
    PROVIDE(IDATA_START = __idata_start);
    PROVIDE(IDATA_END   = __idata_end);

    /* CMSIS / FSP system.c 互換エイリアス */
    PROVIDE(__StackLimit = __bss_end);

    /*
     *  CMSIS6 / FSP system.c は SCB->VTOR の暫定書込み先として
     *  `__VECTOR_TABLE` を参照するが，CMSIS6 マクロにより実体名は
     *  `__Vectors` に展開される．本ポートでは ATK2 cfg pass2 が
     *  生成する kernel_vector_table (.vectors セクション @ 0x00000000)
     *  をそのまま流用したいので，`__Vectors` をエイリアスとして
     *  PROVIDE する．これにより FSP の SCB->VTOR 書込みが
     *  no-op (= 既に 0x00000000) となり，SystemInit 中に発生する
     *  あらゆる例外も常に正しい ATK2 ハンドラへルーティングされる．
     */
    PROVIDE(__Vectors = kernel_vector_table);

    /*
     *  picolibc / ATfE TLS シンボル placeholder
     *  本ポートでは TLS (__thread 変数) を使用しないため，picolibc が要求
     *  する次のシンボルをすべて 0/空で提供する．_init_tls/_set_tls は
     *  動作はするが何も初期化しない．
     */
    PROVIDE(__tls_base              = 0);
    PROVIDE(__tdata_source          = 0);
    PROVIDE(__tdata_size            = 0);
    PROVIDE(__tbss_offset           = 0);
    PROVIDE(__tbss_size             = 0);
    PROVIDE(__arm32_tls_tcb_offset  = 0);

    /*
     *  bsp_linker.c が g_init_info に含めるリンカ生成シンボル群．
     *  本ポートは内蔵 RAM/Flash 単体構成のため，nocache / OSPI / TCM 系
     *  は全て空 (Base = Limit = 0) として g_init_info から空ループで参照
     *  されるだけにする．
     */
    /*
     *  bsp_linker.c の g_init_info テーブルが要求するシンボル．
     *  ATK2 の start.S が既に BSS クリア (BSS_START..BSS_END) と
     *  DATA コピー (IDATA_START..IDATA_END → DATA_START..) を行うため，
     *  FSP system.c の SystemInit() が g_init_info を駆使して BSS/DATA を
     *  二重に処理する必要は無い．
     *
     *  特に重要: __ram_zero$$Base..Limit を __bss_start..__bss_end に
     *  すると SystemInit 内の bzero が **現在実行中の OS スタック
     *  (kernel_ostack ⊂ BSS)** をゼロクリアしてしまい，戻りアドレスを
     *  含む生きたスタックフレームを破壊→ bx lr が NULL に飛んで
     *  HardFault．これを避けるため Base = Limit = 0 で空ループ化する．
     */
    PROVIDE(__ram_zero$$Base                = 0);
    PROVIDE(__ram_zero$$Limit               = 0);
    PROVIDE(__ram_zero_nocache$$Base        = 0);
    PROVIDE(__ram_zero_nocache$$Limit       = 0);
    PROVIDE(__ram_noinit_nocache$$Base      = 0);
    PROVIDE(__ram_noinit_nocache$$Limit     = 0);
    PROVIDE(__ram_tbss$$Base                = 0);
    PROVIDE(__ram_tbss$$Limit               = 0);
    PROVIDE(__ram_tdata$$Base               = 0);
    PROVIDE(__ram_tdata$$Limit              = 0);
    PROVIDE(__ram_tdata$$Load               = 0);
    PROVIDE(__ram_from_flash$$Base          = 0);
    PROVIDE(__ram_from_flash$$Limit         = 0);
    PROVIDE(__ram_from_flash$$Load          = 0);
    PROVIDE(__ram_from_qspi_flash$$Base     = 0);
    PROVIDE(__ram_from_qspi_flash$$Limit    = 0);
    PROVIDE(__ram_from_qspi_flash$$Load     = 0);
    PROVIDE(__ram_from_ospi0_cs1$$Base      = 0);
    PROVIDE(__ram_from_ospi0_cs1$$Limit     = 0);
    PROVIDE(__ram_from_ospi0_cs1$$Load      = 0);
    PROVIDE(__ram_from_data_flash$$Base     = 0);
    PROVIDE(__ram_from_data_flash$$Limit    = 0);
    PROVIDE(__ram_from_data_flash$$Load     = 0);
    PROVIDE(__ospi0_cs0_zero$$Base          = 0);
    PROVIDE(__ospi0_cs0_zero$$Limit         = 0);
    PROVIDE(__ospi0_cs0_zero_nocache$$Base  = 0);
    PROVIDE(__ospi0_cs0_zero_nocache$$Limit = 0);
    PROVIDE(__ospi0_cs0_noinit_nocache$$Base    = 0);
    PROVIDE(__ospi0_cs0_noinit_nocache$$Limit   = 0);
    PROVIDE(__ospi0_cs0_from_qspi_flash$$Base   = 0);
    PROVIDE(__ospi0_cs0_from_qspi_flash$$Limit  = 0);
    PROVIDE(__ospi0_cs0_from_qspi_flash$$Load   = 0);
    PROVIDE(__ospi0_cs0_from_ospi0_cs1$$Base    = 0);
    PROVIDE(__ospi0_cs0_from_ospi0_cs1$$Limit   = 0);
    PROVIDE(__ospi0_cs0_from_ospi0_cs1$$Load    = 0);
    PROVIDE(__ospi0_cs0_from_data_flash$$Base   = 0);
    PROVIDE(__ospi0_cs0_from_data_flash$$Limit  = 0);
    PROVIDE(__ospi0_cs0_from_data_flash$$Load   = 0);
    PROVIDE(__ospi0_cs0_from_flash$$Base        = 0);
    PROVIDE(__ospi0_cs0_from_flash$$Limit       = 0);
    PROVIDE(__ospi0_cs0_from_flash$$Load        = 0);

    . = ALIGN(4);
    _end = .;
    PROVIDE(end = .);

    /*
     *  Option Setting Memory (OFS0/OFS1/DUALSEL/BANKSEL/BPS/PBPS)
     *  bsp_linker.c が `.option_setting_*` セクションへ配置する初期値群．
     *  RA6M5 ハードウェアマニュアル 6.2 の固定アドレス領域に書き込む:
     *    OFS0    0x0100A100  (HOCO/IWDT/WDT/LVD 等の起動時設定)
     *    DUALSEL 0x0100A110  (Dual Bank モード選択)
     *    OFS1    0x0100A180  (HOCO 周波数等)
     *    BANKSEL 0x0100A190  (Bank 選択)
     *    BPS     0x0100A1C0  (Block Protect Setting)
     *    PBPS    0x0100A1E0  (Permanent Block Protect Setting)
     *  Sec 系 (OFS1_SEC 等) は本ポート (Flat Non-TrustZone) では不要．
     *  リセット時 CPU が直接これらアドレスから読出すので，必ず該当
     *  MEMORY 領域 (上で定義) に配置する．
     */
    .option_setting_ofs0    : { KEEP(*(.option_setting_ofs0))    } > OFS0
    .option_setting_dualsel : { KEEP(*(.option_setting_dualsel)) } > DUALSEL
    .option_setting_ofs1    : { KEEP(*(.option_setting_ofs1))    } > OFS1
    .option_setting_banksel : { KEEP(*(.option_setting_banksel)) } > BANKSEL
    .option_setting_bps     : { KEEP(*(.option_setting_bps))     } > BPS
    .option_setting_pbps    : { KEEP(*(.option_setting_pbps))    } > PBPS

    /*
     *  FSP 同梱 startup.c の __VECTOR_TABLE / g_main_stack / g_heap が
     *  万一リンクに含まれた場合に破棄するためのセクション．
     *  Phase 2 では startup.c は KERNEL_COBJS に入れていないため通常は
     *  不要だが，bsp_clocks.c 等から間接参照された場合の保険．
     */
    /DISCARD/ :
    {
        *(.fixed_vectors)
    }
}
