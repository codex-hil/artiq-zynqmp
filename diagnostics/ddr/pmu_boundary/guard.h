/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef ARTIQ_PMU_LAB_GUARD_H
#define ARTIQ_PMU_LAB_GUARD_H
/* Included ONLY with explicit ARTIQ_PMU_LAB_GUARD in request.h. */
#ifdef __MICROBLAZE__
#include "mb_interface.h"
#ifdef ARTIQ_PMU_VECTOR_SNAPSHOT
#error "GPO0 is write-only in UG1087: vector snapshot is not a valid hardware diagnostic"
#endif
#define ARTIQ_GUARD_MSR() ((uint32_t)mfmsr())
#define ARTIQ_GUARD_DISABLE_IRQ() microblaze_disable_interrupts()
#define ARTIQ_GUARD_SLEEP() mb_sleep()
#ifdef ARTIQ_PMU_VECTOR_SNAPSHOT
#include "pmu_iomodule.h"
#include "xil_io.h"
#define ARTIQ_GUARD_GPO0() Xil_In32(PMU_IOMODULE_GPO0)
#endif
#elif defined(ARTIQ_PMU_GUARD_HOST_TEST)
extern uint32_t artiq_guard_test_msr(void);
extern void artiq_guard_test_disable_irq(void);
#ifdef ARTIQ_PMU_VECTOR_SNAPSHOT
extern uint32_t artiq_guard_test_gpo0(void);
#define ARTIQ_GUARD_GPO0() artiq_guard_test_gpo0()
#endif
#define ARTIQ_GUARD_MSR() artiq_guard_test_msr()
#define ARTIQ_GUARD_DISABLE_IRQ() artiq_guard_test_disable_irq()
/* Host backend only models non-return; it cannot model PMU sleep/wakeup. */
#define ARTIQ_GUARD_SLEEP() __asm__ volatile("nop")
#else
#error "Laboratory guard requires MicroBlaze or explicit offline host-test backend"
#endif
struct artiq_pmu_guard_record {
 uint32_t generation, state, nonce_lo, nonce_hi, sequence_lo, sequence_hi;
 uint32_t msr_before, msr_after, ack, unresolved, kind;
 uint32_t reserved[5];
};
static volatile struct artiq_pmu_guard_record artiq_pmu_guard;
static __attribute__((noinline,noreturn)) void artiq_pmu_enter_lab_guard(
 uint32_t gen,uint32_t nlo,uint32_t nhi,uint32_t slo,uint32_t shi) {
 uint32_t before=ARTIQ_GUARD_MSR();
 ARTIQ_GUARD_DISABLE_IRQ();
 uint32_t after=ARTIQ_GUARD_MSR();
 artiq_pmu_guard.generation=0;
 artiq_pmu_order();
 artiq_pmu_guard.state=(after==(before & ~UINT32_C(2))) ? 2 : 3;
 artiq_pmu_guard.nonce_lo=nlo;artiq_pmu_guard.nonce_hi=nhi;
 artiq_pmu_guard.sequence_lo=slo;artiq_pmu_guard.sequence_hi=shi;
 artiq_pmu_guard.msr_before=before;artiq_pmu_guard.msr_after=after;
 artiq_pmu_guard.ack=0;artiq_pmu_guard.unresolved=0x7f;
 artiq_pmu_guard.kind=2;
 for (unsigned i=0;i<5;i++) artiq_pmu_guard.reserved[i]=0;
#ifdef ARTIQ_PMU_VECTOR_SNAPSHOT
 /* Read only from PMU itself, never an external private-register alias.
  * Versioned reserved fields deliberately fail the old host parser. */
 artiq_pmu_guard.reserved[0]=1;
 artiq_pmu_guard.reserved[1]=ARTIQ_GUARD_GPO0();
#endif
 artiq_pmu_order();artiq_pmu_guard.generation=gen;
 /* UG1085 PMU RAM arbitration requires sleep for external APB access.
  * Wakeup resumes here and must re-enter sleep without dispatch or return.
  * Sleep residency/wake wiring remain a physical qualification obligation. */
 artiq_pmu_order();
 for (;;) ARTIQ_GUARD_SLEEP();
}
#endif
