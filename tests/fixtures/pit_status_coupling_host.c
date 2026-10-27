/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "pit_sleep_model.h"
#include "pit_terminal_record.h"
struct fake {
    struct pit_capture_attempt lifecycle;
    struct pit_attempt receipt_attempt;
    unsigned reads, msr_calls, sample_calls, receipt_calls, terminals;
    int mode, cut, after, lifecycle_status, read_failed, sample_publish_failed;
    uint32_t observed_msr[3];
    enum pit_publish_status receipt_status;
    uint32_t samples[12], receipt[24], msr;
};
static int msr_read(void *ctx, uint32_t *out)
{ struct fake *f = ctx; assert(f->msr_calls < 3); f->observed_msr[f->msr_calls] = f->msr; ++f->msr_calls; *out = f->msr; return 0; }
static int disable(void *ctx) { struct fake *f = ctx; f->msr &= ~UINT32_C(2); return 0; }
static int read_word(void *ctx, uint32_t address, uint32_t *out)
{
    struct fake *f = ctx;
    assert(!f->terminals && !f->sample_calls);
    assert(address == UINT32_C(0xffd40044) + (f->reads % 4)*16);
    *out = f->reads++;
    if (f->mode == 3) f->msr |= 2;
    if (f->mode == 1 && f->reads == 3) { f->read_failed = 1; return -1; }
    return 0;
}
static int sample_write(void *ctx, uint32_t offset, uint32_t value)
{
    struct fake *f = ctx;
    assert(f->reads == 8 && !f->terminals && offset < 48 && !(offset%4));
    ++f->sample_calls; f->samples[offset/4] = value;
    /* Sample commit completed, but transport reports error. */
    if (f->mode == 2 && offset == 0 && value == 1) { f->sample_publish_failed = 1; return -1; }
    return 0;
}
static int sample_barrier(void *ctx) { (void)ctx; return 0; }
static int receipt_event(struct fake *f, int barrier, uint32_t offset, uint32_t value)
{
    unsigned index = f->receipt_calls++;
    assert(f->terminals == 1 && f->msr_calls == 3);
    assert(barrier == (index == 1 || index == 25));
    if (f->mode == 4) f->msr |= 2; /* Change AFTER reported final-MSR snapshot. */
    if ((int)index == f->cut && !f->after) return -1;
    if (!barrier) {assert(offset < 96 && !(offset%4)); f->receipt[offset/4] = value;}
    return (int)index == f->cut && f->after ? -1 : 0;
}
static int receipt_write(void *ctx, uint32_t offset, uint32_t value)
{ return receipt_event(ctx, 0, offset, value); }
static int receipt_barrier(void *ctx) { return receipt_event(ctx, 1, 0, 0); }
static void terminal(void *ctx, int status)
{
    struct fake *f = ctx;
    const uint32_t digest[8] = {UINT32_C(0x309c7563),UINT32_C(0xbea00649),UINT32_C(0xadc9f4c1),UINT32_C(0xc95c2fae),UINT32_C(0xf5b1b669),UINT32_C(0x69aa2086),UINT32_C(0xe4c2c3ce),UINT32_C(0x8bbff9e5)};
    struct pit_terminal_record r = {1,PIT_TERMINAL_MAGIC,1,0,7,0x80000104,0,{0},{0}};
#ifdef PIT_EVENT_TRACE
    const uint32_t image_digest[8] = {UINT32_C(0x884f7616),UINT32_C(0x32fd6cbe),UINT32_C(0xdcb8d26e),UINT32_C(0xa701518c),UINT32_C(0x58b43df6),UINT32_C(0x52ca1e97),UINT32_C(0xcb61b320),UINT32_C(0xdaaa4eb0)};
#endif
    unsigned i;
    assert(!f->terminals && f->msr_calls == 3);
    ++f->terminals; f->lifecycle_status = status;
    r.status = (uint32_t)status; r.final_msr = f->msr;
    for (i = 0; i < 8; ++i) {
#ifdef PIT_EVENT_TRACE
        r.image_sha256_le[i] = image_digest[i];
#else
        r.image_sha256_le[i] = UINT32_C(0x12121212);
#endif
        /* Fake fixed-vector digest only, not target hashing implementation. */
        if (f->samples[0]) r.sample_sha256_le[i] = digest[i];
    }
    f->receipt_status = pit_terminal_publish(&f->receipt_attempt, &r, 7,
                                            receipt_write, receipt_barrier, f);
    /* Returning fixture terminal; does NOT model physical sleep. */
}
static void emit(const uint32_t *words, unsigned count)
{
    unsigned i,j;
    for (i=0;i<count;++i) for(j=0;j<4;++j) putchar((int)((words[i]>>(j*8))&255));
}
static void run(int mode, int cut, int after, int output)
{
    struct fake f = {0};
    struct pit_sleep_ops ops = {msr_read,disable,read_word,sample_write,sample_barrier,terminal};
    enum pit_sleep_status result;
    int expected[] = {PIT_SLEEP_CAPTURE_COMPLETE,PIT_SLEEP_READ_FAILED,PIT_SLEEP_PUBLICATION_UNKNOWN,PIT_SLEEP_IRQ_UNPROVEN,PIT_SLEEP_CAPTURE_COMPLETE};
    f.mode=mode;f.cut=cut;f.after=after;f.msr=UINT32_C(0x80000106);
    result=pit_sleep_model(&f.lifecycle,7,&ops,&f);
    assert((int)result==expected[mode] && f.lifecycle_status==(int)result);
    assert(f.terminals==1 && f.lifecycle.consumed && f.receipt_attempt.consumed);
    assert(f.receipt_calls==(cut<0?27u:(unsigned)cut+1));
    assert(f.receipt_status==(cut<0?PIT_CALLBACKS_RETURNED_OFFLINE:PIT_VISIBILITY_UNKNOWN));
    if (mode==1) assert(!f.samples[0] && !f.sample_calls);
    else assert(f.samples[0]==1);
    if(cut==26 && after) assert(f.receipt[0]==1); /* UNKNOWN can have committed receipt. */
    if(mode==4) assert((f.msr & 2) && f.receipt[3]==PIT_SLEEP_CAPTURE_COMPLETE);
    if(output) {
#ifdef PIT_EVENT_TRACE
        uint32_t header[11] = {UINT32_C(0x50544531),1,(uint32_t)mode,f.msr_calls,
            f.observed_msr[0],f.observed_msr[1],f.observed_msr[2],
            f.read_failed ? 2u : (f.sample_publish_failed ? 3u : 4u),
            (uint32_t)result,(uint32_t)f.receipt_status,f.msr};
        emit(header,11);
#endif
        emit(f.samples,12);emit(f.receipt,24);
    }
}
int main(void)
{
    int mode,cut,after;
    for(mode=0;mode<5;++mode)run(mode,-1,0,1);
    for(after=0;after<2;++after)for(cut=0;cut<27;++cut)run(0,cut,after,0);
    return 0;
}
