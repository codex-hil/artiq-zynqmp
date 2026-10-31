/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_TERMINAL_AUDIT_ONLY) || !defined(ARTIQ_PIT_MMIO_AUDIT_ONLY)
#error "Explicit MicroBlaze terminal/MMIO audit opt-ins required; no deployment"
#endif
#include "pit_status_compose.h"
#include "pit_mailbox_publish_audit.h"
extern __attribute__((noreturn)) void pit_mmio_composition_audit(struct pit_status_audit_plan *);
extern __attribute__((noreturn)) void pit_terminal_audit(void);
/* Separate root binds only the owned mailbox wrappers. Caller-supplied MSR/
 * disable callbacks and digest provenance remain unqualified. No main hook. */
__attribute__((noinline,noreturn,used)) void pit_mailbox_composition_audit(
    struct pit_status_audit_plan *plan)
{
    if(!plan || !plan->read_adapter || plan->capture_context || plan->receipt_context ||
       plan->consumed || plan->capture.consumed || plan->publication.consumed ||
       plan->record.commit || !plan->nonce || !plan->image_digest || !plan->sample_digest ||
       !plan->capture_ops.msr || !plan->capture_ops.disable || plan->capture_ops.read ||
       plan->capture_ops.write || plan->capture_ops.barrier || plan->receipt_write ||
       plan->receipt_barrier || plan->read_adapter->armed || plan->read_adapter->attempted ||
       plan->read_adapter->failed || plan->read_adapter->busy)
        pit_terminal_audit();
    if(pit_mailbox_prepare_audit()) pit_terminal_audit();
    plan->capture_ops.write=pit_mailbox_sample_write_audit;
    plan->capture_ops.barrier=pit_mailbox_sample_barrier_audit;
    plan->receipt_write=pit_mailbox_terminal_write_audit;
    plan->receipt_barrier=pit_mailbox_terminal_barrier_audit;
    pit_mmio_composition_audit(plan);
}
