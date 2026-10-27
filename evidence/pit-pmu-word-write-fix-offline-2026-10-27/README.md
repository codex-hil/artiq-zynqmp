# PMU word-write restriction and bounded recovery feasibility — offline

Local official UG1085 v2.5 Chapter6 PMU RAM printed p113: RAM supports word
writes, not byte writes; external accesses must also be word-aligned/32-bit.
Earlier separately linked collector/publisher copies contained sbi instructions
(including local stack copies). Old standalone publisher is now rejected at
ffdcf37c by the new ELF opcode checker. Those old audit bytes are preserved.
IMPORTANT distinction: the previous FULL inlined profile already had no
subword stores after LTO. An initial negative assertion against that full image
failed because it was already word-only; this was not a checker miss. Do not
claim the full image had the standalone component's byte stores.

Collector now zeroes/copies through volatile u32 stores; publisher stages through
volatile u32 and reads samples as volatile u32. This prevents byte-copy
optimization across separate linking contexts while preserving callback ABI.
30 PIT tests PASS including optimized+ASan/UBSan suites; sb/sh/sbi/shi negatives
and sw/swi positives. New full LTO entry has no subword stores, footprint PASS,
frame164 unchanged. This opcode check alone does not prove all access alignment,
callback/library/exception behavior. Remaining memset initializes48 stack bytes
at SP+28; aligned-stack/library word path requires explicit linked review.

Previous source pins now intentionally stale. Previous scoped flow checker is
also compiler-shape-specific (two memset calls/different callback registers),
so it must be requalified before making a new source/artifact audit manifest.
Do not blindly rehash it. No deployment gate or physical backend was enabled.

## Recovery feasibility decision

Host timeout bounds tool waiting, not a stuck PMU load or board recovery. Current
restore script depends on stop -> suspended -> r0 read -> download. Its passes
and historical register-read failure do not establish independent recovery for
a hung local MMIO read. A timer cannot preempt its own hung load. No qualified
independent reset/power path was identified. No watchdog/ATB/reset-policy writes.
UG1085 distinguishes SRST retaining much local/global/power state from full POR.
GPO0[9] also affects sleep reset in fault-tolerance recovery; write-only GPO0
cannot be read to infer policy. Do not modify it to make diagnostics pass.
PMU-to-AP0 visibility and actual sleep entry remain separately unqualified.

No HW/JTAG/UART/network/reset/register access; MUST NOT DEPLOY, DDR NOT_ADMITTED.
Next safe offline work: changed-shape linked-flow controls and aligned-word
initialization/stack path review, preserving recovery/visibility blockers.
