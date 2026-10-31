# Digest-aware lifecycle candidate — offline 2026-10-31

LGPL-3.0-or-later. No hardware operations or runtime integration.

New separate pit_digest_sleep returning model reserves caller state before any
callback. It uses private capture/digest state, invokes existing capture/hash/
publication candidate and copies internally produced digest. No sample hash input
is accepted. Initial MSR/readback requires exact IE-only clear; final MSR happens
after sample hash, publication and digest copy. Returning terminal callback receives
result, never proof of PMU sleep or receipt visibility. Callbacks/state remain
exclusive trusted premises, not a security boundary or atomic publication scheme.

Read failure exposes no digest. Publication failure can retain intended-snapshot
digest with visibility unknown. Hash failure is an explicit distinct enum value5;
it is NOT an extension silently written into terminal-record v1. Final MSR mismatch
or failed return overrides capture result to IRQ-unproven, while any internally
computed digest remains associated with intended bytes. Initial IRQ failure skips
capture; callbacks may hang or raise exceptions outside this model's guarantees.

Host tests exercise successful real C collection/hash/publication, initial/after/
final MSR failures, disable failure, initial/final policy drift, read/publication
failure, exact digest correlation and final-observation ordering, nested-use and
repeat rejection. Explicit failing-capture double under ASan/UBSan verifies hash
failure remains distinct and final observation occurs. No physical instructions.

Standalone actual MicroBlaze object frame128, only expected unresolved symbol
pit_capture_digest, no detected subword-store mnemonics. Scoped standalone
lifecycle128 + capture156 + SHA300 =584 bytes excludes caller/callback/exception
paths; actual linked image remains unreviewed. Old lifecycle, root, terminal v1,
working runtime and frozen images unchanged. No main/request hook or runtime entry.

Next safe offline step: specify and implement a distinct terminal composition
adapter consuming this model's internally produced digest and recorded MSR outcomes.
Hash-failure representation must fail closed or use a separately versioned receipt;
do not reuse terminal v1 status5. Test status/digest/session correlation before
binding a new root and doing fresh LTO/store/stack review. Image hash delivery,
exception exclusion, reader no-wake lifetime and recovery remain open; no deployment.

Full PIT Python suite:123 tests PASS.
