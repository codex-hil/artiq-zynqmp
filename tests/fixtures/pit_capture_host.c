/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include "pit_capture.h"
struct fake {
    struct pit_capture_attempt *attempt;
    unsigned reads, events;
    int read_fail, publish_fail, after;
    uint32_t slot[12];
};
static int read_fake(void *, uint32_t, uint32_t *);
static int write_fake(void *, uint32_t, uint32_t);
static int barrier_fake(void *);
static void nested(struct fake *f)
{
    assert(pit_capture(f->attempt, 7, read_fake, write_fake, barrier_fake, f) == PIT_CAPTURE_REJECTED);
}
static int read_fake(void *ctx, uint32_t address, uint32_t *value)
{
    struct fake *f = ctx;
    unsigned n = f->reads++;
    nested(f);
    assert(!f->events);
    assert(address == UINT32_C(0xffd40044) + (n % 4) * 16);
    *value = n + 100;
    return (int)n == f->read_fail ? -1 : 0;
}
static int event(struct fake *f, int barrier, uint32_t offset, uint32_t value)
{
    unsigned n = f->events++;
    nested(f);
    assert(f->reads == 8);
    assert(barrier == (n == 1 || n == 13));
    if ((int)n == f->publish_fail && !f->after) return -1;
    if (!barrier) {
        assert(offset < 48 && !(offset % 4));
        f->slot[offset / 4] = value;
    }
    return (int)n == f->publish_fail && f->after ? -1 : 0;
}
static int write_fake(void *ctx, uint32_t offset, uint32_t value)
{ return event(ctx, 0, offset, value); }
static int barrier_fake(void *ctx)
{ return event(ctx, 1, 0, 0); }
int main(void)
{
    int fail, after;
    for (fail = 0; fail < 8; ++fail) {
        struct pit_capture_attempt a = {0};
        struct fake f = {&a, 0, 0, fail, -1, 0, {0}};
        assert(pit_capture(&a, 7, read_fake, write_fake, barrier_fake, &f) == PIT_CAPTURE_READ_FAILED);
        assert(f.reads == (unsigned)fail + 1 && !f.events && a.consumed);
        nested(&f);
        assert(!f.events);
    }
    for (after = 0; after < 2; ++after)
    for (fail = -1; fail < 15; ++fail) {
        struct pit_capture_attempt a = {0};
        struct fake f = {&a, 0, 0, -1, fail, after, {0}};
        enum pit_capture_status s = pit_capture(&a, 7, read_fake, write_fake, barrier_fake, &f);
        assert(s == (fail < 0 ? PIT_CAPTURE_OFFLINE_COMPLETE : PIT_CAPTURE_PUBLICATION_UNKNOWN));
        assert(f.reads == 8 && f.events == (fail < 0 ? 15u : (unsigned)fail + 1));
        if (fail < 0 || (fail == 14 && after)) {
            unsigned i;
            assert(f.slot[0] == 1 && f.slot[1] == 1 && f.slot[2] == 7 && !f.slot[3]);
            for (i = 0; i < 8; ++i) assert(f.slot[i+4] == i+100);
        } else assert(!f.slot[0]);
        nested(&f);
    }
    {
        struct pit_capture_attempt a = {0};
        struct fake f = {&a, 0, 0, -1, -1, 0, {0}};
        assert(pit_capture(&a, 0, read_fake, write_fake, barrier_fake, &f) == PIT_CAPTURE_REJECTED);
        assert(pit_capture(&a, 7, 0, write_fake, barrier_fake, &f) == PIT_CAPTURE_REJECTED);
        assert(pit_capture(&a, 7, read_fake, 0, barrier_fake, &f) == PIT_CAPTURE_REJECTED);
        assert(pit_capture(&a, 7, read_fake, write_fake, 0, &f) == PIT_CAPTURE_REJECTED);
        assert(!a.consumed && !f.reads && !f.events);
    }
    return 0;
}
