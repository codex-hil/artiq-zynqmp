/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_MAILBOX_AUDIT_H
#define PIT_MAILBOX_AUDIT_H
#include "pit_collect.h"
#include "pit_terminal_record.h"
/* Image-owned allocation only. No runtime hook, producer or external reader.
 * Zero-initialized storage is not a committed result or a sleep receipt. */
struct pit_mailbox_audit {
    union { struct pit_record samples; uint32_t sample_words[12]; };
    union { struct pit_terminal_record terminal; uint32_t terminal_words[24]; };
};
extern volatile struct pit_mailbox_audit pit_mailbox_audit;
#endif
