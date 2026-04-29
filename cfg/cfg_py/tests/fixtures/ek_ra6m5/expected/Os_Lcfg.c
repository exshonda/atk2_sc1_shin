/* Os_Lcfg.c */
#include "kernel/kernel_int.h"
#include "Os_Lcfg.h"

#ifndef TOPPERS_EMPTY_LABEL
#define TOPPERS_EMPTY_LABEL(x, y) x y[0]
#endif

/*
 *  Default Definitions of Trace Log Macros
 */

#ifndef LOG_ISR_ENTER
#define LOG_ISR_ENTER(isrid)
#endif /* LOG_ISR_ENTER */

#ifndef LOG_ISR_LEAVE
#define LOG_ISR_LEAVE(isrid)
#endif /* LOG_ISR_LEAVE */

/*
 *  Include Directives (#include)
 */

#include "sample1.h"
#include "target_serial.h"
#include "target_hw_counter.h"

const AlarmType					kernel_tnum_alarm				= TNUM_ALARM;
const CounterType				kernel_tnum_counter			= TNUM_COUNTER;
const CounterType				kernel_tnum_hardcounter		= TNUM_HARDCOUNTER;
const ISRType					kernel_tnum_isr2				= TNUM_ISR2;
const ResourceType				kernel_tnum_stdresource		= TNUM_STD_RESOURCE;
const TaskType					kernel_tnum_task				= TNUM_TASK;
const TaskType					kernel_tnum_exttask			= TNUM_EXTTASK;
const AppModeType				kernel_tnum_appmode			= TNUM_APP_MODE;
const ScheduleTableType			kernel_tnum_scheduletable		= TNUM_SCHEDULETABLE;
const ScheduleTableType			kernel_tnum_implscheduletable	= TNUM_IMPLSCHEDULETABLE;


/****** Object TASK ******/

static StackType kernel_stack_MainTask[COUNT_STK_T(592U)];
static StackType kernel_stack_Task2[COUNT_STK_T(592U)];
static StackType kernel_stack_Task3[COUNT_STK_T(592U)];
static StackType kernel_stack_Task6[COUNT_STK_T(592U)];
static StackType kernel_stack_Task7[COUNT_STK_T(592U)];
static StackType kernel_stack_Task8[COUNT_STK_T(592U)];
static StackType kernel_shared_stack_1[COUNT_STK_T(592U)];
static StackType kernel_shared_stack_4[COUNT_STK_T(592U)];
static StackType kernel_shared_stack_6[COUNT_STK_T(592U)];
static StackType kernel_shared_stack_9[COUNT_STK_T(592U)];
static StackType kernel_shared_stack_15[COUNT_STK_T(592U)];

const TINIB kernel_tinib_table[TNUM_TASK] = {
	{
		&TASKNAME(MainTask),
		ROUND_STK_T(592U),
		kernel_stack_MainTask,
		1,
		0,
		(1U) - 1U,
		0x00000007U
	},
	{
		&TASKNAME(Task2),
		ROUND_STK_T(592U),
		kernel_stack_Task2,
		8,
		8,
		(1U) - 1U,
		0x00000000U
	},
	{
		&TASKNAME(Task3),
		ROUND_STK_T(592U),
		kernel_stack_Task3,
		3,
		3,
		(1U) - 1U,
		0x00000004U
	},
	{
		&TASKNAME(Task6),
		ROUND_STK_T(592U),
		kernel_stack_Task6,
		2,
		0,
		(1U) - 1U,
		0x00000000U
	},
	{
		&TASKNAME(Task7),
		ROUND_STK_T(592U),
		kernel_stack_Task7,
		2,
		0,
		(1U) - 1U,
		0x00000000U
	},
	{
		&TASKNAME(Task8),
		ROUND_STK_T(592U),
		kernel_stack_Task8,
		2,
		0,
		(1U) - 1U,
		0x00000000U
	},
	{
		&TASKNAME(HighPriorityTask),
		ROUND_STK_T(592U),
		kernel_shared_stack_15,
		0,
		0,
		(1U) - 1U,
		0x00000000U
	},
	{
		&TASKNAME(NonPriTask),
		ROUND_STK_T(592U),
		kernel_shared_stack_1,
		14,
		0,
		(8U) - 1U,
		0x00000000U
	},
	{
		&TASKNAME(Task1),
		ROUND_STK_T(592U),
		kernel_shared_stack_4,
		11,
		11,
		(8U) - 1U,
		0x00000002U
	},
	{
		&TASKNAME(Task4),
		ROUND_STK_T(592U),
		kernel_shared_stack_6,
		9,
		6,
		(5U) - 1U,
		0x00000000U
	},
	{
		&TASKNAME(Task5),
		ROUND_STK_T(592U),
		kernel_shared_stack_9,
		6,
		6,
		(5U) - 1U,
		0x00000000U
	}
};

TCB kernel_tcb_table[TNUM_TASK];


/****** Object COUNTER ******/

