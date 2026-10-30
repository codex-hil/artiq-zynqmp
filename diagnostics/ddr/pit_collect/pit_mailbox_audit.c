/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_MMIO_AUDIT_ONLY)
#error "Explicit MicroBlaze MMIO audit-only allocation required; no deployment"
#endif
#include <stddef.h>
#include "pit_mailbox_audit.h"
_Static_assert(sizeof(struct pit_record)==48,"sample layout");
_Static_assert(sizeof(struct pit_terminal_record)==96,"terminal layout");
_Static_assert(offsetof(struct pit_mailbox_audit,samples)==0,"sample offset");
_Static_assert(offsetof(struct pit_mailbox_audit,terminal)==48,"terminal offset");
_Static_assert(sizeof(struct pit_mailbox_audit)==144,"mailbox size");
volatile struct pit_mailbox_audit pit_mailbox_audit
    __attribute__((used,aligned(8),section(".bss.pit_mailbox_audit")));
