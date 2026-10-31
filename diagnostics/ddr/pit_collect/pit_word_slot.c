/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_word_slot.h"
int pit_word_slot_prepare(struct pit_word_slot *slot, volatile uint32_t *words,
                          uint32_t count, pit_barrier_fn fence, void *context)
{
    unsigned i;
    if(!slot || !words || ((uintptr_t)words&3) || !fence ||
       (count!=12 && count!=24) || slot->armed || slot->failed || slot->busy || slot->step)
        return -1;
    for(i=0;i<count;++i) if(words[i]) return -1;
    slot->words=words;slot->word_count=count;
    slot->fence=fence;slot->fence_context=context;slot->armed=1;
    return 0;
}
int pit_word_slot_write(void *context, uint32_t offset, uint32_t value)
{
    struct pit_word_slot *slot=context;
    uint32_t expected;
    if(!slot || !slot->armed || slot->failed || slot->busy) return -1;
    if((offset&3) || offset>=slot->word_count*4) {slot->failed=1;return -1;}
    if(slot->step==0) {
        if(offset || value) {slot->failed=1;return -1;}
    } else if(slot->step>=2 && slot->step<=slot->word_count) {
        expected=(slot->step-1)*4;
        if(offset!=expected) {slot->failed=1;return -1;}
    } else if(slot->step==slot->word_count+2) {
        if(offset || value!=1) {slot->failed=1;return -1;}
    } else {slot->failed=1;return -1;}
    slot->busy=1;
    ++slot->step; /* Consume before the store. No rollback after uncertain writes. */
    slot->words[offset/4]=value;
    slot->busy=0;
    return 0;
}
int pit_word_slot_barrier(void *context)
{
    struct pit_word_slot *slot=context;
    int result;
    if(!slot || !slot->armed || slot->failed || slot->busy) return -1;
    if(slot->step!=1 && slot->step!=slot->word_count+1) {slot->failed=1;return -1;}
    slot->busy=1;
    ++slot->step;
    result=slot->fence(slot->fence_context);
    slot->busy=0;
    if(result) {slot->failed=1;return -1;}
    return 0;
}
