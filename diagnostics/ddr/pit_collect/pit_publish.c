/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_publish.h"
enum pit_publish_status pit_publish(struct pit_attempt *attempt,
                                   const struct pit_record *source,
                                   uint64_t nonce, pit_write_fn write,
                                   pit_barrier_fn barrier, void *ctx)
{
    volatile uint32_t words[11];
    unsigned i;
    if (!attempt || !source || !nonce || !write || !barrier ||
        attempt->consumed || source->complete != 1 || source->version != 1 ||
        source->nonce != nonce)
        return PIT_PUBLISH_REJECTED;
    /* Freeze private source before callbacks; callbacks cannot change payload. */
    words[0] = 1;
    words[1] = (uint32_t)nonce;
    words[2] = (uint32_t)(nonce >> 32);
    for (i = 0; i < 8; ++i)
        words[i + 3] = ((const volatile uint32_t *)source->values)[i];
    attempt->consumed = 1;
    if (write(ctx, 0, 0) || barrier(ctx))
        return PIT_VISIBILITY_UNKNOWN;
    for (i = 0; i < 11; ++i)
        if (write(ctx, (i + 1) * 4, words[i]))
            return PIT_VISIBILITY_UNKNOWN;
    if (barrier(ctx) || write(ctx, 0, 1))
        return PIT_VISIBILITY_UNKNOWN;
    return PIT_CALLBACKS_RETURNED_OFFLINE;
}
