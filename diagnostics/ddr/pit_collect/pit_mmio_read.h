/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_MMIO_READ_H
#define PIT_MMIO_READ_H
#include "pit_collect.h"
/* PMU-local raw callback only. Context must be NULL. Returning zero means the
 * volatile load returned, not that bus faults/hangs are recovered. Sequence and
 * eight-load budget belong to pit_ro_adapter. No physical deployment admission. */
int pit_mmio_read(void *, uint32_t, uint32_t *);
#endif
