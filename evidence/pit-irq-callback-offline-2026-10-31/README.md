# IRQ callback candidates — offline, 2026-10-31

LGPL-3.0-or-later. Standalone compilation only, no hardware operations.

`pit_irq_audit.c` adds two separately opted-in MicroBlaze callback candidates.
Both reject non-NULL context before touching MSR. The observer rejects NULL or
non-word-aligned output, then reads MSR once and stores one volatile u32.
The disable callback invokes the maintained AMD interrupt-only helper once.
Empty volatile assembly with memory clobbers brackets each operation: compiler
ordering only, not a CPU/bus fence. These are returning callback candidates;
the lifecycle's separate readback must check the expected IE-only transition.

Reviewed actual non-LTO object: observer 11 instructions/44 bytes, no stack;
disable 15 instructions/60 bytes, 8-byte frame, one relocation to
microblaze_disable_interrupts. The separately recompiled helper has five
instructions: mfs/andi(-3)/mts/rtsd/nop, clearing IE mask 0x2. It does not
clear exception-enable 0x100. The canonical MSR-instruction macro is undefined
for this compile; no msrclr claim. See build.json and archived disassemblies.

Host doubles test invalid inputs without touching MSR/helper, output preservation,
read/clear/read values, repeated clear, and missing target/opt-in rejection.
They do not execute or qualify MicroBlaze instructions. Standalone compilation
uses actual BSP/tool flags but is not LTO/linked-image proof. The helper may be
interrupted before its write; synchronous exceptions, NMI, ROM/error paths,
whole-path stack and no-wake lifetime remain unqualified. Zero return only
reports that the instruction/helper returned. No exception/bus fault recovery.

The callbacks are NOT bound into any existing root, manifest or frozen image.
Next safe step: a separate audit-only root binding these callbacks, then fresh
small C/LTO link and inspection of actual callback/helper targets, frames and
instruction/store behavior. Preserve all previous frozen profiles. No main/request
hook, external PMU RAM reader, deployment or physical IRQ claim is admitted.
