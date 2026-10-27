/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_collect.h"
enum pit_status pit_collect(struct pit_attempt *attempt, struct pit_record *out,
                            uint64_t nonce, pit_read_fn read, void *ctx)
{
    uint32_t staged[8] = {0};
    unsigned i;
    if (!attempt || !out || !nonce || !read || attempt->consumed || out->complete)
        return PIT_REJECTED;
    attempt->consumed = 1;
    /* Caller must not expose this record as a receipt until successful return. */
    for (i = 0; i < 8; ++i) {
        if (read(ctx, UINT32_C(0xffd40044) + (i % 4) * 16, &staged[i]))
            return PIT_INCOMPLETE;
    }
    out->version = 1;
    out->nonce = nonce;
    for (i = 0; i < 8; ++i)
        out->values[i] = staged[i];
    out->complete = 1;
    return PIT_COMPLETE_OFFLINE;
}
