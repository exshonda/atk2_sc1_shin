/* Os_Lcfg.h */
#ifndef TOPPERS_OS_LCFG_H
#define TOPPERS_OS_LCFG_H

#define TNUM_ALARM				UINT_C(7)
#define TNUM_COUNTER			UINT_C(5)
#define TNUM_HARDCOUNTER		UINT_C(1)
#define TNUM_ISR2				UINT_C(2)
#define TNUM_STD_RESOURCE		UINT_C(2)
#define TNUM_TASK				UINT_C(11)
#define TNUM_EXTTASK			UINT_C(6)
#define TNUM_APP_MODE			UINT_C(3)
#define TNUM_SCHEDULETABLE		UINT_C(2)
#define TNUM_IMPLSCHEDULETABLE	UINT_C(0)

/*
 *  Default Definitions of Trace Log Macros
 */

#ifndef TOPPERS_ENABLE_TRACE
#ifndef LOG_USER_MARK
#define LOG_USER_MARK(str)
#endif /* LOG_USER_MARK */
#endif /* TOPPERS_ENABLE_TRACE */

/****** Object TASK ******/

#define MainTask	UINT_C(0)
#define Task2	UINT_C(1)
#define Task3	UINT_C(2)
#define Task6	UINT_C(3)
#define Task7	UINT_C(4)
#define Task8	UINT_C(5)
#define HighPriorityTask	UINT_C(6)
#define NonPriTask	UINT_C(7)
#define Task1	UINT_C(8)
#define Task4	UINT_C(9)
#define Task5	UINT_C(10)

/****** Object COUNTER ******/

#define MAIN_HW_COUNTER	UINT_C(0)
#define SampleCnt	UINT_C(1)
#define SampleCnt2	UINT_C(2)
#define SampleCnt3	UINT_C(3)
#define SchtblSampleCnt	UINT_C(4)

#define OSMAXALLOWEDVALUE_MAIN_HW_COUNTER	((TickType) 2147483647)
#define OSTICKSPERBASE_MAIN_HW_COUNTER	((TickType) 25000)
#define OSMINCYCLE_MAIN_HW_COUNTER	((TickType) 25)
#define OSMAXALLOWEDVALUE_SampleCnt	((TickType) 99)
#define OSTICKSPERBASE_SampleCnt	((TickType) 10)
#define OSMINCYCLE_SampleCnt	((TickType) 10)
#define OSMAXALLOWEDVALUE_SampleCnt2	((TickType) 99)
#define OSTICKSPERBASE_SampleCnt2	((TickType) 10)
#define OSMINCYCLE_SampleCnt2	((TickType) 10)
#define OSMAXALLOWEDVALUE_SampleCnt3	((TickType) 99)
#define OSTICKSPERBASE_SampleCnt3	((TickType) 10)
#define OSMINCYCLE_SampleCnt3	((TickType) 10)
#define OSMAXALLOWEDVALUE_SchtblSampleCnt	((TickType) 99)
#define OSTICKSPERBASE_SchtblSampleCnt	((TickType) 10)
#define OSMINCYCLE_SchtblSampleCnt	((TickType) 10)

#define OS_TICKS2SEC_MAIN_HW_COUNTER(tick)	(((PhysicalTimeType)0U) * (tick) / 1000000000U)	/* (0.000000 * 1000000000) * (tick) / 1000000000 */
#define OS_TICKS2MS_MAIN_HW_COUNTER(tick)	(((PhysicalTimeType)0U) * (tick) / 1000000U)		/* (0.000000 * 1000000000) * (tick) / 1000000 */
#define OS_TICKS2US_MAIN_HW_COUNTER(tick)	(((PhysicalTimeType)0U) * (tick) / 1000U)			/* (0.000000 * 1000000000) * (tick) / 1000 */
#define OS_TICKS2NS_MAIN_HW_COUNTER(tick)	(((PhysicalTimeType)0U) * (tick))					/* (0.000000 * 1000000000) * (tick) */

