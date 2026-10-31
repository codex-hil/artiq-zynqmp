/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_DIGEST_TERMINAL_H
#define PIT_DIGEST_TERMINAL_H
#include "pit_digest_sleep.h"
#include "pit_terminal_build.h"
/* Returning offline adapter. Output initially zero and exclusive, inputs disjoint.
 * Observations must be recorded by the same exclusive session; not authenticated.
 * Explicit hash failure is not representable in terminal v1 and is rejected.
 * No caller sample-digest argument; state must come from private digest producer. */
int pit_digest_terminal(struct pit_terminal_record *,const struct pit_digest_attempt *,
 enum pit_digest_sleep_status,const struct pit_terminal_observations *,uint64_t,
 const uint32_t image[8]);
#endif
