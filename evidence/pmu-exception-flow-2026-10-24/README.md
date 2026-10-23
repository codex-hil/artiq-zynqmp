# Linked PMU exception inventory — 2026-10-24

Exact sleep-guard ELF was physically qualified previously; this audit has no HW
access. Disassembly hash matches the prior sleep-guard offline input manifest.
Software vector0xffdc0008 targets XPfw_Exception0xffdc00bc; hardware vector
0xffdc0020 targets XPfw_Exception_Handler0xffdc89fc. Direct-edge traversal finds
13 function blocks,26 edges,148 memory instructions and two self loops. This is
an overapproximate function inventory, not a complete instruction-level graph.

Hardware handler calls xil_printf0xffdcc810 and XPfw_UtilRMW0xffdc5b60.
Formatting reaches outbyte/number/string/division helpers. At0xffdcc9ec the
linked printf has bra r3: a register-derived jump target that this analysis does
not resolve. Other conditional/unsupported branches are explicitly retained as
unresolved control. No claim that these represent actual ROM calls is made.
Every memory instruction remains address-unproven, including stack accesses.

Software handler and hardware handler terminate in tight self loops at
0xffdc00f0 and0xffdc8a6c respectively, without sleep. Thus the physically read
guard record cannot establish that no later exception path runs. No code change,
exception masking or repeated hardware capture is warranted by this inventory.

Two decoder tests PASS: extended absolute and negative relative target handling,
indirect-control retention, memory marking, denial of DDR admission and rejection
of missing vectors. Actual image inventory generated from retained disassembly.

Next offline: resolve the printf indirect jump table using ELF section/relocation
and register-definition evidence, then classify concrete exception MMIO and stack
addresses with source-to-linked binding. Indirect targets, ROM/reset/NMI behavior,
secondary cores and PS transaction history remain separate open obligations.
DDR NOT_ADMITTED. No fresh normal-runtime health claim.
