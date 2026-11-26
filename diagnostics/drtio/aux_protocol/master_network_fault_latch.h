/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include <stdatomic.h>
#include <limits.h>
_Static_assert(UINT_MAX==0xffffffffu,"Requires 32-bit unsigned int");
_Static_assert(ATOMIC_INT_LOCK_FREE==2,"IRQ path must always be lock-free");
_Static_assert(sizeof(atomic_uint)==4&&_Alignof(atomic_uint)==4,"Reviewed atomic layout");
/* ISOLATED sticky fault publication. Static initializer before IRQ enable,
 * valid pointer for whole lifetime, coherent normal memory. Never reinitialize
 * or copy this object after publication starts. No clear/reset/rearm API.
 * Any producer only stores1; no RMW, retry loop, counter wrap or payload.
 * This is not an IRQ nesting/AXI fault barrier or a health qualification.
 */
struct mnf_latch {atomic_uint fault;};
#define MNF_LATCH_INITIALIZER {ATOMIC_VAR_INIT(0)}
static inline void mnf_publish(struct mnf_latch *latch){atomic_store_explicit(&latch->fault,1u,memory_order_release);}
static inline unsigned mnf_seen(const struct mnf_latch *latch){return atomic_load_explicit(&latch->fault,memory_order_acquire)!=0;}
