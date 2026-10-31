# Stackless audit exception entry proposal — not implemented/admitted

SPDX-License-Identifier: LGPL-3.0-or-later

Scope: standalone assembly-entry candidate for a separate future audit image.
No vector replacement, exception-policy change, hardware trial or promise of
recovery. Current production handlers and image/frozen artifacts remain intact.
The existing C fault-slot writer has132-byte linked frame and returns: it cannot
serve as entry when incoming C stack/ABI validity is unknown.

## Evidence and architecture boundaries

Local xpfw_start.S directly branches from software vector to assembly handler,
which writes ESR/EAR/error MMIO then loops. Hardware vector branches to a C handler
that uses stack and printf. That shows existing source paths, not that stackless
replacement preserves all production notification semantics or is safe on a fault.

AMD UG984 defines R1 as stack pointer and R2/R13 as small-data anchors; ordinary
C callees save/use registers through ABI conventions. A stackless candidate must
avoid relying on those values. [Register Usage Conventions,2024.1](https://docs.amd.com/r/2024.1-English/ug984-vivado-microblaze-ref/Register-Usage-Conventions).

Hardware exception entry changes execution state and transfers to its vector;
R17/return semantics vary with cause and delay-slot circumstances. Captured MSR
is the value read AFTER entry, not reconstructed pre-fault policy. This design
never returns and must not interpret R17 as a universally correct fault PC.
[Hardware Exceptions,2024.1](https://docs.amd.com/r/2024.1-English/ug984-vivado-microblaze-ref/Hardware-Exceptions).

MBAR waits on prior memory transactions; it is not a bounded recovery operation.
It must not immediately follow IMM or occupy a branch delay slot. Review actual
expanded instructions, not just assembly source. Sleep/wake behavior is separate;
no sleep instruction is proposed. [mbar,2024.1](https://docs.amd.com/r/2024.1-English/ug984-vivado-microblaze-ref/mbar).

These general MicroBlaze references do not establish all fixed PMU configuration,
ROM/debug/NMI/routing or fault semantics. Preserve those as explicit unknowns.

## Candidate interface, clobbers and inputs

Propose separately named software/hardware entry symbols with literal route1/2,
no argument pointers, return address or function-call ABI. Initial instruction
sequence should read selected special registers into dedicated scratch registers
before reusing them. No attempt to save/restore interrupted GPRs or resume code.
No claim of an atomic multi-register snapshot if another event intervenes.

Proposed reserved working set:

| Register | Candidate role |
|---|---|
| r3 | entry MSR snapshot |
| r4 | ESR snapshot |
| r5 | EAR snapshot |
| r6 | optional EDR, only if route/config access is separately qualified |
| r8 | direct linker-owned fault-slot address |
| r9 | literal word/route/commit scratch |

No read or write of r1, r2, r13; no use of ABI arguments, saved return registers,
normal stack, GOT/SDA-relative addressing or arbitrary context. Do not use r18
explicitly; review assembler expansion/relocations for unexpected clobbers. Since
there is no return, interrupted scratch-register preservation is not promised.
Unsupported special-register reads must be omitted with zero invalid field/mask;
never execute an unqualified read merely to fill the four-field format.

## Storage and control flow

Use a dedicated linker-owned64-byte aligned slot belonging only to this future
entry profile. Existing C writer cannot simultaneously own/use the same slot.
Linker BSS initialization and single-session ownership must be established before
entry; static ELF zero bytes do not prove startup ran. No stack-based temporary,
C helper, printf/UART, allocator, callback or library clear/copy is allowed.

Allowed outline (requirements, not executable implementation): special-register
snapshots; direct absolute linker relocation for slot; commit0; mbar1; direct u32
payload/header/reserved-zero stores; mbar1; commit1; nonreturn local loop. No pointer
loads or callback dispatch. Every payload/reserved word must be initialized before
commit. No stores narrower than u32. No incoming-SP-derived address. Each branch
and its delay slot must be inspected in linked bytes; no branch to other firmware.

A loop is fail-stop intent, not sleep or PMU RAM external-reader permission.
A missing/partial receipt is expected on capture/store/fence faults. A second
exception or other writer may overwrite/interleave: neither a plain flag nor this
outline proves exclusion. No status can be interpreted as successful recovery,
PIT sample or normal terminal receipt. Session nonce remains zero in fault-v1.

## Policy and admission limits

Production error-notification writes currently differ between software/hardware
routes. They are not copied or removed by this contract. Any separate audit-image
policy change must state those effects explicitly before vector binding. A
standalone unreferenced candidate can be assembled/inspected without replacing
handlers. Do not disable exception reporting to avoid the printf byte-store gap.

Before hardware consideration: verify target-specific special-register access,
entry privilege/mode/vector selection, trusted owned RAM availability, BSS/session
lifetime, reentry/nested fault behavior, notification policy and independent
recovery. No routine can guarantee receipt completion when its instruction/data
path is itself faulty or a pending access never completes. PMU RAM external APB
access still needs independently qualified sleep/no-wake lifetime.

Next safe offline step: assemble an isolated, unreferenced no-stack/no-call
candidate using only qualified snapshot subset and reserved zero fields; inspect
clobbers, relocations, direct u32 stores, fences/delay slots and infinite terminal
loop. No vector section, link-hook, HW access or injection is implied.
