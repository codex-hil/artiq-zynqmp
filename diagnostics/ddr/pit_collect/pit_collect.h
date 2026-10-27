/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_COLLECT_H
#define PIT_COLLECT_H
#include <stdint.h>
/* Caller owns zero-initialized state/result, disjoint from callback storage.
 * Single execution context only: this is not a lock or atomic publication.
 * read must return; this interface cannot interrupt a hung MMIO transaction.
 * No hardware backend is supplied. Nonzero read return means failure.
 */
struct pit_attempt { uint32_t consumed; };
struct pit_record {
    uint32_t complete, version;
    uint64_t nonce;
    uint32_t values[8];
};
typedef int (*pit_read_fn)(void *, uint32_t, uint32_t *);
enum pit_status { PIT_REJECTED, PIT_INCOMPLETE, PIT_COMPLETE_OFFLINE };
enum pit_status pit_collect(struct pit_attempt *, struct pit_record *,
                            uint64_t nonce, pit_read_fn, void *);
#endif
