# Standalone stackless assembly candidate — offline 2026-11-01

LGPL-3.0-or-later. Assembled object only, not linked/referenced/executed.
No hardware operation, live exception injection or vector/runtime/frozen change.

Two standalone entries, software route1 and hardware route2, each128 bytes/32
instructions. First instructions capture post-entry MSR/ESR/EAR into r3/r4/r5;
no EDR read (field zero, validity mask7). Uses r8 direct slot base and r9 literal
scratch plus r0. No r1/r2/r13 dependence, loads, C ABI arguments, stack allocation,
function call, library, printf/UART or return. Direct u32 stores build complete
fault-v1 record, two mbar1 barriers, then local infinite branch. MBAR does not
follow IMM or occupy a branch delay slot in reviewed bytes. Completion is not
bounded when data accesses/fences fault or hang; loop is not sleep.

Dedicated NOBITS64-byte slot aligned8. Object has no vector section; each entry
has only its slot R_MICROBLAZE_64 relocation (offset12) and local loop NONE
relocation (offset120). No concrete linked slot address or vector target exists.
Separate exact ELF32 relocatable checker validates section/symbol/relocation
closure and instruction bytes, including route-specific word.64 instruction-word
mutants and relocation/header/vector-section controls reject. Text object.hex is
the small original standalone object fixture, no vendor firmware/code inside.

This is a candidate under assumptions, not proven exception-safe entry. Special
register access/privilege, vector selection, trusted memory/startup, same-context
ownership, nested fault/reentry, debug/NMI/ROM routes, notification policy and
independent recovery remain unqualified. Both entries share one slot and may
interleave without exclusion: no first-fault preservation/atomicity claim. No
session/image binding; fault-v1 nonce stays zero. The production printf handler
remains present and is NOT repaired by this unreferenced object.

Next safe offline step: isolated non-runtime link with only this object and a
bounded explicit code/slot linker map, then verify resolved relocations, slot
bounds/nonoverlap, no vectors/calls/stack, emitted barriers and terminal loop.
Keep it outside production PMU image; do not replace handlers or test live faults.
Policy, exception recovery and safe PMU RAM external-reader lifetime stay open.

Full PIT Python suite:149 tests PASS.
