/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_capture.h"
enum pit_capture_status pit_capture(struct pit_capture_attempt *attempt, uint64_t nonce,
                                   pit_read_fn read, pit_write_fn write,
                                   pit_barrier_fn barrier, void *ctx)
{
    struct pit_attempt collection = {0}, publication = {0};
    union { struct pit_record record; uint32_t words[12]; } storage;
    unsigned i;
    _Static_assert(sizeof(storage) == 48, "word-initialized record size");
    if (!attempt || !nonce || !read || !write || !barrier || attempt->consumed)
        return PIT_CAPTURE_REJECTED;
    attempt->consumed = 1;
    /* C union representation view, aligned by pit_record. Volatile word stores
     * prevent aggregate clearing from becoming library memset byte paths. */
    for (i = 0; i < 12; ++i)
        ((volatile uint32_t *)storage.words)[i] = 0;
    if (pit_collect(&collection, &storage.record, nonce, read, ctx) != PIT_COMPLETE_OFFLINE)
        return PIT_CAPTURE_READ_FAILED;
    if (pit_publish(&publication, &storage.record, nonce, write, barrier, ctx) !=
        PIT_CALLBACKS_RETURNED_OFFLINE)
        return PIT_CAPTURE_PUBLICATION_UNKNOWN;
    return PIT_CAPTURE_OFFLINE_COMPLETE;
}
