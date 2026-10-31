/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_FAULT_SLOT_AUDIT_H
#define PIT_FAULT_SLOT_AUDIT_H
#include <stdint.h>
extern volatile uint32_t pit_fault_slot_audit[16];
/* Separate opt-in C candidate, NOT exception entry or reentrancy protection.
 * Registers must be valid exclusive aligned storage, disjoint from owned slot.
 * Any admitted first attempt consumes state, even if formatting fails. */
int pit_fault_store_audit(uint32_t route,uint32_t valid,const uint32_t registers[4]);
#endif
