/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef ARTIQ_AIB_STRICT_H
#define ARTIQ_AIB_STRICT_H
#include <stdint.h>
enum aib_reg { AIB_REQ, AIB_ACK, AIB_TYPE };
enum aib_status { AIB_REJECTED, AIB_DRAIN_OBSERVED, AIB_TIMEOUT,
 AIB_CHANGED, AIB_IO_UNCERTAIN, AIB_CLOCK_ERROR };
struct aib_io {
 void *ctx;
 int (*read)(void *,enum aib_reg,uint32_t *);
 int (*write_request)(void *,uint32_t);
 int (*ticks)(void *,uint64_t *);
};
struct aib_result {
 enum aib_status status;
 uint32_t mask, original_request, requested_word, last_ack, response_type, polls;
 unsigned write_attempted, destructive_test_allowed;
};
/* Callback-only protocol. No MMIO backend, resume, release or hardware permit.
 * Callbacks must themselves be bounded. Caller must exclude competing writers.
 * Write error may mean partial/accepted write; never automatically undo it. */
struct aib_result aib_strict_hold(const struct aib_io *,uint32_t mask,
 uint32_t poll_budget,uint64_t timeout_ticks);
#endif
