/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_CAPTURE_H
#define PIT_CAPTURE_H
#include "pit_publish.h"
/* Zero-initialized, caller-owned state; single execution context, no reset reuse.
 * Physical session freshness, ownership and bounded callbacks remain external.
 */
struct pit_capture_attempt { uint32_t consumed; };
enum pit_capture_status { PIT_CAPTURE_REJECTED, PIT_CAPTURE_READ_FAILED,
                          PIT_CAPTURE_PUBLICATION_UNKNOWN, PIT_CAPTURE_OFFLINE_COMPLETE };
enum pit_capture_status pit_capture(struct pit_capture_attempt *, uint64_t,
                                   pit_read_fn, pit_write_fn, pit_barrier_fn, void *);
#endif
