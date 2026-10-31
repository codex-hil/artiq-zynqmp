/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_CAPTURE_DIGEST_H
#define PIT_CAPTURE_DIGEST_H
#include "pit_publish.h"
/* Offline one-shot model. Exclusive zero-initialized state disjoint from all
 * callbacks. Digest_valid identifies intended private bytes, not visibility.
 * Callbacks must return and must not mutate this state or private stack. */
struct pit_digest_attempt { uint32_t consumed, digest_valid, digest_le[8]; };
enum pit_digest_status { PIT_DIGEST_REJECTED, PIT_DIGEST_READ_FAILED,
    PIT_DIGEST_HASH_FAILED, PIT_DIGEST_PUBLICATION_UNKNOWN,
    PIT_DIGEST_CALLBACKS_RETURNED_OFFLINE };
enum pit_digest_status pit_capture_digest(struct pit_digest_attempt *,uint64_t,
    pit_read_fn,pit_write_fn,pit_barrier_fn,void *);
#endif
