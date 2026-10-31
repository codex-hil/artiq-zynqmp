# Supplied-word fault formatter/publication model — offline 2026-10-31

LGPL-3.0-or-later. No hardware operation or exception/vector binding.

Portable C formatter emits proposed64-byte/16-u32 schema from caller-supplied
route/validity/special-register words. Requires exclusive disjoint aligned input/
zero output. Rejects bad route/mask or nonzero invalid snapshots without output
writes. Word-oriented staging and output stores, no aggregate memset/libc path.
These are supplied snapshots, not special-register reads or session provenance.

Publisher snapshots and validates16 source words before any callback, consumes
one-shot state, invalidate0/fence/15 payload words/fence/commit1.17 write callbacks
plus2 fence callbacks; all must return. First nonzero callback return yields
visibility unknown and no retry. A failed callback may already have affected
memory, so no rollback/complete record claim. Snapshot survives source mutation
by callbacks under valid stack/state ownership premises. Not an exception-safe
entry handler: function-pointer callbacks and C stack are host-model contracts.

Tests compare both routes/all16 masks with host reference codec, exact successful
record, source mutation during callback, failure at each19 stages, unchanged
invalid outputs/records and one-shot rejection. Separate ASan/UBSan formatter+
publisher execution passes. Actual standalone MicroBlaze object has no undefined
symbols or detected subword-store mnemonics; formatter frame68, publisher120.
No linked exceptional call graph, ABI entry, dedicated stack, reentrancy exclusion,
concrete slot visibility or physical behavior is established. Existing image and
all frozen profiles remain unchanged; linked exception printf gap is not repaired.

Next safe offline step: separate target-only owned64-byte slot/direct word-store
writer and explicit fence candidate, with linker bounds/word-store checks and no
callback dispatch. Keep it unbound from vectors. Actual exception entry/register/
stack safety, nested fault behavior and preserved notification policy require
separate review before any audit image/vector change. No deployment, external
PMU RAM consumer, sleep or recovery admission follows.

Full PIT Python suite:142 tests PASS.
