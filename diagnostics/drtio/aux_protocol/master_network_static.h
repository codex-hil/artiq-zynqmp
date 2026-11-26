/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_network_start.h"
/* Isolated SINGLE-USE foreground caller. Private aligned BSS context, no
 * reset/rebind API or automatic retry. Gate, bus.ctx and observer_ctx must
 * outlive all calls. Sole CPU0 foreground, never ISR/concurrent. Callback
 * recursion returns BUSY; no thread/IRQ lock or panic cleanup is provided.
 * Poll result1 remains tentative: only snapshot may publish complete/credits.
 * All underlying observer/IRQ/worker/clock/recovery qualifications remain open.
 */
int mns_begin(struct mfo_gate *,uint64_t,const struct mm_bus *,void *,mnh_observer,uint32_t,uint32_t,uint32_t,uint32_t);
int mns_poll(void);
int mns_snapshot(struct mnh_status *);
