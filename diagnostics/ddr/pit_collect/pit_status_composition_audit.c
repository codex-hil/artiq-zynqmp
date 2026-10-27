/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_TERMINAL_AUDIT_ONLY)
#error "MicroBlaze audit-only compilation required; no deployment profile"
#endif
#include "pit_status_compose.h"
extern __attribute__((noreturn)) void pit_terminal_audit(void);
/* Linked audit arrangement only: no PMU main hook or physical callbacks.
 * Metadata MSR values/validity now come from forwarding callback observations.
 * Hash provenance, live IRQ after receipt write and actual sleep remain OPEN. */
__attribute__((noinline,noreturn,used)) void pit_status_composition_audit(
    struct pit_status_audit_plan *plan)
{
    (void)pit_status_compose_model(plan);
    pit_terminal_audit();
}
