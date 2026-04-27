/*
 *  TOPPERS ATK2 - STM32H563ZI Linker Script
 *
 *  STM32H563ZI: 2MB Flash @ 0x08000000, 655KB SRAM @ 0x20000000
 *
 *  セクション配置:
 *    .vectors  - ARM割込みベクタテーブル (Flash先頭, 1024バイトアライン)
 *    .text     - コード (Flash)
 *    .rodata   - 読み取り専用データ (Flash)
 *    .data     - 初期化済みデータ (Flash→SRAM コピー)
 *    .bss      - ゼロ初期化データ (SRAM)
 */

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 2048K
    SRAM  (xrw) : ORIGIN = 0x20000000, LENGTH = 655K
}

/* スタートアップ・エントリポイント */
STARTUP(start.o)
ENTRY(_kernel_start)

/* SRAM 末尾 = 初期 MSP (CPU リセット時の割込みスタック頂点) */
_estack = ORIGIN(SRAM) + LENGTH(SRAM);

SECTIONS
{
    /*
     *  ARM ベクタテーブル (VTOR=0x08000000 でリセット時参照)
     *  kernel_vector_table[] が .vectors セクションに配置される
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

    . = ALIGN(4);
    _end = .;
    PROVIDE(end = .);
}
