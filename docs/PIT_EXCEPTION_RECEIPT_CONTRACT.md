# Audit-only exception receipt proposal — not implemented or admitted

SPDX-License-Identifier: LGPL-3.0-or-later

The current linked hardware-exception path calls xil_printf, whose actual PMU
stack path contains byte stores. The normal-path word-store/stack checks do not
qualify it. This proposal defines a separate diagnostic format and constraints;
it does not replace a vector, disable exceptions or authorize executing a fault.
Existing firmware, vector policy, frozen images and terminal-v1 format stay intact.

## Meaning and separation

An exception receipt means only that a separate audited handler reached its commit
store after capturing selected register snapshots. It is never sample success,
normal terminal status, proof of sleep, bus visibility, no-wake lifetime, completed
recovery or permission for an external APB PMU RAM read. A handler may stop before
any store or hang on an instruction. No host timeout can preempt that instruction.

Use distinct owned storage, magic and schema from sample and normal terminal
mailboxes. Reject a fault receipt wherever a normal terminal receipt is expected.
Keep the PMU RAM arbitration rule: externally reading even this diagnostic memory
requires independently established safe sleep/lifetime conditions. A permanent
busy loop is fail-stop software intent, not safe external-memory visibility.

## Proposed fixed words (version1, 64 bytes)

All fields are little-endian u32, 16 naturally aligned words; no C padding or
64-bit store assumptions. Storage must be isolated and allocated by linker symbols.

| Word | Meaning |
|---|---|
| 0 | commit: initially0, final1 |
| 1 | magic: 0x50465831 (PFX1 as numerical identifier) |
| 2 | schema:1 |
| 3 | route:1 software exception,2 hardware exception |
| 4 | validity mask: bit0 MSR,1 ESR,2 EAR,3 EDR; other bits0 |
| 5 | captured MSR if valid, otherwise0 |
| 6 | captured ESR if valid, otherwise0 |
| 7 | captured EAR if valid, otherwise0 |
| 8 | captured EDR if valid, otherwise0 |
| 9 | reserved0 |
| 10 | session nonce low,0 in this unbound proposal |
| 11 | session nonce high,0 in this unbound proposal |
| 12–15 | reserved0 |

Version1 intentionally has no session binding: nonce words MUST be zero, and
readers MUST NOT associate the receipt with a requested nonce/image or sample.
A future binding requires a separately audited entry protocol/version, including
safe lifetime/access to session state during exception handling. No pointer to an
arbitrary plan, callback state or stack should be dereferenced by this proposal.
Never invent zeros as valid special-register values when reads did not occur.
Validity bits describe supplied snapshots, not automatic hardware provenance.

## Writer and entry obligations

A future independent handler candidate must use only reviewed native u32 stores
into a dedicated linker-owned64-byte slot. Capture special registers before using
registers that could destroy needed values; determine architecturally permitted
reads for each route. Do not use printf/UART, allocators, libc initialization,
function-pointer dispatch, arbitrary input pointers, locks or normal callbacks.
No calls into the existing PMU firmware error-notification/RMW path are implied.

Entry from an exception cannot assume a valid C stack, ABI argument registers,
caller frame, spare stack headroom or reentrancy exclusion. A C helper producing
this format from supplied words can test formatting only; it is not an entry stub.
An actual entry stub needs separate assembly/prologue/clobber analysis, including
whether trusted dedicated stack/slot access can be established without touching
corrupt state. No initial MSR assumption or IRQ-only clear excludes NMI/debug/ROM.

Writer order: invalidate commit0; reviewed fence; write words1..15; reviewed fence;
commit1. Any interrupted/recursive/partial publication is visibility-unknown. The
single-writer/non-reentry assumption must be justified before slot reuse or an
external consumer is considered. No rollback, retry, overwrite or reset of another
writer's slot. A bare software reentrancy flag is not hardware exception exclusion.

After writing, never return to the failed PIT operation. Terminal behavior must
be separately reviewed. A tight loop may avoid return but does not establish PMU
sleep. Reusing sleep instructions or IRQ policy without wake/exception analysis
could lose the receipt or resume execution; neither is authorized by this design.
Preserve production error policy unless an explicitly isolated audit image is
reviewed. Do not remove exception reporting simply to make word-store checks pass.

## Offline validation and remaining gate

First implement a pure host formatter/parser for the supplied-word contract,
checking exact length, magic/version/route/mask, zero invalid/reserved/nonce words,
and commit. Test truncation, wrong type/word range, malformed masks, partial commit
and explicit rejection as normal terminal metadata. Synthetic inputs must remain
labeled; no fabricated physical exception claims.

Then a separate portable word-oriented candidate can be compiled/checked without
binding vectors. Before any handler link or hardware trial, establish target entry
stack/register safety, non-reentry/fault behavior, owned slot bounds/fences and
preserved notification policy. Actual linked paths, exceptional stack and recovery
must be qualified separately. No live exception injection, vector replacement,
external RAM read or destructive DDR admission is granted by this proposal.