const CNTINIB kernel_cntinib_table[TNUM_COUNTER] = {
	{ 2147483647U, (2147483647U * 2U) + 1U, 25000U, 25U },
	{ 99U, (99U * 2U) + 1U, 10U, 10U },
	{ 99U, (99U * 2U) + 1U, 10U, 10U },
	{ 99U, (99U * 2U) + 1U, 10U, 10U },
	{ 99U, (99U * 2U) + 1U, 10U, 10U }
};

CNTCB kernel_cntcb_table[TNUM_COUNTER];
const HWCNTINIB kernel_hwcntinib_table[TNUM_HARDCOUNTER] = 
{
	{
		&init_hwcounter_MAIN_HW_COUNTER,
		&start_hwcounter_MAIN_HW_COUNTER,
		&stop_hwcounter_MAIN_HW_COUNTER,
		&set_hwcounter_MAIN_HW_COUNTER,
		&get_hwcounter_MAIN_HW_COUNTER,
		&cancel_hwcounter_MAIN_HW_COUNTER,
		&trigger_hwcounter_MAIN_HW_COUNTER,
		&int_clear_hwcounter_MAIN_HW_COUNTER,
		&int_cancel_hwcounter_MAIN_HW_COUNTER,
		&increment_hwcounter_MAIN_HW_COUNTER,
		0U		/* 0.000000 * 1000000000 */ 
	}
};


/****** Object ALARM ******/

static void
setevent_alarm_1(void);
static void
setevent_alarm_1(void)
{
	(void) kernel_set_event_action(MainTask, MainEvt);
}

static void
activate_alarm_2(void);
static void
activate_alarm_2(void)
{
	(void) kernel_activate_task_action(Task1);
}

static void
setevent_alarm_3(void);
static void
setevent_alarm_3(void)
{
	(void) kernel_set_event_action(Task3, T3Evt);
}



static void
incrementcounter_alarm_6(void);
static void
incrementcounter_alarm_6(void)
{
	(void) kernel_incr_counter_action(SampleCnt3);
}


const ALMINIB kernel_alminib_table[TNUM_ALARM] = {
	{ &(kernel_cntcb_table[MAIN_HW_COUNTER]), &setevent_alarm_1, 0x00000000U, 0U, 0U, SETEVENT & CALLBACK },
	{ &(kernel_cntcb_table[MAIN_HW_COUNTER]), &activate_alarm_2, 0x00000000U, 0U, 0U, ACTIVATETASK & CALLBACK },
	{ &(kernel_cntcb_table[MAIN_HW_COUNTER]), &setevent_alarm_3, 0x00000000U, 0U, 0U, SETEVENT & CALLBACK },
	{ &(kernel_cntcb_table[MAIN_HW_COUNTER]), ALARMCALLBACKNAME(SysTimerAlmCb), 0x00000000U, 0U, 0U, CALLBACK & CALLBACK },
	{ &(kernel_cntcb_table[SampleCnt]), ALARMCALLBACKNAME(SampleAlmCb), 0x00000007U, 10U, 10U, (CALLBACK & CALLBACK) | ABSOLUTE },
	{ &(kernel_cntcb_table[SampleCnt2]), &incrementcounter_alarm_6, 0x00000007U, 10U, 10U, (INCREMENTCOUNTER & CALLBACK) | ABSOLUTE },
	{ &(kernel_cntcb_table[SampleCnt3]), ALARMCALLBACKNAME(SampleAlmCb2), 0x00000007U, 10U, 10U, (CALLBACK & CALLBACK) | ABSOLUTE }
};

ALMCB	kernel_almcb_table[TNUM_ALARM];

/****** Object SCHEDULETABLE ******/

/* Object SCHEDULETABLE(scheduletable1) */

static void
expire_scheduletable_1_0(void);
static void
expire_scheduletable_1_0(void)
{
	(void) kernel_activate_task_action(Task6);
	(void) kernel_activate_task_action(Task7);
	(void) kernel_activate_task_action(Task8);
}
static void
expire_scheduletable_1_1(void);
static void
expire_scheduletable_1_1(void)
{
	(void) kernel_set_event_action(Task6, T6Evt);
	(void) kernel_set_event_action(Task7, T7Evt);
	(void) kernel_set_event_action(Task8, T8Evt);
}

static const SCHTBLEXPPTCB schtblexppt_table_1[2] = {
	{ 10U, &expire_scheduletable_1_0 },
	{ 20U, &expire_scheduletable_1_1 }
};

/* Object SCHEDULETABLE(scheduletable2) */

static void
expire_scheduletable_2_0(void);
static void
expire_scheduletable_2_0(void)
{
	(void) kernel_activate_task_action(Task8);
	(void) kernel_activate_task_action(Task7);
}
static void
expire_scheduletable_2_1(void);
static void
expire_scheduletable_2_1(void)
{
	(void) kernel_set_event_action(Task8, T8Evt);
}
static void
expire_scheduletable_2_2(void);
static void
expire_scheduletable_2_2(void)
{
	(void) kernel_set_event_action(Task7, T7Evt);
}

