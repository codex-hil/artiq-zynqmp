/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_MAILBOX_PUBLISH_AUDIT_H
#define PIT_MAILBOX_PUBLISH_AUDIT_H
/* Allocation-specific target wrappers; all contexts must be NULL.
 * No main hook or physical reader. Preparation must occur once before capture. */
#include "pit_word_slot.h"
int pit_mailbox_prepare_audit(void);
int pit_mailbox_sample_write_audit(void *, uint32_t, uint32_t);
int pit_mailbox_terminal_write_audit(void *, uint32_t, uint32_t);
int pit_mailbox_sample_barrier_audit(void *);
int pit_mailbox_terminal_barrier_audit(void *);
#endif
