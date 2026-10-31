/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_DIGEST_SLEEP_H
#define PIT_DIGEST_SLEEP_H
#include "pit_sleep_model.h"
#include "pit_capture_digest.h"
/* Separate returning offline model, not terminal-record v1 status extension.
 * Hash failure deliberately has an explicit distinct outcome. */
enum pit_digest_sleep_status { PIT_DS_REJECTED, PIT_DS_IRQ_UNPROVEN,
 PIT_DS_READ_FAILED, PIT_DS_PUBLICATION_UNKNOWN, PIT_DS_CALLBACKS_RETURNED,
 PIT_DS_HASH_FAILED };
/* Exclusive zero-initialized state; no caller-supplied sample digest. */
enum pit_digest_sleep_status pit_digest_sleep(struct pit_digest_attempt *,uint64_t,
 const struct pit_sleep_ops *,void *);
#endif