static const SCHTBLEXPPTCB schtblexppt_table_2[3] = {
	{ 20U, &expire_scheduletable_2_0 },
	{ 30U, &expire_scheduletable_2_1 },
	{ 40U, &expire_scheduletable_2_2 }
};


const SCHTBLINIB kernel_schtblinib_table[TNUM_SCHEDULETABLE] = {
	{ &(kernel_cntcb_table[SchtblSampleCnt]), 60U, 0x00000000U, 0U, 0U, schtblexppt_table_1, TRUE, 2U },
	{ &(kernel_cntcb_table[SchtblSampleCnt]), 50U, 0x00000000U, 0U, 0U, schtblexppt_table_2, TRUE, 3U }
};

SCHTBLCB kernel_schtblcb_table[TNUM_SCHEDULETABLE];


/****** Object RESOURCE ******/

const RESINIB kernel_resinib_table[TNUM_STD_RESOURCE] = {
	{ 6 },
	{ 3 }
};

RESCB kernel_rescb_table[TNUM_STD_RESOURCE];


/****** Object ISR ******/


ISRCB kernel_isrcb_table[TNUM_ISR2];


void
kernel_object_initialize(void)
{
	kernel_interrupt_initialize();
	kernel_resource_initialize();
	kernel_task_initialize();
	kernel_counter_initialize();
	kernel_alarm_initialize();
	kernel_schtbl_initialize();
}


void
kernel_object_terminate(void)
{
	kernel_counter_terminate();
}


/*
 *  Interrupt Management Functions
 */

void
kernel_inthdr_17(void)
{
	i_begin_int(17U);
	LOG_ISR_ENTER(RxHwSerialInt);
	ISRNAME(RxHwSerialInt)();
	LOG_ISR_LEAVE(RxHwSerialInt);
	i_end_int(17U);
}
void
kernel_inthdr_16(void)
{
	i_begin_int(16U);
	LOG_ISR_ENTER(C2ISR_for_MAIN_HW_COUNTER);
	ISRNAME(C2ISR_for_MAIN_HW_COUNTER)();
	LOG_ISR_LEAVE(C2ISR_for_MAIN_HW_COUNTER);
	i_end_int(16U);
}

/* HardWare Counter Interrupt Handler(C2ISR) */
ISR(C2ISR_for_MAIN_HW_COUNTER)
{
	kernel_notify_hardware_counter(MAIN_HW_COUNTER);
}

/*
 *  Stack Area for Non-task Context
 */

#define TNUM_INTNO	UINT_C(2)
const InterruptNumberType kernel_tnum_intno = TNUM_INTNO;

const INTINIB kernel_intinib_table[TNUM_INTNO] = {
	{ (17U), ENABLE, (-2), 0x450U},
	{ (16U), ENABLE, (-1), 0x6a0U}
};

static StackType			kernel_ostack[COUNT_STK_T(0x8a0U)];
#define TOPPERS_OSTKSZ		ROUND_STK_T(0x8a0U)
#define TOPPERS_OSTK		kernel_ostack

const MemorySizeType	kernel_ostksz = TOPPERS_OSTKSZ;
StackType * const		kernel_ostk = (StackType *) TOPPERS_OSTK;

#ifdef TOPPERS_OSTKPT
StackType * const	kernel_ostkpt = TOPPERS_OSTKPT(TOPPERS_OSTK, TOPPERS_OSTKSZ);
#endif /* TOPPERS_OSTKPT */


#ifdef TOPPERS_ENABLE_TRACE
const char8 *
kernel_appid_str(AppModeType id)
{
	const char8	*appid_str;
	switch (id) {
	case AppMode1:
		appid_str = "AppMode1";
		break;
	case AppMode2:
		appid_str = "AppMode2";
		break;
	case AppMode3:
		appid_str = "AppMode3";
		break;
	default:
		appid_str = "";
		break;
	}
	return(appid_str);
}
const char8 *
kernel_tskid_str(TaskType id)
{
	const char8	*tskid_str;
	switch (id) {
	case MainTask:
		tskid_str = "MainTask";
		break;
	case Task2:
		tskid_str = "Task2";
		break;
	case Task3:
		tskid_str = "Task3";
		break;
	case Task6:
		tskid_str = "Task6";
		break;
	case Task7:
		tskid_str = "Task7";
		break;
	case Task8:
		tskid_str = "Task8";
		break;
	case HighPriorityTask:
		tskid_str = "HighPriorityTask";
		break;
	case NonPriTask:
		tskid_str = "NonPriTask";
		break;
	case Task1:
		tskid_str = "Task1";
		break;
	case Task4:
		tskid_str = "Task4";
		break;
	case Task5:
		tskid_str = "Task5";
		break;
	case INVALID_TASK:
		tskid_str = "INVALID_TASK";
		break;
	default:
		tskid_str = "";
		break;
	}
	return(tskid_str);
}

