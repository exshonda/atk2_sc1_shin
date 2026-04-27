/* This file is generated from prc_rename.def by genrename. */

#ifndef TOPPERS_PRC_RENAME_H
#define TOPPERS_PRC_RENAME_H

/*
 *  prc_config.c
 */
#define prc_hardware_initialize     kernel_prc_hardware_initialize
#define prc_initialize              kernel_prc_initialize
#define prc_terminate               kernel_prc_terminate
#define x_config_int                kernel_x_config_int
#define default_int_handler         kernel_default_int_handler

/*
 *  Os_Lcfg.c (cfg tool が生成)
 */
#define tmin_basepri                kernel_tmin_basepri
#define isr_tbl                     kernel_isr_tbl
#define isr_p_isrcb_tbl             kernel_isr_p_isrcb_tbl
#define vector_table                kernel_vector_table

/*
 *  prc_support.S
 */
#define interrupt_entry             kernel_interrupt_entry
#define pendsv_handler              kernel_pendsv_handler
#define svc_handler                 kernel_svc_handler
#define do_dispatch                 kernel_do_dispatch
#define start_dispatch              kernel_start_dispatch
#define exit_and_dispatch           kernel_exit_and_dispatch
#define start_r                     kernel_start_r
#define stack_change_and_call_func_1  kernel_stack_change_and_call_func_1
#define stack_change_and_call_func_2  kernel_stack_change_and_call_func_2

#endif /* TOPPERS_PRC_RENAME_H */
