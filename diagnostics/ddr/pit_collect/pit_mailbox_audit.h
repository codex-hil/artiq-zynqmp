/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_MAILBOX_AUDIT_H
#define PIT_MAILBOX_AUDIT_H
#include "pit_collect.h"
#include "pit_terminal_record.h"
/* Image-owned allocation only. No runtime hook, producer or external reader.
 * Zero-initialized storage is not a committed result or a sleep receipt. */
struct pit_mailbox_audit {
    struct pit_record samples;
    struct pit_terminal_record terminal;
};
extern volatile struct pit_mailbox_audit pit_mailbox_audit;
#endif