const char8 *
kernel_isrid_str(ISRType id)
{
	const char8	*isrid_str;
	switch (id) {
	case RxHwSerialInt:
		isrid_str = "RxHwSerialInt";
		break;
	case C2ISR_for_MAIN_HW_COUNTER:
		isrid_str = "C2ISR_for_MAIN_HW_COUNTER";
		break;
	case INVALID_ISR:
		isrid_str = "INVALID_ISR";
		break;
	default:
		isrid_str = "";
		break;
	}
	return(isrid_str);
}

const char8 *
kernel_cntid_str(CounterType id)
{
	const char8	*cntid_str;
	switch (id) {
	case MAIN_HW_COUNTER:
		cntid_str = "MAIN_HW_COUNTER";
		break;
	case SampleCnt:
		cntid_str = "SampleCnt";
		break;
	case SampleCnt2:
		cntid_str = "SampleCnt2";
		break;
	case SampleCnt3:
		cntid_str = "SampleCnt3";
		break;
	case SchtblSampleCnt:
		cntid_str = "SchtblSampleCnt";
		break;
	default:
		cntid_str = "";
		break;
	}
	return(cntid_str);
}

const char8 *
kernel_almid_str(AlarmType id)
{
	const char8	*almid_str;
	switch (id) {
	case MainCycArm:
		almid_str = "MainCycArm";
		break;
	case ActTskArm:
		almid_str = "ActTskArm";
		break;
	case SetEvtArm:
		almid_str = "SetEvtArm";
		break;
	case CallBackArm:
		almid_str = "CallBackArm";
		break;
	case SampleAlm:
		almid_str = "SampleAlm";
		break;
	case SampleAlm1:
		almid_str = "SampleAlm1";
		break;
	case SampleAlm2:
		almid_str = "SampleAlm2";
		break;
	default:
		almid_str = "";
		break;
	}
	return(almid_str);
}

const char8 *
kernel_resid_str(ResourceType id)
{
	const char8	*resid_str;
	switch (id) {
	case TskLevelRes:
		resid_str = "TskLevelRes";
		break;
	case CntRes:
		resid_str = "CntRes";
		break;
	case GroupRes:
		resid_str = "GroupRes";
		break;
	default:
		resid_str = "";
		break;
	}
	return(resid_str);
}

const char8 *
kernel_schtblid_str(ScheduleTableType id)
{
	const char8	*schtblid_str;
	switch (id) {
	case scheduletable1:
		schtblid_str = "scheduletable1";
		break;
	case scheduletable2:
		schtblid_str = "scheduletable2";
		break;
	default:
		schtblid_str = "";
		break;
	}
	return(schtblid_str);
}

const char8 *
kernel_evtid_str(TaskType task, EventMaskType event)
{
	const char8	*evtid_str;
	switch (task) {
	case MainTask:
		switch (event) {
		case MainEvt:
			evtid_str = "MainEvt";
			break;
		default:
			evtid_str = NULL;
			break;
		}
		break;
	case Task2:
		switch (event) {
		case T2Evt:
			evtid_str = "T2Evt";
			break;
		default:
			evtid_str = NULL;
			break;
		}
		break;
	case Task3:
		switch (event) {
		case T3Evt:
			evtid_str = "T3Evt";
			break;
		default:
			evtid_str = NULL;
			break;
		}
		break;
	case Task6:
		switch (event) {
		case T6Evt:
			evtid_str = "T6Evt";
			break;
		default:
			evtid_str = NULL;
			break;
		}
		break;
	case Task7:
		switch (event) {
		case T7Evt:
			evtid_str = "T7Evt";
			break;
		default:
			evtid_str = NULL;
			break;
		}
		break;
	case Task8:
		switch (event) {
		case T8Evt:
			evtid_str = "T8Evt";
			break;
		default:
			evtid_str = NULL;
			break;
		}
		break;
	case HighPriorityTask:
		evtid_str = NULL;
		break;
	case NonPriTask:
		evtid_str = NULL;
		break;
	case Task1:
		evtid_str = NULL;
		break;
	case Task4:
		evtid_str = NULL;
		break;
	case Task5:
		evtid_str = NULL;
		break;
	default:
		evtid_str = NULL;
		break;
	}
	if (evtid_str == NULL) {
		if (event == MainEvt) {
			evtid_str = "MainEvt";
		}
		if (event == T2Evt) {
			evtid_str = "T2Evt";
		}
		if (event == T3Evt) {
			evtid_str = "T3Evt";
		}
		if (event == T6Evt) {
			evtid_str = "T6Evt";
		}
		if (event == T7Evt) {
			evtid_str = "T7Evt";
		}
		if (event == T8Evt) {
			evtid_str = "T8Evt";
		}
	}
	return(evtid_str);
}
#endif /* TOPPERS_ENABLE_TRACE */

const uint32 kernel_tmin_basepri = (((uint32)(16U - (uint32)(-(PriorityType)(-2))) << 4U));

