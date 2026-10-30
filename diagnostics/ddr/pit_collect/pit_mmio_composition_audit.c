/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_TERMINAL_AUDIT_ONLY) || !defined(ARTIQ_PIT_MMIO_AUDIT_ONLY)
#error "Explicit MicroBlaze terminal/MMIO audit opt-ins required; no deployment"
#endif
#include "pit_status_compose.h"
#include "pit_mmio_read.h"
extern __attribute__((noreturn)) void pit_terminal_audit(void);
/* Separate linked audit profile. No main/request hook or physical consumer.
 * Context NULL is required by the concrete raw callback; remaining callbacks
 * and image/sample digests are still externally supplied, not authenticated.
 * Never silently replace an already selected transport or consumed plan. */
__attribute__((noinline,noreturn,used)) void pit_mmio_composition_audit(
    struct pit_status_audit_plan *plan)
{
    if(plan && plan->read_adapter && !plan->capture_context &&
       !plan->capture_ops.read && !plan->consumed) {
        plan->capture_ops.read=pit_mmio_read;
        (void)pit_status_compose_model(plan);
    }
    pit_terminal_audit();
}