/****** Object ALARM ******/

#define MainCycArm	UINT_C(0)
#define ActTskArm	UINT_C(1)
#define SetEvtArm	UINT_C(2)
#define CallBackArm	UINT_C(3)
#define SampleAlm	UINT_C(4)
#define SampleAlm1	UINT_C(5)
#define SampleAlm2	UINT_C(6)

/****** Object SCHEDULETABLE ******/

#define scheduletable1	UINT_C(0)
#define scheduletable2	UINT_C(1)

/****** Object RESOURCE ******/

#define TskLevelRes	UINT_C(0)
#define CntRes	UINT_C(1)
#define GroupRes	UINT_C(2)

/****** Object ISR ******/

#define RxHwSerialInt	UINT_C(0)
#define C2ISR_for_MAIN_HW_COUNTER	UINT_C(1)

/****** Object APPMODE ******/

#define AppMode1	UINT_C(0)
#define AppMode2	UINT_C(1)
#define AppMode3	UINT_C(2)

/****** Object EVENT ******/
#define MainEvt	UINT_C(0x00000001)
#define T2Evt	UINT_C(0x00000001)
#define T3Evt	UINT_C(0x00010000)
#define T6Evt	UINT_C(0x00000001)
#define T7Evt	UINT_C(0x00000001)
#define T8Evt	UINT_C(0x00000001)



#ifndef TOPPERS_MACRO_ONLY
#ifdef TOPPERS_ENABLE_TRACE
extern const char8 *kernel_appid_str(AppModeType id);
extern const char8 *kernel_tskid_str(TaskType id);
extern const char8 *kernel_isrid_str(ISRType id);
extern const char8 *kernel_cntid_str(CounterType id);
extern const char8 *kernel_almid_str(AlarmType id);
extern const char8 *kernel_resid_str(ResourceType id);
extern const char8 *kernel_schtblid_str(ScheduleTableType id);
extern const char8 *kernel_evtid_str(TaskType task, EventMaskType event);
#endif /* TOPPERS_ENABLE_TRACE */

/****** Object TASK ******/

extern TASK(MainTask);
extern TASK(Task2);
extern TASK(Task3);
extern TASK(Task6);
extern TASK(Task7);
extern TASK(Task8);
extern TASK(HighPriorityTask);
extern TASK(NonPriTask);
extern TASK(Task1);
extern TASK(Task4);
extern TASK(Task5);

/****** Object ALARM ******/

extern ALARMCALLBACK(SysTimerAlmCb);
extern ALARMCALLBACK(SampleAlmCb);
extern ALARMCALLBACK(SampleAlmCb2);

/*
 *  Interrupt Management Functions
 */

extern void kernel_inthdr_17(void);
extern void kernel_inthdr_16(void);
extern ISR(RxHwSerialInt);
extern ISR(C2ISR_for_MAIN_HW_COUNTER);

extern void init_hwcounter_MAIN_HW_COUNTER(TickType maxval, TimeType nspertick);
extern void start_hwcounter_MAIN_HW_COUNTER(void);
extern void stop_hwcounter_MAIN_HW_COUNTER(void);
extern void set_hwcounter_MAIN_HW_COUNTER(TickType exprtick);
extern TickType get_hwcounter_MAIN_HW_COUNTER(void);
extern void cancel_hwcounter_MAIN_HW_COUNTER(void);
extern void trigger_hwcounter_MAIN_HW_COUNTER(void);
extern void int_clear_hwcounter_MAIN_HW_COUNTER(void);
extern void int_cancel_hwcounter_MAIN_HW_COUNTER(void);
extern void increment_hwcounter_MAIN_HW_COUNTER(void);

#endif /* TOPPERS_MACRO_ONLY */
#endif /* TOPPERS_OS_LCFG_H */

