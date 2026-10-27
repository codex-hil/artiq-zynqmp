/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <stddef.h>
#include "pit_terminal_record.h"
_Static_assert(sizeof(struct pit_terminal_record) == 96, "terminal record size");
_Static_assert(offsetof(struct pit_terminal_record, nonce) == 16, "nonce offset");
_Static_assert(offsetof(struct pit_terminal_record, checked_msr) == 24, "MSR offset");
_Static_assert(offsetof(struct pit_terminal_record, image_sha256_le) == 32, "image offset");
_Static_assert(offsetof(struct pit_terminal_record, sample_sha256_le) == 64, "sample offset");
enum pit_publish_status pit_terminal_publish(struct pit_attempt *attempt,
    const struct pit_terminal_record *source, uint64_t nonce,
    pit_write_fn write, pit_barrier_fn barrier, void *ctx)
{
    volatile uint32_t words[23];
    uint32_t image_nonzero = 0, sample_nonzero = 0;
    unsigned i;
    if (!attempt || !source || !nonce || !write || !barrier || attempt->consumed ||
        source->commit != 1 || source->magic != PIT_TERMINAL_MAGIC || source->version != 1 ||
        source->nonce != nonce || source->status < 1 || source->status > 4)
        return PIT_PUBLISH_REJECTED;
    if (source->status == 4 && ((source->checked_msr & 2) || source->checked_msr != source->final_msr))
        return PIT_PUBLISH_REJECTED;
    words[0] = source->magic; words[1] = source->version; words[2] = source->status;
    words[3] = (uint32_t)nonce; words[4] = (uint32_t)(nonce >> 32);
    words[5] = source->checked_msr; words[6] = source->final_msr;
    for (i = 0; i < 8; ++i) {
        uint32_t image = ((const volatile uint32_t *)source->image_sha256_le)[i];
        uint32_t sample = ((const volatile uint32_t *)source->sample_sha256_le)[i];
        words[7+i] = image; words[15+i] = sample;
        image_nonzero |= image; sample_nonzero |= sample;
    }
    if (!image_nonzero || (source->status == 4 && !sample_nonzero))
        return PIT_PUBLISH_REJECTED;
    attempt->consumed = 1;
    if (write(ctx, 0, 0) || barrier(ctx)) return PIT_VISIBILITY_UNKNOWN;
    for (i = 0; i < 23; ++i)
        if (write(ctx, (i+1)*4, words[i])) return PIT_VISIBILITY_UNKNOWN;
    if (barrier(ctx) || write(ctx, 0, 1)) return PIT_VISIBILITY_UNKNOWN;
    return PIT_CALLBACKS_RETURNED_OFFLINE;
}
