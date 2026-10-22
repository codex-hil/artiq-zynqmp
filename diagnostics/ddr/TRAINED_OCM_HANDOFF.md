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

## Register-only EL3 observer built offline —2026-10-22

Separate `diagnostics/ddr/el3_observer` image builds with Arm GNU13.2.Rel1.
Exactly64RX bytes at0xfffc0000; no stack/data/BSS, memory loads/stores, UART,
cache operations or control-register writes. CurrentEL checked before EL3 reads.
At terminal PC0xfffc0034, x0=CurrentEL, x1=SCTLR_EL3, x2=SCR_EL3,
x3=SCTLR_EL2, x4=SCTLR_EL1, x5=HCR_EL2, x6=DAIF, x7=MPIDR_EL1,
x8=entrySP, x9=entryPC, x15=0x33. WrongEL branches to0xfffc003c with
x15=0xee; other captured fields invalid. Interrupt state is observed, unchanged;
loader must establish masked entry before execution. Unexpected faults are not
handled by this tiny observer and must fail the bounded parent lifecycle.

The contract's initial UART observation is narrowed to debugger register reads:
this avoids UART/MMIO/data-mapping assumptions and records values without memory
writes. Exact instruction-word gate validates all16instructions/branches and
single RX segment. Three tests PASS: accepted image, injected store rejection,
layout/permission/entry mutations rejected. Evidence:
`evidence/el3-register-observer-build-2026-10-22`. Static proof only, HW NOT_RUN.
Next implement bounded trained-FSBL terminal-PC/EL/cache admission and read-only
observer loading/capture with mandatory normal restoration. No DDR test admitted.

## FSBL terminal entry validation offline —2026-10-22

`check_fsbl_observer_entry.py` binds a unique XFsbl_Loop symbol to actual
AArch64 ELF executable bytes (exact WFE/back-branch). Real diagnostic FSBL
terminal0xfffc0bf4/0xfffc0bf8 verified offline; hash retained in descriptor.
Supplied-capture validation requires two identical CPU0/cable/suspended samples,
EL3, masked DAIF and SCTLR_EL3 M/C/I clear. It rejects wrong image, state drift,
wrong EL/target, cache/MMU enabled, missing masks and malformed fields. Three
test methods PASS (synthetic observations); no physical observations supplied.
Evidence: `evidence/fsbl-observer-entry-2026-10-22`. No hardware accessed.
This checker does not establish provenance, lease, other-master inactivity or
DDR write authorization. Next implement bounded XSDB collection/observer load
inside the existing mandatory-restoration lifecycle; do not reset after training.

## XSDB entry collector library offline PASS —2026-10-22

`collect_fsbl_entry.tcl` reads two identical snapshots of uniquely current,
halted Genesys CPU0 at the selected FSBL terminal. Checks CurrentEL before
EL3 register reads, cache/MMU/masks/core-affinity before returning. No connect,
stop, reset, target-selection, download or continue operation is in this library.
Parent must provide the shared lease and positive terminal halt. XSDB2025.2
source confirms `rrd -nvlist` name/hex-value dictionary format; actual backend
register availability remains untested and missing names fail closed.
Three Tcl-host test groups PASS including nine rejected states and wrong-EL
privileged-read exclusion. Evidence: `evidence/fsbl-entry-collector-2026-10-22`.
No hardware access or baseline changes. Next compose this library with trained
FSBL boot/checked halt and observer download in mandatory-restoration lifecycle;
this component alone neither loads the observer nor authorizes DDR writes.