const FunctionRefType kernel_isr_tbl[TNUM_INT] = {
	&kernel_inthdr_16,	/* 16 */
	&kernel_inthdr_17,	/* 17 */
	(FunctionRefType)&kernel_default_int_handler,	/* 18 */
	(FunctionRefType)&kernel_default_int_handler,	/* 19 */
	(FunctionRefType)&kernel_default_int_handler,	/* 20 */
	(FunctionRefType)&kernel_default_int_handler,	/* 21 */
	(FunctionRefType)&kernel_default_int_handler,	/* 22 */
	(FunctionRefType)&kernel_default_int_handler,	/* 23 */
	(FunctionRefType)&kernel_default_int_handler,	/* 24 */
	(FunctionRefType)&kernel_default_int_handler,	/* 25 */
	(FunctionRefType)&kernel_default_int_handler,	/* 26 */
	(FunctionRefType)&kernel_default_int_handler,	/* 27 */
	(FunctionRefType)&kernel_default_int_handler,	/* 28 */
	(FunctionRefType)&kernel_default_int_handler,	/* 29 */
	(FunctionRefType)&kernel_default_int_handler,	/* 30 */
	(FunctionRefType)&kernel_default_int_handler,	/* 31 */
	(FunctionRefType)&kernel_default_int_handler,	/* 32 */
	(FunctionRefType)&kernel_default_int_handler,	/* 33 */
	(FunctionRefType)&kernel_default_int_handler,	/* 34 */
	(FunctionRefType)&kernel_default_int_handler,	/* 35 */
	(FunctionRefType)&kernel_default_int_handler,	/* 36 */
	(FunctionRefType)&kernel_default_int_handler,	/* 37 */
	(FunctionRefType)&kernel_default_int_handler,	/* 38 */
	(FunctionRefType)&kernel_default_int_handler,	/* 39 */
	(FunctionRefType)&kernel_default_int_handler,	/* 40 */
	(FunctionRefType)&kernel_default_int_handler,	/* 41 */
	(FunctionRefType)&kernel_default_int_handler,	/* 42 */
	(FunctionRefType)&kernel_default_int_handler,	/* 43 */
	(FunctionRefType)&kernel_default_int_handler,	/* 44 */
	(FunctionRefType)&kernel_default_int_handler,	/* 45 */
	(FunctionRefType)&kernel_default_int_handler,	/* 46 */
	(FunctionRefType)&kernel_default_int_handler,	/* 47 */
	(FunctionRefType)&kernel_default_int_handler,	/* 48 */
	(FunctionRefType)&kernel_default_int_handler,	/* 49 */
	(FunctionRefType)&kernel_default_int_handler,	/* 50 */
	(FunctionRefType)&kernel_default_int_handler,	/* 51 */
	(FunctionRefType)&kernel_default_int_handler,	/* 52 */
	(FunctionRefType)&kernel_default_int_handler,	/* 53 */
	(FunctionRefType)&kernel_default_int_handler,	/* 54 */
	(FunctionRefType)&kernel_default_int_handler,	/* 55 */
	(FunctionRefType)&kernel_default_int_handler,	/* 56 */
	(FunctionRefType)&kernel_default_int_handler,	/* 57 */
	(FunctionRefType)&kernel_default_int_handler,	/* 58 */
	(FunctionRefType)&kernel_default_int_handler,	/* 59 */
	(FunctionRefType)&kernel_default_int_handler,	/* 60 */
	(FunctionRefType)&kernel_default_int_handler,	/* 61 */
	(FunctionRefType)&kernel_default_int_handler,	/* 62 */
	(FunctionRefType)&kernel_default_int_handler,	/* 63 */
	(FunctionRefType)&kernel_default_int_handler,	/* 64 */
	(FunctionRefType)&kernel_default_int_handler,	/* 65 */
	(FunctionRefType)&kernel_default_int_handler,	/* 66 */
	(FunctionRefType)&kernel_default_int_handler,	/* 67 */
	(FunctionRefType)&kernel_default_int_handler,	/* 68 */
	(FunctionRefType)&kernel_default_int_handler,	/* 69 */
	(FunctionRefType)&kernel_default_int_handler,	/* 70 */
	(FunctionRefType)&kernel_default_int_handler,	/* 71 */
	(FunctionRefType)&kernel_default_int_handler,	/* 72 */
	(FunctionRefType)&kernel_default_int_handler,	/* 73 */
	(FunctionRefType)&kernel_default_int_handler,	/* 74 */
	(FunctionRefType)&kernel_default_int_handler,	/* 75 */
	(FunctionRefType)&kernel_default_int_handler,	/* 76 */
	(FunctionRefType)&kernel_default_int_handler,	/* 77 */
	(FunctionRefType)&kernel_default_int_handler,	/* 78 */
	(FunctionRefType)&kernel_default_int_handler,	/* 79 */
	(FunctionRefType)&kernel_default_int_handler,	/* 80 */
	(FunctionRefType)&kernel_default_int_handler,	/* 81 */
	(FunctionRefType)&kernel_default_int_handler,	/* 82 */
	(FunctionRefType)&kernel_default_int_handler,	/* 83 */
	(FunctionRefType)&kernel_default_int_handler,	/* 84 */
	(FunctionRefType)&kernel_default_int_handler,	/* 85 */
	(FunctionRefType)&kernel_default_int_handler,	/* 86 */
	(FunctionRefType)&kernel_default_int_handler,	/* 87 */
	(FunctionRefType)&kernel_default_int_handler,	/* 88 */
	(FunctionRefType)&kernel_default_int_handler,	/* 89 */
	(FunctionRefType)&kernel_default_int_handler,	/* 90 */
	(FunctionRefType)&kernel_default_int_handler,	/* 91 */
	(FunctionRefType)&kernel_default_int_handler,	/* 92 */
	(FunctionRefType)&kernel_default_int_handler,	/* 93 */
	(FunctionRefType)&kernel_default_int_handler,	/* 94 */
	(FunctionRefType)&kernel_default_int_handler,	/* 95 */
	(FunctionRefType)&kernel_default_int_handler,	/* 96 */
	(FunctionRefType)&kernel_default_int_handler,	/* 97 */
	(FunctionRefType)&kernel_default_int_handler,	/* 98 */
	(FunctionRefType)&kernel_default_int_handler,	/* 99 */
	(FunctionRefType)&kernel_default_int_handler,	/* 100 */
	(FunctionRefType)&kernel_default_int_handler,	/* 101 */
	(FunctionRefType)&kernel_default_int_handler,	/* 102 */
	(FunctionRefType)&kernel_default_int_handler,	/* 103 */
	(FunctionRefType)&kernel_default_int_handler,	/* 104 */
	(FunctionRefType)&kernel_default_int_handler,	/* 105 */
	(FunctionRefType)&kernel_default_int_handler,	/* 106 */
	(FunctionRefType)&kernel_default_int_handler,	/* 107 */
	(FunctionRefType)&kernel_default_int_handler,	/* 108 */
	(FunctionRefType)&kernel_default_int_handler,	/* 109 */
	(FunctionRefType)&kernel_default_int_handler,	/* 110 */
	(FunctionRefType)&kernel_default_int_handler	/* 111 */
};

