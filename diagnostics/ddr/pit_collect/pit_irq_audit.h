/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_IRQ_AUDIT_H
#define PIT_IRQ_AUDIT_H
#include <stdint.h>
/* Audit-only callback candidates: NULL context, exclusive aligned output.
 * Return zero means instruction/helper returned, not exception exclusion.
 * Compiler barriers are not CPU/bus fences or a no-wake guarantee. */
int pit_irq_msr_audit(void *, uint32_t *);
int pit_irq_disable_audit(void *);
#endif
