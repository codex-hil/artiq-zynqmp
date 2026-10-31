/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_IRQ_AUDIT_ONLY)
#error "Explicit MicroBlaze IRQ audit opt-in required; no deployment"
#endif
#include "pit_irq_audit.h"
#include "mb_interface.h"
__attribute__((noinline,used)) int pit_irq_msr_audit(void *ctx, uint32_t *out)
{
    uint32_t value;
    if(ctx || !out || ((uintptr_t)out & 3u)) return -1;
    __asm__ volatile("" ::: "memory");
    value=(uint32_t)mfmsr();
    __asm__ volatile("" ::: "memory");
    *(volatile uint32_t *)out=value;
    return 0;
}
__attribute__((noinline,used)) int pit_irq_disable_audit(void *ctx)
{
    if(ctx) return -1;
    __asm__ volatile("" ::: "memory");
    microblaze_disable_interrupts();
    __asm__ volatile("" ::: "memory");
    return 0;
}
