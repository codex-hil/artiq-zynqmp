/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef DDR_PATTERN_H
#define DDR_PATTERN_H
#include <stdint.h>
/* Callbacks must be bounded and return nonzero on fault. No physical backend here. */
struct ddr_io {
 void *context;
 int (*write)(void *, uint64_t, uint64_t);
 int (*read)(void *, uint64_t, uint64_t *);
 int (*barrier)(void *);
};
struct ddr_report {
 uint64_t writes, reads, address, expected, actual;
 uint32_t phase, error;
};
enum { DDR_OK=0, DDR_ARGUMENT=1, DDR_WRITE=2, DDR_BARRIER=3, DDR_READ=4, DDR_MISMATCH=5 };
/* Up to 8192 unique aligned words; both configured DDR windows, never MMIO gap. */
int ddr_pattern(const uint64_t *, uint32_t, const struct ddr_io *, struct ddr_report *);
#endif
