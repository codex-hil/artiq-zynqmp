/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_sleep_model.h"
enum pit_sleep_status pit_sleep_model(struct pit_capture_attempt *attempt, uint64_t nonce,
                                     const struct pit_sleep_ops *ops, void *ctx)
{
    uint32_t before = 0, after = 0;
    struct pit_capture_attempt capture = {0};
    enum pit_sleep_status result = PIT_SLEEP_IRQ_UNPROVEN;
    enum pit_capture_status status;
    struct pit_sleep_ops local;
    if (!attempt || !nonce || !ops || !ops->msr || !ops->disable ||
        !ops->read || !ops->write || !ops->barrier || !ops->terminal || attempt->consumed)
        return PIT_SLEEP_REJECTED;
    local = *ops;
    attempt->consumed = 1;
    if (local.msr(ctx, &before) || local.disable(ctx) || local.msr(ctx, &after) ||
        after != (before & ~UINT32_C(2)))
        goto terminal;
    status = pit_capture(&capture, nonce, local.read, local.write, local.barrier, ctx);
    if (status == PIT_CAPTURE_OFFLINE_COMPLETE)
        result = PIT_SLEEP_CAPTURE_COMPLETE;
    else if (status == PIT_CAPTURE_READ_FAILED)
        result = PIT_SLEEP_READ_FAILED;
    else
        result = PIT_SLEEP_PUBLICATION_UNKNOWN;
terminal:
    local.terminal(ctx, result);
    return result; /* Model only; a physical terminal would never return. */
}
