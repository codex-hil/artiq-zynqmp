/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_PUBLISH_H
#define PIT_PUBLISH_H
#include "pit_collect.h"
/* Offsets only, not physical addresses. Callbacks return 0 or failure.
 * Caller owns a fresh session/slot and separate source/state. Single context.
 * Barrier callback must establish actual platform visibility; none supplied.
 * A returned error may follow a completed write. No retry or rollback.
 */
typedef int (*pit_write_fn)(void *, uint32_t offset, uint32_t value);
typedef int (*pit_barrier_fn)(void *);
enum pit_publish_status { PIT_PUBLISH_REJECTED, PIT_VISIBILITY_UNKNOWN,
                          PIT_CALLBACKS_RETURNED_OFFLINE };
enum pit_publish_status pit_publish(struct pit_attempt *, const struct pit_record *,
                                   uint64_t expected_nonce, pit_write_fn,
                                   pit_barrier_fn, void *);
#endif
