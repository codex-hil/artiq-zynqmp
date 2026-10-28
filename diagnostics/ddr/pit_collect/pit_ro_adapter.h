/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_RO_ADAPTER_H
#define PIT_RO_ADAPTER_H
#include "pit_collect.h"
struct pit_ro_adapter {
    pit_read_fn transport;
    void *context;
    uint32_t armed, attempted, failed, busy;
};
/* Caller owns zero-initialized state. Single-context, not a lock/security
 * boundary. The injected transport must perform one returning read only.
 * No MMIO backend is supplied; there is no timeout/preemption of hung reads.
 */
int pit_ro_prepare(struct pit_ro_adapter *, pit_read_fn, void *);
int pit_ro_read(void *, uint32_t, uint32_t *);
#endif
