/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_WORD_SLOT_H
#define PIT_WORD_SLOT_H
#include "pit_publish.h"
/* Exclusive zero-initialized caller-owned state, disjoint from words/context.
 * Not a lock or sandbox. Do not reset/reuse to create another publication. */
struct pit_word_slot {
    volatile uint32_t *words;
    pit_barrier_fn fence;
    void *fence_context;
    uint32_t word_count, step, armed, failed, busy;
};
int pit_word_slot_prepare(struct pit_word_slot *, volatile uint32_t *, uint32_t,
                          pit_barrier_fn, void *);
int pit_word_slot_write(void *, uint32_t, uint32_t);
int pit_word_slot_barrier(void *);
#endif