ISRCB * const kernel_isr_p_isrcb_tbl[TNUM_INT] = {
	&(kernel_isrcb_table[1]),	/* 16 */
	&(kernel_isrcb_table[0]),	/* 17 */
	NULL,	/* 18 */
	NULL,	/* 19 */
	NULL,	/* 20 */
	NULL,	/* 21 */
	NULL,	/* 22 */
	NULL,	/* 23 */
	NULL,	/* 24 */
	NULL,	/* 25 */
	NULL,	/* 26 */
	NULL,	/* 27 */
	NULL,	/* 28 */
	NULL,	/* 29 */
	NULL,	/* 30 */
	NULL,	/* 31 */
	NULL,	/* 32 */
	NULL,	/* 33 */
	NULL,	/* 34 */
	NULL,	/* 35 */
	NULL,	/* 36 */
	NULL,	/* 37 */
	NULL,	/* 38 */
	NULL,	/* 39 */
	NULL,	/* 40 */
	NULL,	/* 41 */
	NULL,	/* 42 */
	NULL,	/* 43 */
	NULL,	/* 44 */
	NULL,	/* 45 */
	NULL,	/* 46 */
	NULL,	/* 47 */
	NULL,	/* 48 */
	NULL,	/* 49 */
	NULL,	/* 50 */
	NULL,	/* 51 */
	NULL,	/* 52 */
	NULL,	/* 53 */
	NULL,	/* 54 */
	NULL,	/* 55 */
	NULL,	/* 56 */
	NULL,	/* 57 */
	NULL,	/* 58 */
	NULL,	/* 59 */
	NULL,	/* 60 */
	NULL,	/* 61 */
	NULL,	/* 62 */
	NULL,	/* 63 */
	NULL,	/* 64 */
	NULL,	/* 65 */
	NULL,	/* 66 */
	NULL,	/* 67 */
	NULL,	/* 68 */
	NULL,	/* 69 */
	NULL,	/* 70 */
	NULL,	/* 71 */
	NULL,	/* 72 */
	NULL,	/* 73 */
	NULL,	/* 74 */
	NULL,	/* 75 */
	NULL,	/* 76 */
	NULL,	/* 77 */
	NULL,	/* 78 */
	NULL,	/* 79 */
	NULL,	/* 80 */
	NULL,	/* 81 */
	NULL,	/* 82 */
	NULL,	/* 83 */
	NULL,	/* 84 */
	NULL,	/* 85 */
	NULL,	/* 86 */
	NULL,	/* 87 */
	NULL,	/* 88 */
	NULL,	/* 89 */
	NULL,	/* 90 */
	NULL,	/* 91 */
	NULL,	/* 92 */
	NULL,	/* 93 */
	NULL,	/* 94 */
	NULL,	/* 95 */
	NULL,	/* 96 */
	NULL,	/* 97 */
	NULL,	/* 98 */
	NULL,	/* 99 */
	NULL,	/* 100 */
	NULL,	/* 101 */
	NULL,	/* 102 */
	NULL,	/* 103 */
	NULL,	/* 104 */
	NULL,	/* 105 */
	NULL,	/* 106 */
	NULL,	/* 107 */
	NULL,	/* 108 */
	NULL,	/* 109 */
	NULL,	/* 110 */
	NULL	/* 111 */
};

