# Proposed fault receipt contract — offline 2026-10-31

LGPL-3.0-or-later. No hardware operation, handler implementation/vector binding,
fault injection, image/runtime or frozen-profile modification.

Contract docs/PIT_EXCEPTION_RECEIPT_CONTRACT.md proposes a distinct16-u32/64-byte
record with commit/magic/version/route, validity mask and MSR/ESR/EAR/EDR snapshots.
Reserved/session words must be zero: this version intentionally establishes NO
session/image binding. Distinct magic/length prevents treating it as terminal-v1;
normal terminal acceptance still needs its own independent parser/consumer rules.
Host supplied-word encoder/strict decoder is a reference, not physical acquisition.

Tests cover both routes/all16 validity masks with valid zero/nonzero snapshots,
malformed commit/magic/version/route/mask, all invalid/reserved/session words,
length/type and u32 range/type rejection. Decoder returns explicit false hardware,
deployment/session/sleep/recovery/PMU-RAM-access claims. Synthetic example labeled
in synthetic-vector.json; no live event or special-register observation fabricated.

Writer/entry requirements explicitly separate future pure formatting from assembly
exception entry: cannot assume C stack/ABI/reentrancy, no printf/UART/libc/callbacks,
owned word-only storage and reviewed fences, no return to failed operation. Fail-
stop looping is not PMU sleep; an exception commit never grants external APB access.
Normal exception reporting/production vector policy must not be removed to pass
store checks. Existing linked printf byte-store gap remains unresolved.

Next safe offline step: standalone portable u32-only formatter/writer candidate
using supplied snapshots, with rejection/output/torn-publication controls and real
target object store/stack review. No target special-register entry, vector hook,
exception injection or hardware trial follows from host format tests. Entry,
reentrancy, notification policy, sleep lifetime and recovery remain open.

Full PIT Python suite:140 tests PASS.
