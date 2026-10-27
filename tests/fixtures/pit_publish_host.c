/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <string.h>
#include "pit_publish.h"
struct fake {
    unsigned calls;
    int cut, after;
    uint32_t slot[12];
    struct pit_attempt *attempt;
    struct pit_record *source;
};
static int write_fake(void *, uint32_t, uint32_t);
static int barrier_fake(void *);
static int event(struct fake *f, int barrier, uint32_t offset, uint32_t value)
{
    unsigned n = f->calls++;
    assert(pit_publish(f->attempt, f->source, UINT64_C(0x123456789abcdef0),
                       write_fake, barrier_fake, f) == PIT_PUBLISH_REJECTED);
    if (n == 0) f->source->values[0] = 999; /* private copy must stay unchanged */
    if (n == 1 || n == 13) assert(barrier);
    else {
        assert(!barrier);
        if (n == 0 || n == 14) {
            assert(offset == 0 && value == (n == 14));
        } else assert(offset == (n - 1) * 4);
    }
    if ((int)n == f->cut && !f->after) return -1;
    if (!barrier) f->slot[offset / 4] = value;
    if ((int)n == f->cut && f->after) return -1;
    return 0;
}
static int write_fake(void *ctx, uint32_t offset, uint32_t value)
{ return event(ctx, 0, offset, value); }
static int barrier_fake(void *ctx)
{ return event(ctx, 1, 0, 0); }
int main(void)
{
    int cut, after, old;
    for (old = 0; old < 2; ++old)
    for (after = 0; after < 2; ++after)
    for (cut = -1; cut < 15; ++cut) {
        struct pit_attempt a = {0};
        struct pit_record r = {1, 1, UINT64_C(0x123456789abcdef0), {0,1,2,3,4,5,6,7}};
        struct fake f = {0, cut, after, {0}, &a, &r};
        enum pit_publish_status status;
        if (old) { f.slot[0] = 1; f.slot[1] = 1; f.slot[2] = 8; }
        status = pit_publish(&a, &r, r.nonce, write_fake, barrier_fake, &f);
        assert(a.consumed);
        assert(f.calls == (cut < 0 ? 15u : (unsigned)cut + 1));
        assert(status == (cut < 0 ? PIT_CALLBACKS_RETURNED_OFFLINE : PIT_VISIBILITY_UNKNOWN));
        if (cut < 0 || (cut == 14 && after)) {
            unsigned i;
            assert(f.slot[0] == 1 && f.slot[1] == 1);
            assert(f.slot[2] == UINT32_C(0x9abcdef0) && f.slot[3] == UINT32_C(0x12345678));
            for (i = 0; i < 8; ++i) assert(f.slot[4+i] == i);
        } else assert(f.slot[0] != 1 || f.slot[2] != UINT32_C(0x9abcdef0));
        assert(pit_publish(&a, &r, r.nonce, write_fake, barrier_fake, &f) == PIT_PUBLISH_REJECTED);
    }
    {
        struct pit_attempt a = {0};
        struct pit_record r = {0};
        struct fake f = {0, -1, 0, {0}, &a, &r};
        assert(pit_publish(&a, &r, 7, write_fake, barrier_fake, &f) == PIT_PUBLISH_REJECTED);
        assert(!a.consumed && !f.calls);
        assert(pit_publish(0, &r, 7, write_fake, barrier_fake, &f) == PIT_PUBLISH_REJECTED);
        assert(pit_publish(&a, 0, 7, write_fake, barrier_fake, &f) == PIT_PUBLISH_REJECTED);
    }
    return 0;
}
