/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_guarded_start.h"
/* Isolated SINGLE-USE foreground candidate, not linked to production runtime.
 * One private aligned BSS context, no heap/automatic context or reset API.
 * Caller-owned gate and bus.ctx must outlive all polls/snapshots. Call only from
 * sole CPU0 foreground, never ISR/concurrent/reentrant. Real hardware lease,
 * worker admission, epoch/readiness and independent fault containment external.
 */
struct mfc_status {unsigned initialized;enum mfg_phase phase;int result;uint64_t ticket,epoch;unsigned profile_bound,candidate_complete;uint32_t routing_completed,credits;};
int mfc_begin(struct mfo_gate *gate,uint64_t ticket,const struct mm_bus *bus,uint32_t poll_budget,uint32_t action_budget,uint32_t routing_budget,uint32_t total_setup_budget);
int mfc_poll(void);
int mfc_cancel(void);
int mfc_snapshot(struct mfc_status *out); /* Memory-only, never runs a service step. */
