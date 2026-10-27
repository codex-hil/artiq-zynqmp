/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include "pit_sleep_model.h"
struct fake {
    struct pit_capture_attempt attempt;
    struct pit_sleep_ops ops;
    unsigned msrs, disabled, reads, writes, barriers, terminal;
    int fail, status;
};
static void nested(struct fake *f)
{ assert(pit_sleep_model(&f->attempt, 7, &f->ops, f) == PIT_SLEEP_REJECTED); }
static int msr(void *ctx, uint32_t *out)
{
    struct fake *f = ctx;
    nested(f);
    assert(!f->reads && !f->terminal);
    *out = f->msrs++ ? UINT32_C(0x80000104) : UINT32_C(0x80000106);
    if (f->msrs == 2) {
        assert(f->disabled == 1);
        if (f->fail == 3) *out |= 2;
    }
    return f->fail == 0 || (f->fail == 2 && f->msrs == 2) ? -1 : 0;
}
static int disable(void *ctx)
{
    struct fake *f = ctx; nested(f);
    assert(f->msrs == 1 && !f->reads);
    ++f->disabled;
    return f->fail == 1 ? -1 : 0;
}
static int read_word(void *ctx, uint32_t address, uint32_t *out)
{
    struct fake *f = ctx; nested(f);
    assert(f->msrs == 2 && f->disabled == 1 && !f->terminal && !f->writes);
    assert(address == UINT32_C(0xffd40044) + (f->reads % 4) * 16);
    *out = f->reads++;
    return f->fail >= 10 && (int)f->reads == f->fail - 9 ? -1 : 0;
}
static int write_word(void *ctx, uint32_t offset, uint32_t value)
{
    struct fake *f = ctx; nested(f);
    assert(f->reads == 8 && !f->terminal && offset < 48);
    (void)value; ++f->writes;
    return f->fail == 20 ? -1 : 0;
}
static int barrier(void *ctx)
{
    struct fake *f = ctx; nested(f); ++f->barriers;
    assert(f->reads == 8 && !f->terminal);
    return f->fail == 21 ? -1 : 0;
}
static void terminal(void *ctx, int result)
{
    struct fake *f = ctx; nested(f);
    assert(!f->terminal); ++f->terminal; f->status = result;
    /* Real sleep/wake residency is deliberately not modeled. */
}
int main(void)
{
    int failures[] = {-1,0,1,2,3,10,11,12,13,14,15,16,17,20,21};
    unsigned i;
    for (i = 0; i < sizeof failures / sizeof failures[0]; ++i) {
        struct fake f = {0};
        enum pit_sleep_status s;
        f.ops = (struct pit_sleep_ops){msr,disable,read_word,write_word,barrier,terminal};
        f.fail = failures[i];
        s = pit_sleep_model(&f.attempt, 7, &f.ops, &f);
        assert(f.terminal == 1 && f.status == (int)s && f.attempt.consumed);
        if (f.fail == -1) assert(s == PIT_SLEEP_CAPTURE_COMPLETE && f.writes == 13 && f.barriers == 2);
        else if (f.fail <= 3) assert(s == PIT_SLEEP_IRQ_UNPROVEN && !f.reads && !f.writes);
        else if (f.fail <= 17) assert(s == PIT_SLEEP_READ_FAILED && !f.writes && !f.barriers);
        else assert(s == PIT_SLEEP_PUBLICATION_UNKNOWN);
        nested(&f);
    }
    {
        struct fake f = {0};
        assert(pit_sleep_model(&f.attempt, 7, &f.ops, &f) == PIT_SLEEP_REJECTED);
        assert(!f.attempt.consumed && !f.terminal);
    }
    return 0;
}
