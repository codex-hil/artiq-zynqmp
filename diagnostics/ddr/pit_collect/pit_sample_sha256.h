/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_SAMPLE_SHA256_H
#define PIT_SAMPLE_SHA256_H
#include <stdint.h>
/* Fixed canonical 12 little-endian words, no arbitrary-length hash API.
 * Exclusive aligned input/output must be disjoint. Output unchanged on reject.
 * Output is eight little-endian u32 groups of standard SHA256 digest bytes.
 * Offline candidate, not bound into any target capture/runtime. */
int pit_sample_sha256(const uint32_t words[12], uint64_t expected_nonce,
                      uint32_t digest_le[8]);
#endif
