# Trained DDR to OCM diagnostic contract

This is an offline design, not an executable sequence or permission to write DDR.
Source locations and hashes: `evidence/trained-ddr-handoff-audit-2026-10-22/audit.json`.

Retain Piotr's SPD-driven training and AMD PMU/FSBL. Do not substitute the current
cold OCM loader: its system reset and peripheral-only initialization do not
preserve a trained DDR handoff. Do not reuse the existing OCM entry unchanged:
it writes data/BSS before its EL3 setup and enables EL3 data/instruction caches
with `0x1006`. Its historical EL1 cache report is insufficient for this path.

## First implementation: observation only

1. Produce a separate stackless AArch64 EL3 entry in OCM. Before data/BSS setup,
   check CurrentEL and record SCTLR_EL3, SCR_EL3, SCTLR_EL2, SCTLR_EL1, HCR_EL2,
   DAIF, MPIDR, entry PC and SP. Unexpected EL must terminate without accessing
   higher-level registers. Do not touch DDR or enable caches. An initially
   unproven MMU/cache state must not be silently normalized before reporting.
2. Reuse FSBL's completed DDR training, then stop CPU0 with positively checked
   suspended state. UART `Exit from FSBL` occurs before assembly exit; validate
   PC against the selected ELF's exit loop and inspect live EL/control state.
   Do not reset CPU0 or the system between training and this observation.
3. Both FSBL and the observer occupy OCM. Prove terminal halt before overwriting
   any FSBL bytes; after download, use checked explicit entry selection. Retain
   debugger cache synchronization; failures must abort, not trigger a bypass.
4. Confirm other A53/R5 target states; record PL configuration/isolation and
   PS DMA/peripheral ownership. FSBL can remove PL isolation if DONE is set.
   Neither a lack of new PL programming nor a halted A53 proves DMA quiescence.
5. Observe UART/state only, then run the existing mandatory normal restoration
   and physical TTL/DMA/debug/Ethernet validation under the same shared lease.

The initial observer must not write test patterns. A later destructive runner
needs a separately reviewed cache-maintenance policy and positive master
quiescence checks. PMU firmware remains active and must be included in that
review. Source-level calls/comments do not prove live state or bus inactivity.

## Later sparse test

Use `plan_ddr_alias_probes.py` only after all admission conditions are established.
Keep low/high windows disjoint. Write distinct tags to all sparse locations,
barrier, then verify all locations; repeat complemented tags. Bound progress and
abort on the first failure. This does not replace full-window and sustained tests.
