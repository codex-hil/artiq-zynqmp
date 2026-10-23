/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef ARTIQ_PMU_LAB_GUARD_H
#define ARTIQ_PMU_LAB_GUARD_H
/* Included ONLY with explicit ARTIQ_PMU_LAB_GUARD in request.h. */
#ifdef __MICROBLAZE__
#include "mb_interface.h"
#define ARTIQ_GUARD_MSR() ((uint32_t)mfmsr())
#define ARTIQ_GUARD_DISABLE_IRQ() microblaze_disable_interrupts()
#elif defined(ARTIQ_PMU_GUARD_HOST_TEST)
extern uint32_t artiq_guard_test_msr(void);
extern void artiq_guard_test_disable_irq(void);
#define ARTIQ_GUARD_MSR() artiq_guard_test_msr()
#define ARTIQ_GUARD_DISABLE_IRQ() artiq_guard_test_disable_irq()
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
 artiq_pmu_order();artiq_pmu_guard.generation=gen;
 /* No scheduler, request dispatch, memory load/store, sleep, return or resume. */
 for (;;) __asm__ volatile("nop");
}
#endif
