/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_DIGEST_COMPOSE_H
#define PIT_DIGEST_COMPOSE_H
#include "pit_digest_terminal.h"
struct pit_digest_plan {
 uint32_t consumed;
 uint64_t nonce;
 struct pit_sleep_ops ops;
 void *capture_context;
 pit_write_fn receipt_write;
 pit_barrier_fn receipt_barrier;
 void *receipt_context;
 const uint32_t *image_digest;
 struct pit_terminal_record record;
 uint32_t lifecycle_status;
 int32_t metadata_status;
 uint32_t publication_status;
};
/* Returning offline model. Exclusive zero result/state, disjoint inputs/callbacks.
 * No sample digest input. Image digest provenance remains external/untrusted.
 * No raw MMIO binding or read-order adapter/root is added by this API. */
int pit_digest_compose(struct pit_digest_plan *);
#endif
