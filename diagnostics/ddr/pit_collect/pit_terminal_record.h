/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_TERMINAL_RECORD_H
#define PIT_TERMINAL_RECORD_H
#include "pit_publish.h"
#define PIT_TERMINAL_MAGIC UINT32_C(0x50545331)
/* SHA256 byte strings represented as little-endian u32 groups to avoid byte
 * writes in PMU RAM. Hash computation/provenance is external, not supplied.
 * This is software intent/status, NEVER proof of actual sleep or visibility.
 */
struct pit_terminal_record {
    uint32_t commit, magic, version, status;
    uint64_t nonce;
    uint32_t checked_msr, final_msr;
    uint32_t image_sha256_le[8], sample_sha256_le[8];
};
enum pit_publish_status pit_terminal_publish(struct pit_attempt *,
    const struct pit_terminal_record *, uint64_t, pit_write_fn, pit_barrier_fn, void *);
#endif
