# Exact minimal fault-writer scope — offline 2026-11-01

LGPL-3.0-or-later. No hardware operation or firmware/vector/frozen-profile change.

Actual minimal ELF passes a distinct scoped check for pit_fault_store_audit:
ffdd078c/440 bytes/110 words with inlined formatter, direct stores and two mbar1.
Every one-bit mutation of110 words is rejected with consistent changed listings,
so barriers, commit and payload/control bindings are included. Stale listings,
changed/duplicate owned storage and changed BSS/stack bounds reject separately.

Pins cover consumed state ffddd378/4, fault slot ffddd400/64, normal mailbox
ffddd440/144, sample/terminal slot state, BSS and stack symbols. Storage must be
unique writable zero-init load tail, inside BSS and pairwise disjoint. Generic ELF
and normal mailbox checks also run. Stack symbolic range4100 and2288 gap to fixed
service table remain unchanged from successful minimal link. No stack shrink or
reserved-table move. Artifact/source/helper hashes recorded in inputs.json.

This is intentionally a ONE-FUNCTION/layout profile, not a whole-image execution
or source-provenance gate. It does not qualify new digest-root/callback/SHA image
paths, exception vectors, incoming stack/ABI/reentrancy, physical register capture,
external visibility, sleep or recovery. Prior profiles are not repinned and their
frozen copies remain intact. Full vendor-containing ELF stays local.

The writer still takes supplied snapshot pointers on a C stack and returns.
Exception printf path is still present and unqualified; no vector invokes this
candidate. Passing these checks does not permit an external PMU RAM read.

Next safe offline step: specify assembly-entry register/stack/slot ownership
requirements for a separately isolated audit handler, preserving production
notification/vector policy. Identify what can be captured without assuming a
valid C stack and what remains unqualified. No vector replacement, live fault
injection, IRQ/exception disabling or hardware trial is authorized by this scope.

Full PIT Python suite:146 tests PASS.
