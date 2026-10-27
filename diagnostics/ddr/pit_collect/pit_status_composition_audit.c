/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_TERMINAL_AUDIT_ONLY)
#error "MicroBlaze audit-only compilation required; no deployment profile"
#endif
#include "pit_sleep_model.h"
#include "pit_terminal_record.h"
extern __attribute__((noreturn)) void pit_terminal_audit(void);
/* Caller-supplied audit inputs only. No storage allocation, hardware backend,
 * hash producer, metadata population, boot identity or main/request hook.
 */
struct pit_status_audit_plan {
    struct pit_capture_attempt capture;
    struct pit_attempt publication;
    struct pit_terminal_record record;
    uint64_t nonce;
    struct pit_sleep_ops capture_ops;
    void *capture_context;
    pit_write_fn receipt_write;
    pit_barrier_fn receipt_barrier;
    void *receipt_context;
    volatile uint32_t publication_status;
};
static void deferred_terminal(void *ctx, int status)
{
    (void)ctx; (void)status;
    /* Return only inside audit composition; physical terminal follows receipt. */
}
__attribute__((noinline,noreturn,used)) void pit_status_composition_audit(
    struct pit_status_audit_plan *plan)
{
    if (plan) {
        struct pit_sleep_ops local = plan->capture_ops;
        enum pit_sleep_status status;
        local.terminal = deferred_terminal;
        status = pit_sleep_model(&plan->capture, plan->nonce, &local, plan->capture_context);
        plan->record.status = (uint32_t)status;
        /* MSR/hash fields are external framing inputs, not populated here.
         * Publication errors remain separate from the lifecycle status. */
        plan->publication_status = (uint32_t)pit_terminal_publish(&plan->publication,
            &plan->record, plan->nonce, plan->receipt_write, plan->receipt_barrier,
            plan->receipt_context);
    }
    pit_terminal_audit();
}
