/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_TERMINAL_AUDIT_ONLY)
#error "MicroBlaze audit-only compilation required; no deployment profile"
#endif
#include "pit_sleep_model.h"
extern __attribute__((noreturn)) void pit_terminal_audit(void);
static __attribute__((noinline,noreturn)) void terminal_adapter(void *ctx, int status)
{
    (void)ctx;
    (void)status;
    pit_terminal_audit();
}
/* Retained for linked-flow analysis only. NOT hooked into vendor main/request.
 * Caller callbacks remain abstract; no physical transport/MSR implementation.
 */
__attribute__((noinline,noreturn,used)) void pit_profile_entry_audit(
    struct pit_capture_attempt *attempt, uint64_t nonce,
    const struct pit_sleep_ops *ops, void *ctx)
{
    if (ops) {
        struct pit_sleep_ops local = *ops;
        local.terminal = terminal_adapter;
        (void)pit_sleep_model(attempt, nonce, &local, ctx);
    }
    /* Rejected input also parks; successful/failed admitted paths use adapter. */
    pit_terminal_audit();
}
