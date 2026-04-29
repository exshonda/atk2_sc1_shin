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
}

/* スタートアップ・エントリポイント */
STARTUP(start.o)
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

    . = ALIGN(4);
    _end = .;
    PROVIDE(end = .);

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
