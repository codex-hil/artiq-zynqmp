/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_network_fault_latch.h"
#include "master_network_start.h"
/* View initialized before producers/consumer and then immutable. Generation
 * and exact receipt mask come from separate qualification, never inferred
 * from a clear latch. Foreground only; producer never calls the owner policy.
 * Result is linearized at acquire load, not a guarantee against a later IRQ.
 * Fault after a read may require next post-step/snapshot check; in-flight IO
 * and atomic success-vs-IRQ serialization remain external requirements.
 */
struct mnf_view {const struct mnf_latch *latch;uint64_t generation;unsigned receipts;};
static inline int mnf_observe(void *ctx,struct mnh_health *out){
 const struct mnf_view *v=ctx;
 if(!v||!out||!v->latch||!v->generation||v->receipts!=MNE_RECEIPTS)return -1;
 *out=(struct mnh_health){.generation=v->generation,.receipts=v->receipts,.fault=(int)mnf_seen(v->latch)};
 return 0;
}
