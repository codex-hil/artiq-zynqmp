/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <string.h>
#include "pit_collect.h"
struct fake {
    unsigned calls;
    int fail, reenter;
    struct pit_attempt *attempt;
    struct pit_record *record;
};
static int read_fake(void *context, uint32_t address, uint32_t *value)
{
    struct fake *f = context;
    unsigned n = f->calls++;
    assert(address == UINT32_C(0xffd40044) + (n % 4) * 16);
    assert(!f->record->complete);
    if (f->reenter)
        assert(pit_collect(f->attempt, f->record, 9, read_fake, f) == PIT_REJECTED);
    *value = UINT32_C(0xffffffff) - n;
    return (int)n == f->fail ? -1 : 0;
}
int main(void)
{
    int fail;
    for (fail = -1; fail < 8; ++fail) {
        struct pit_attempt a = {0};
        struct pit_record r = {0}, before = r;
        struct fake f = {0, fail, 1, &a, &r};
        enum pit_status status = pit_collect(&a, &r, UINT64_C(0x123456789abcdef0), read_fake, &f);
        assert(a.consumed == 1);
        if (fail >= 0) {
            assert(status == PIT_INCOMPLETE);
            assert(f.calls == (unsigned)fail + 1);
            assert(memcmp(&r, &before, sizeof r) == 0);
        } else {
            unsigned i;
            assert(status == PIT_COMPLETE_OFFLINE && f.calls == 8);
            assert(r.complete == 1 && r.version == 1);
            assert(r.nonce == UINT64_C(0x123456789abcdef0));
            for (i = 0; i < 8; ++i) assert(r.values[i] == UINT32_C(0xffffffff) - i);
        }
        assert(pit_collect(&a, &r, 7, read_fake, &f) == PIT_REJECTED);
    }
    {
        struct pit_attempt a = {0};
        struct pit_record r = {0};
        struct fake f = {0, -1, 0, &a, &r};
        assert(pit_collect(0, &r, 7, read_fake, &f) == PIT_REJECTED);
        assert(pit_collect(&a, 0, 7, read_fake, &f) == PIT_REJECTED);
        assert(pit_collect(&a, &r, 0, read_fake, &f) == PIT_REJECTED);
        assert(pit_collect(&a, &r, 7, 0, &f) == PIT_REJECTED);
        r.complete = 1;
        assert(pit_collect(&a, &r, 7, read_fake, &f) == PIT_REJECTED);
        assert(!a.consumed && !f.calls);
    }
    return 0;
}
