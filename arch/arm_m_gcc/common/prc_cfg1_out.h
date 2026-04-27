/*
 *  TOPPERS ATK2
 *      Toyohashi Open Platform for Embedded Real-Time Systems
 *      Automotive Kernel Version 2
 *
 *  Copyright (C) 2008-2017 by Center for Embedded Computing Systems
 *              Graduate School of Information Science, Nagoya Univ., JAPAN
 *
 *  上記著作権者は，以下の(1)〜(4)の条件を満たす場合に限り，本ソフトウェ
 *  ア（本ソフトウェアを改変したものを含む．以下同じ）を使用・複製・改
 *  変・再配布（以下，利用と呼ぶ）することを無償で許諾する．
 *
 *  本ソフトウェアは，無保証で提供されているものである．
 */

/*
 *		cfg1_out.cをリンクするために必要なスタブの定義（ARM Cortex-M共通）
 */

int
main(void)
{
	return(0);
}
StackType * const	kernel_ostkpt = UINT_C(0x00);

/*
 *  オフセットファイルを生成するための定義
 */
const uint8			MAGIC_1 = UINT_C(0x12);
const uint16		MAGIC_2 = UINT_C(0x1234);
const uint32		MAGIC_4 = UINT_C(0x12345678);
