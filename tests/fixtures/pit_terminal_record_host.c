/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "pit_terminal_record.h"
struct fake {
    struct pit_attempt *attempt;
    struct pit_terminal_record *record;
    unsigned calls;
    int cut, after;
    uint32_t slot[24];
};
static int write_word(void *, uint32_t, uint32_t);
static int barrier(void *);
static int event(struct fake *f, int is_barrier, uint32_t offset, uint32_t value)
{
    unsigned n = f->calls++;
    assert(pit_terminal_publish(f->attempt, f->record, f->record->nonce, write_word, barrier, f) == PIT_PUBLISH_REJECTED);
    assert(is_barrier == (n == 1 || n == 25));
    if (!is_barrier) {
        assert(offset == (n == 0 || n == 26 ? 0 : (n-1)*4));
        assert(!(offset % 4) && offset < 96);
    }
    if (n == 0) f->record->image_sha256_le[0] = UINT32_C(0xdeadbeef);
    if ((int)n == f->cut && !f->after) return -1;
    if (!is_barrier) f->slot[offset/4] = value;
    return (int)n == f->cut && f->after ? -1 : 0;
}
static int write_word(void *ctx, uint32_t offset, uint32_t value)
{ return event(ctx, 0, offset, value); }
static int barrier(void *ctx) { return event(ctx, 1, 0, 0); }
static struct pit_terminal_record source(void)
{
    struct pit_terminal_record r = {1, PIT_TERMINAL_MAGIC, 1, 1,
        UINT64_C(0x123456789abcdef0), 0x80000104, 0x80000106, {0}, {0}};
    unsigned i;
    for (i = 0; i < 8; ++i) r.image_sha256_le[i] = UINT32_C(0x12121212);
    return r;
}
int main(void)
{
    int cut, after, old;
    for (old = 0; old < 2; ++old)
    for (after = 0; after < 2; ++after)
    for (cut = -1; cut < 27; ++cut) {
        struct pit_attempt a = {0};
        struct pit_terminal_record r = source();
        struct fake f = {&a, &r, 0, cut, after, {0}};
        enum pit_publish_status status;
        if (old) {f.slot[0] = 1; f.slot[4] = 8;}
        status = pit_terminal_publish(&a, &r, r.nonce, write_word, barrier, &f);
        assert(a.consumed && f.calls == (cut < 0 ? 27u : (unsigned)cut+1));
        assert(status == (cut < 0 ? PIT_CALLBACKS_RETURNED_OFFLINE : PIT_VISIBILITY_UNKNOWN));
        if (cut < 0 || (cut == 26 && after)) {
            assert(f.slot[0] == 1 && f.slot[4] == UINT32_C(0x9abcdef0));
            assert(f.slot[8] == UINT32_C(0x12121212));
        } else assert(f.slot[0] != 1 || f.slot[4] != UINT32_C(0x9abcdef0));
    }
    {
        unsigned status;
        for (status = 1; status <= 4; ++status) {
            struct pit_attempt a = {0};
            struct pit_terminal_record r = source();
            struct fake f = {&a, &r, 0, -1, 0, {0}};
            r.status = status; r.final_msr = r.checked_msr;
            r.sample_sha256_le[0] = 1; /* Provided digest, not computed/authenticated here. */
            assert(pit_terminal_publish(&a, &r, r.nonce, write_word, barrier, &f) == PIT_CALLBACKS_RETURNED_OFFLINE);
            assert(f.slot[3] == status && f.slot[8] == UINT32_C(0x12121212));
        }
    }
    {
        struct pit_attempt a = {0};
        struct pit_terminal_record r = source();
        struct fake f = {&a, &r, 0, -1, 0, {0}};
        unsigned i, j;
        r.status = 4;
        assert(pit_terminal_publish(&a, &r, r.nonce, write_word, barrier, &f) == PIT_PUBLISH_REJECTED);
        assert(!a.consumed && !f.calls);
        r.status = 1;
        assert(pit_terminal_publish(&a, &r, r.nonce, write_word, barrier, &f) == PIT_CALLBACKS_RETURNED_OFFLINE);
        for (i = 0; i < 24; ++i)
            for (j = 0; j < 4; ++j) putchar((int)((f.slot[i] >> (j*8)) & 255));
    }
    return 0;
}
