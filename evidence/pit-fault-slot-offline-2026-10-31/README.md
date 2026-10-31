# Owned fault slot candidate — offline 2026-10-31

LGPL-3.0-or-later. No hardware operation, vector change or runtime deployment.

Separate target-opt-in C candidate owns64-byte aligned BSS slot and4-byte one-shot
state, validates zero slot, consumes once even if formatting fails, stages supplied
snapshots, then direct commit0/mbar1/15 payload-word stores/mbar1/commit1. No callback
dispatch in target writer; only direct formatter call. Returns after stores: not
exception entry/fail-stop/sleep/visibility/recovery proof. State flag is not atomic
NMI/exception exclusion; valid disjoint aligned input and C stack remain premises.

Host tests compile a temporary explicit fence-double copy, leaving target source
unchanged. O2 and ASan/UBSan validate both barrier positions/commit remains0,
successful slot bytes, one-shot rejection, consumed format failure and nonzero-slot
refusal. These do not execute mbar or special-register instructions.

Actual standalone MicroBlaze object: writer252 bytes/frame100, slot64 bytes and
state4, expected pit_fault_format relocation only; two mbar1 instructions, no
indirect calls or detected subword-store mnemonics. Final linker slot addresses,
whole stack/exception entry and complete writer-linked paths remain unqualified.

Important failed full audit link: PMU_RAM overflow272 bytes; stack range
ffdde7ec..ffddf7ef overlaps fixed service table ffddf6e0..ffddfadf. This candidate
is NOT a valid linked image. failed-link.log/json preserve evidence. No stack
reduction, table move, linker relaxation, RAM write or workaround was performed.
Previous valid/frozen images remain untouched. Existing exception printf path is
still unqualified and this candidate does not replace its vector.

Next safe offline step: construct a separate minimal audit-link source closure,
remove unrelated retained audit roots/dead diagnostic profiles, preserve normal
vendor dependencies/stack/service-table boundaries, and recheck actual RAM layout.
If capacity cannot be recovered without changing requirements, report that limit
rather than shrinking stack or moving reserved tables. No hardware admission.

Full PIT Python suite:143 tests PASS. Full target link remains FAILED.