extern const uint32 kernel_vector_table[];

/* リンカスクリプトで定義されるSRAM末尾シンボル（初期MSP） */
extern const uint32 _estack;

/* スタートアップ・例外ハンドラの宣言 (start.S / prc_support.S)             */
/* prc_rename.h によるリネーム済みのため kernel_ プレフィクスを直接使用する */
extern void _kernel_start(void);
extern void default_exc_handler(void);
extern void kernel_svc_handler(void);
extern void kernel_pendsv_handler(void);
extern void kernel_interrupt_entry(void);

const uint32 kernel_vector_table[] __attribute__((section(".vectors"), aligned(1024))) = {
	(uint32)&_estack,                                /* 0: Initial MSP */
	(uint32)_kernel_start + 1,                       /* 1: Reset (Thumb bit) */
	(uint32)default_exc_handler + 1,          /* 2: NMI */
	(uint32)default_exc_handler + 1,          /* 3: HardFault */
	(uint32)default_exc_handler + 1,          /* 4: MemManage */
	(uint32)default_exc_handler + 1,          /* 5: BusFault */
	(uint32)default_exc_handler + 1,          /* 6: UsageFault */
	(uint32)default_exc_handler + 1,          /* 7: SecureFault */
	0U,                                              /* 8: Reserved */
	0U,                                              /* 9: Reserved */
	0U,                                              /* 10: Reserved */
	(uint32)kernel_svc_handler + 1,                  /* 11: SVCall */
	0U,                                              /* 12: DebugMon */
	0U,                                              /* 13: Reserved */
	(uint32)kernel_pendsv_handler + 1,               /* 14: PendSV */
	(uint32)default_exc_handler + 1,          /* 15: SysTick */
	(uint32)kernel_interrupt_entry + 1,	/* 16: IRQ0 */
	(uint32)kernel_interrupt_entry + 1,	/* 17: IRQ1 */
	(uint32)kernel_default_int_handler + 1,	/* 18: IRQ2 */
	(uint32)kernel_default_int_handler + 1,	/* 19: IRQ3 */
	(uint32)kernel_default_int_handler + 1,	/* 20: IRQ4 */
	(uint32)kernel_default_int_handler + 1,	/* 21: IRQ5 */
	(uint32)kernel_default_int_handler + 1,	/* 22: IRQ6 */
	(uint32)kernel_default_int_handler + 1,	/* 23: IRQ7 */
	(uint32)kernel_default_int_handler + 1,	/* 24: IRQ8 */
	(uint32)kernel_default_int_handler + 1,	/* 25: IRQ9 */
	(uint32)kernel_default_int_handler + 1,	/* 26: IRQ10 */
	(uint32)kernel_default_int_handler + 1,	/* 27: IRQ11 */
	(uint32)kernel_default_int_handler + 1,	/* 28: IRQ12 */
	(uint32)kernel_default_int_handler + 1,	/* 29: IRQ13 */
	(uint32)kernel_default_int_handler + 1,	/* 30: IRQ14 */
	(uint32)kernel_default_int_handler + 1,	/* 31: IRQ15 */
	(uint32)kernel_default_int_handler + 1,	/* 32: IRQ16 */
	(uint32)kernel_default_int_handler + 1,	/* 33: IRQ17 */
	(uint32)kernel_default_int_handler + 1,	/* 34: IRQ18 */
	(uint32)kernel_default_int_handler + 1,	/* 35: IRQ19 */
	(uint32)kernel_default_int_handler + 1,	/* 36: IRQ20 */
	(uint32)kernel_default_int_handler + 1,	/* 37: IRQ21 */
	(uint32)kernel_default_int_handler + 1,	/* 38: IRQ22 */
	(uint32)kernel_default_int_handler + 1,	/* 39: IRQ23 */
	(uint32)kernel_default_int_handler + 1,	/* 40: IRQ24 */
	(uint32)kernel_default_int_handler + 1,	/* 41: IRQ25 */
	(uint32)kernel_default_int_handler + 1,	/* 42: IRQ26 */
	(uint32)kernel_default_int_handler + 1,	/* 43: IRQ27 */
	(uint32)kernel_default_int_handler + 1,	/* 44: IRQ28 */
	(uint32)kernel_default_int_handler + 1,	/* 45: IRQ29 */
	(uint32)kernel_default_int_handler + 1,	/* 46: IRQ30 */
	(uint32)kernel_default_int_handler + 1,	/* 47: IRQ31 */
	(uint32)kernel_default_int_handler + 1,	/* 48: IRQ32 */
	(uint32)kernel_default_int_handler + 1,	/* 49: IRQ33 */
	(uint32)kernel_default_int_handler + 1,	/* 50: IRQ34 */
	(uint32)kernel_default_int_handler + 1,	/* 51: IRQ35 */
	(uint32)kernel_default_int_handler + 1,	/* 52: IRQ36 */
	(uint32)kernel_default_int_handler + 1,	/* 53: IRQ37 */
	(uint32)kernel_default_int_handler + 1,	/* 54: IRQ38 */
	(uint32)kernel_default_int_handler + 1,	/* 55: IRQ39 */
	(uint32)kernel_default_int_handler + 1,	/* 56: IRQ40 */
	(uint32)kernel_default_int_handler + 1,	/* 57: IRQ41 */
	(uint32)kernel_default_int_handler + 1,	/* 58: IRQ42 */
	(uint32)kernel_default_int_handler + 1,	/* 59: IRQ43 */
	(uint32)kernel_default_int_handler + 1,	/* 60: IRQ44 */
	(uint32)kernel_default_int_handler + 1,	/* 61: IRQ45 */
	(uint32)kernel_default_int_handler + 1,	/* 62: IRQ46 */
	(uint32)kernel_default_int_handler + 1,	/* 63: IRQ47 */
	(uint32)kernel_default_int_handler + 1,	/* 64: IRQ48 */
	(uint32)kernel_default_int_handler + 1,	/* 65: IRQ49 */
	(uint32)kernel_default_int_handler + 1,	/* 66: IRQ50 */
	(uint32)kernel_default_int_handler + 1,	/* 67: IRQ51 */
	(uint32)kernel_default_int_handler + 1,	/* 68: IRQ52 */
	(uint32)kernel_default_int_handler + 1,	/* 69: IRQ53 */
	(uint32)kernel_default_int_handler + 1,	/* 70: IRQ54 */
	(uint32)kernel_default_int_handler + 1,	/* 71: IRQ55 */
	(uint32)kernel_default_int_handler + 1,	/* 72: IRQ56 */
	(uint32)kernel_default_int_handler + 1,	/* 73: IRQ57 */
	(uint32)kernel_default_int_handler + 1,	/* 74: IRQ58 */
	(uint32)kernel_default_int_handler + 1,	/* 75: IRQ59 */
	(uint32)kernel_default_int_handler + 1,	/* 76: IRQ60 */
	(uint32)kernel_default_int_handler + 1,	/* 77: IRQ61 */
	(uint32)kernel_default_int_handler + 1,	/* 78: IRQ62 */
	(uint32)kernel_default_int_handler + 1,	/* 79: IRQ63 */
	(uint32)kernel_default_int_handler + 1,	/* 80: IRQ64 */
	(uint32)kernel_default_int_handler + 1,	/* 81: IRQ65 */
	(uint32)kernel_default_int_handler + 1,	/* 82: IRQ66 */
	(uint32)kernel_default_int_handler + 1,	/* 83: IRQ67 */
	(uint32)kernel_default_int_handler + 1,	/* 84: IRQ68 */
	(uint32)kernel_default_int_handler + 1,	/* 85: IRQ69 */
	(uint32)kernel_default_int_handler + 1,	/* 86: IRQ70 */
	(uint32)kernel_default_int_handler + 1,	/* 87: IRQ71 */
	(uint32)kernel_default_int_handler + 1,	/* 88: IRQ72 */
	(uint32)kernel_default_int_handler + 1,	/* 89: IRQ73 */
	(uint32)kernel_default_int_handler + 1,	/* 90: IRQ74 */
	(uint32)kernel_default_int_handler + 1,	/* 91: IRQ75 */
	(uint32)kernel_default_int_handler + 1,	/* 92: IRQ76 */
	(uint32)kernel_default_int_handler + 1,	/* 93: IRQ77 */
	(uint32)kernel_default_int_handler + 1,	/* 94: IRQ78 */
	(uint32)kernel_default_int_handler + 1,	/* 95: IRQ79 */
	(uint32)kernel_default_int_handler + 1,	/* 96: IRQ80 */
	(uint32)kernel_default_int_handler + 1,	/* 97: IRQ81 */
	(uint32)kernel_default_int_handler + 1,	/* 98: IRQ82 */
	(uint32)kernel_default_int_handler + 1,	/* 99: IRQ83 */
	(uint32)kernel_default_int_handler + 1,	/* 100: IRQ84 */
	(uint32)kernel_default_int_handler + 1,	/* 101: IRQ85 */
	(uint32)kernel_default_int_handler + 1,	/* 102: IRQ86 */
	(uint32)kernel_default_int_handler + 1,	/* 103: IRQ87 */
	(uint32)kernel_default_int_handler + 1,	/* 104: IRQ88 */
	(uint32)kernel_default_int_handler + 1,	/* 105: IRQ89 */
	(uint32)kernel_default_int_handler + 1,	/* 106: IRQ90 */
	(uint32)kernel_default_int_handler + 1,	/* 107: IRQ91 */
	(uint32)kernel_default_int_handler + 1,	/* 108: IRQ92 */
	(uint32)kernel_default_int_handler + 1,	/* 109: IRQ93 */
	(uint32)kernel_default_int_handler + 1,	/* 110: IRQ94 */
	(uint32)kernel_default_int_handler + 1	/* 111: IRQ95 */
};
