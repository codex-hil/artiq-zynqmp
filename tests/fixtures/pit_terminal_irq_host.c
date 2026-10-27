/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include "pit_sleep_model.h"
struct fake {
    struct pit_capture_attempt attempt;
    unsigned msr_calls, reads, writes, terminal;
    uint32_t msr, complete;
    int leak_read, leak_write, fail_final, result;
};
static int msr(void *ctx, uint32_t *out)
{
    struct fake *f = ctx; ++f->msr_calls; *out = f->msr;
    return f->fail_final && f->msr_calls == 3 ? -1 : 0;
}
static int disable(void *ctx)
{ struct fake *f = ctx; f->msr &= ~UINT32_C(2); return 0; }
static int read_word(void *ctx, uint32_t address, uint32_t *out)
{
    struct fake *f = ctx;
    assert(address == UINT32_C(0xffd40044) + (f->reads % 4) * 16);
    ++f->reads; *out = 0;
    if (f->leak_read) f->msr |= 2;
    return 0;
}
static int write_word(void *ctx, uint32_t offset, uint32_t value)
{
    struct fake *f = ctx; ++f->writes;
    if (!offset) f->complete = value;
    if (f->leak_write) f->msr ^= UINT32_C(0x100); /* EE/other policy change */
    return 0;
}
static int barrier(void *ctx) { (void)ctx; return 0; }
static void terminal(void *ctx, int result)
{ struct fake *f = ctx; ++f->terminal; f->result = result; }
int main(void)
{
    int mode;
    for (mode = 0; mode < 4; ++mode) {
        struct fake f = {0};
        struct pit_sleep_ops ops = {msr,disable,read_word,write_word,barrier,terminal};
        enum pit_sleep_status result;
        f.msr = UINT32_C(0x80000106);
        f.leak_read = mode == 1; f.leak_write = mode == 2; f.fail_final = mode == 3;
        result = pit_sleep_model(&f.attempt, 7, &ops, &f);
        assert(result == (mode ? PIT_SLEEP_IRQ_UNPROVEN : PIT_SLEEP_CAPTURE_COMPLETE));
        assert(f.msr_calls == 3 && f.terminal == 1 && f.result == (int)result);
        assert(f.reads == 8 && f.writes == 13 && f.complete == 1);
        /* Even unproven terminal state can coexist with a committed payload. */
    }
    return 0;
}
