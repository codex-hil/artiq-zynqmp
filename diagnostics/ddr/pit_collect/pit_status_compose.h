/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_STATUS_COMPOSE_H
#define PIT_STATUS_COMPOSE_H
#include "pit_sleep_model.h"
#include "pit_terminal_build.h"
#include "pit_ro_adapter.h"
struct pit_status_audit_plan {
    uint32_t consumed;
    struct pit_capture_attempt capture;
    struct pit_attempt publication;
    struct pit_terminal_record record;
    uint64_t nonce;
    struct pit_sleep_ops capture_ops;
    void *capture_context;
    struct pit_ro_adapter *read_adapter; /* Optional in host model; required by audit entry. */
    pit_write_fn receipt_write;
    pit_barrier_fn receipt_barrier;
    void *receipt_context;
    const uint32_t *image_digest, *sample_digest; /* External/untrusted provenance. */
    uint32_t lifecycle_status;
    int32_t metadata_status;
    uint32_t publication_status;
};
/* Returning offline model, no sleep/hardware guarantee. Zero-initialized,
 * exclusive caller-owned plan and disjoint callbacks/digest storage required. */
int pit_status_compose_model(struct pit_status_audit_plan *);
#endif
