/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_FAULT_RECORD_H
#define PIT_FAULT_RECORD_H
#include "pit_publish.h"
/* Supplied snapshots only, never an exception entry stub. Exclusive disjoint
 * word-aligned buffers/state and returning callbacks required. No session binding.
 * Formatter requires zero output; invalid input leaves output unchanged. */
int pit_fault_format(uint32_t out[16],uint32_t route,uint32_t valid,const uint32_t registers[4]);
enum pit_publish_status pit_fault_publish(struct pit_attempt *,const uint32_t words[16],
 pit_write_fn,pit_barrier_fn,void *);
#endif
