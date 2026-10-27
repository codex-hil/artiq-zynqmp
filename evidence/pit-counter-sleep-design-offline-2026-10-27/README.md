# Counter-before-sleep profile design — offline lifecycle model

22 PIT tests PASS including new actual C optimized+ASan/UBSan lifecycle fixture:
15 scenarios (success; initial MSR/disable/final MSR errors; IE mismatch; each
of eight read failures; first write/barrier failure), invalid entry, reentrant
and duplicate rejection. Ops are copied before callbacks. Exact order is
MSR-before, disable, MSR-after check, collection/publication, terminal callback.
MSR failure/mismatch prevents all counter reads; read failure prevents all writes
and barriers. Every admitted returning path reaches terminal exactly once.

A terminal callback in this OFFLINE MODEL returns to the test. It is NOT a
physical sleep backend, nonreturning guard, halt proof or external visibility
proof. A callback which never returns prevents terminal entry: no timeout or
recovery claim. EE/exception policy and ROM/RAM vector mapping remain unqualified.
No GPO0/preload/control reads or MMIO intrinsics occur in this component.

MicroBlaze non-LTO object compilation PASS: text408/data0/bss0, frame84 excludes
pit_capture/callbacks/caller, unresolved pit_capture. No final profile ELF was
built and no physical entry/symbol addresses are admitted. Do not add frame84
to an unrelated LTO link and claim a total bound. Prior full audit ELFs contain
the prohibited historical vector guard and remain MUST NOT DEPLOY.

## Future physical binding requirements

Design-only JSON pins current source, deliberately leaves physical entry and
request/record/terminal addresses null, and sets deployable/backend/admission
false. It is not accepted as a hardware manifest. A new physical profile needs
fresh source generation WITHOUT vector-v1/GPO0 code, explicit BSS slot and
one-shot boot/session identity, a linked nonreturning sleep loop, exact source/
ELF/helper hashes and symbol-derived addresses. Source profile name or a prior
layout probe alone is insufficient. Existing old hardcoded Tcl offsets must
never be copied into that profile.

Counter capture must precede terminal sleep. A returning error must still reach
a safe terminal without publishing success; publication failure may leave a
committed record and must preserve UNKNOWN/no retry. Actual MMIO fault/hang
recovery and PMU-to-AP0 visibility across sleep remain unresolved prerequisites.
No programming/UART/JTAG/network/reset/hardware action occurred.

Next safe offline work: standalone GPO0-free target guard source generation and
linked nonreturning terminal/callback ordering audit, with deployment refusal
until concrete adapter and recovery/visibility obligations are met. No physical
attempt is justified by this model. DDR NOT_ADMITTED.
