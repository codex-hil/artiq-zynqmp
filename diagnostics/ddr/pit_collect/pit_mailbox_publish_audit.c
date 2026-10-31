/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_MMIO_AUDIT_ONLY)
#error "Explicit MicroBlaze MMIO audit-only publication required; no deployment"
#endif
#include "pit_mailbox_publish_audit.h"
#include "pit_mailbox_audit.h"
static struct pit_word_slot sample_slot, terminal_slot;
static int fence(void *context)
{
    if(context) return -1;
    __asm__ volatile("mbar 1" ::: "memory");
    return 0;
}
int pit_mailbox_prepare_audit(void)
{
    if(pit_word_slot_prepare(&sample_slot,pit_mailbox_audit.sample_words,12,fence,0)) return -1;
    /* A later failure leaves the first slot armed, never rolled back/reused. */
    return pit_word_slot_prepare(&terminal_slot,pit_mailbox_audit.terminal_words,24,fence,0);
}
int pit_mailbox_sample_write_audit(void *context,uint32_t offset,uint32_t value)
{ return context?-1:pit_word_slot_write(&sample_slot,offset,value); }
int pit_mailbox_terminal_write_audit(void *context,uint32_t offset,uint32_t value)
{ return context?-1:pit_word_slot_write(&terminal_slot,offset,value); }
int pit_mailbox_sample_barrier_audit(void *context)
{ return context?-1:pit_word_slot_barrier(&sample_slot); }
int pit_mailbox_terminal_barrier_audit(void *context)
{ return context?-1:pit_word_slot_barrier(&terminal_slot); }
