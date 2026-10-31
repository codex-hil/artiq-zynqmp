/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "pit_word_slot.h"
#include "pit_terminal_record.h"
struct fake { struct pit_word_slot *slot; unsigned calls, fail_at; };
static int fence(void *context) {
    struct fake *f=context;++f->calls;
    assert(f->slot->words[0]==0);
    assert(pit_word_slot_write(f->slot,0,1)==-1); /* Reentry refused. */
    assert(pit_word_slot_barrier(f->slot)==-1);
    assert(!f->slot->failed);
    return f->calls==f->fail_at?-1:0;
}
static void step(struct pit_word_slot *s) {
    unsigned n=s->step;
    if(n==1 || n==s->word_count+1) assert(pit_word_slot_barrier(s)==0);
    else assert(pit_word_slot_write(s,n==0 || n==s->word_count+2?0:(n-1)*4,
          n==0?0:(n==s->word_count+2?1:0x12340000+n))==0);
}
static void success(void) {
    uint32_t sample[12]={0},terminal[24]={0};
    struct pit_word_slot s={0},t={0};struct fake fs={&s,0,0},ft={&t,0,0};
    struct pit_attempt a={0},b={0};struct pit_record record={.complete=1,.version=1,.nonce=7};
    struct pit_terminal_record receipt={.commit=1,.magic=PIT_TERMINAL_MAGIC,.version=1,
        .status=4,.nonce=7,.checked_msr=0x104,.final_msr=0x104,.image_sha256_le={1},.sample_sha256_le={2}};
    for(unsigned i=0;i<8;i++)record.values[i]=i;
    assert(pit_word_slot_prepare(&s,sample,12,fence,&fs)==0);
    assert(pit_word_slot_prepare(&t,terminal,24,fence,&ft)==0);
    assert(pit_publish(&a,&record,7,pit_word_slot_write,pit_word_slot_barrier,&s)==PIT_CALLBACKS_RETURNED_OFFLINE);
    assert(pit_terminal_publish(&b,&receipt,7,pit_word_slot_write,pit_word_slot_barrier,&t)==PIT_CALLBACKS_RETURNED_OFFLINE);
    assert(memcmp(sample,&record,48)==0 && memcmp(terminal,&receipt,96)==0);
    assert(s.step==15 && t.step==27 && fs.calls==2 && ft.calls==2);
    assert(pit_word_slot_prepare(&s,sample,12,fence,&fs)==-1);
    assert(pit_word_slot_write(&s,0,0)==-1 && sample[0]==1);
}
static void faults(void) {
    for(unsigned count=12;count<=24;count+=12) for(unsigned fail=0;fail<count+3;fail++) {
        uint32_t guarded[26]={0},before[26];guarded[0]=0xa55a;guarded[count+1]=0x55aa;
        struct pit_word_slot s={0};struct fake f={&s,0,0};
        assert(pit_word_slot_prepare(&s,guarded+1,count,fence,&f)==0);
        while(s.step<fail)step(&s);
        memcpy(before,guarded,sizeof before);
        assert(pit_word_slot_write(&s,count*4,9)==-1 && s.failed);
        assert(pit_word_slot_write(&s,0,0)==-1 && pit_word_slot_barrier(&s)==-1);
        assert(memcmp(before,guarded,sizeof before)==0);
    }
    for(unsigned count=12;count<=24;count+=12) for(unsigned fail=1;fail<=2;fail++) {
        uint32_t words[24]={0};struct pit_word_slot s={0};struct fake f={&s,0,fail};
        assert(pit_word_slot_prepare(&s,words,count,fence,&f)==0);
        while(!s.failed) {
            if(s.step==1 || s.step==count+1) {if(pit_word_slot_barrier(&s))break;}
            else step(&s);
        }
        assert(s.failed && words[0]==0 && f.calls==fail);
    }
}
static void malformed(void) {
    uint32_t words[24]={0};struct pit_word_slot s={0};struct fake f={&s,0,0};
    assert(pit_word_slot_prepare(&s,words,13,fence,&f)==-1);
    assert(pit_word_slot_prepare(&s,(void *)((char *)words+1),12,fence,&f)==-1);
    assert(pit_word_slot_prepare(&s,words,12,0,&f)==-1);
    words[5]=1;assert(pit_word_slot_prepare(&s,words,12,fence,&f)==-1);words[5]=0;
    assert(pit_word_slot_prepare(&s,words,12,fence,&f)==0);
    assert(pit_word_slot_write(&s,2,0)==-1 && s.failed && words[0]==0);
    for(unsigned k=0;k<3;k++) {
        struct pit_word_slot bad={0};f.slot=&bad;
        assert(pit_word_slot_prepare(&bad,words,12,fence,&f)==0);
        if(k==0)assert(pit_word_slot_write(&bad,0,1)==-1); /* premature commit */
        else if(k==1)assert(pit_word_slot_barrier(&bad)==-1);
        else {assert(pit_word_slot_write(&bad,0,0)==0);assert(pit_word_slot_write(&bad,4,2)==-1);}
        assert(bad.failed && words[0]==0);
    }
}
int main(int argc,char **argv) {
    assert(argc==2);
    if(atoi(argv[1])==0)success();else if(atoi(argv[1])==1)faults();else malformed();
    return 0;
}
