# Actual PMU BSP access and barrier probe — offline

Pinned installed BSP inspected, then actual MicroBlaze v9.2 little-endian -Os
compiler recipe used without LTO to expose six isolated probe functions. No
probe function was executed. Source, commands, disassembly, header/object hashes
and six checked function inventories are preserved. No vendor source was edited.

| Path | Source / emitted code | What remains unknown |
|---|---|---|
| Xil_In32 | xil_io.h139: volatile u32 dereference; one lwi | Read fault/hang cannot be represented as callback nonzero return |
| Xil_Out32 | xil_io.h213 normal non-ENABLE_SAFETY branch; one swi, void | Completion, fault recovery and external visibility |
| DATA_SYNC | xil_io.h72 maps to mbar(1); mb_interface.h137; b8220004 | Actual PMU-to-DAP/coherency and transaction response guarantees |
| compiler ordering | both BSP and explicit memory-clobber probes retain lwi/mbar1/lwi | Six small probes are not whole-program/LTO or platform memory-model proof |
| callback return | software wrapper could return 0 after intrinsic returns | Does not catch exceptions or interrupt a hung access |

The BSP macro uses basic volatile inline assembly without an explicit extended
assembly memory clobber. The compiled load-pair probe DOES preserve both loads;
no optimizer bug or unsafe reordering is demonstrated. The explicit-clobber
variant has the same emitted instructions here. Neither result qualifies an
external observer. ENABLE_SAFETY changes the write source branch; that branch
was not selected by this recorded compiler recipe and is not covered.

## Admission decision

Physical adapter remains NOT_READY. Before a physical capture: establish exact
slot placement/ownership (outside active stack/firmware/guard), no epoch reuse,
PMU-local PIT access and fault path, barrier/store visibility to the chosen
consumer, and independent bounded recovery if a load never returns. Then build
a new guard image without prohibited GPO0/vector snapshot code, review its full
link/stack/exception paths and qualify normal restoration under the board lease.
Do not turn raw intrinsic completion into a fabricated bus-error receipt. Do
not use a software deadline to claim preemption of a hung instruction. RO PIT
motion remains neither elapsed time nor destructive DDR admission.

Next safe offline work: source/linked audit of PMU RAM slot ownership and exact
capture/consumer access path, selecting no slot or physical backend until the
layout and lifetime conflict checks pass. No HW/reset/network/register access.
Normal runtime unchanged; DDR NOT_ADMITTED.
