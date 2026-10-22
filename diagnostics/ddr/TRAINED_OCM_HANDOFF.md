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

## Trained observer integrated, offline preflight PASS —2026-10-22

Candidate wrapper now accepts `--trained-observer-manifest` as an exclusive
observation mode. It pins observer ELF/FSBL symbols and execution/restoration
scripts, verifies inputs before and under the shared lease, and always runs
normal baseline restoration/debug/Ethernet through the existing lifecycle.
Child requires inherited lease and storage admission, resets once before
PMU/FSBL, waits bounded UART completion, then positively halts CPU0 and checks
its terminal twice. No reset follows training. Standard XSDB download retains
cache synchronization, checks entry PC, runs the64-byte observer and halts for
terminal/register validation. Missing backend register names or any unexpected
state fail; no cache-sync bypass or register-name fallback. No DDR test writes.

Three new model groups and six lifecycle regression groups PASS. Actual artifact
and script-pin preflight PASS without hardware access. No observer hardware
run or trained handoff state is claimed. Evidence/manifests:
`evidence/trained-observer-integration-2026-10-22`. Historical SPD v2 execution
pins deliberately remain unchanged; use the new observer manifest for this mode.

Offline reproducer (omit --execute):
```sh
python3 scripts/test_candidate_runtime_hw.py \
  --manifest evidence/trained-observer-integration-2026-10-22/runtime-inputs.json \
  --trained-observer-manifest evidence/trained-observer-integration-2026-10-22/observer-inputs.json \
  --output /path/to/fresh-preflight
```
Next review script pins and current HW allocation/storage, then one bounded
`--execute --server SERVER --port UART --interface NIC` observation/restoration
window. Backend currentel/DAIF names and live post-FSBL masks remain unqualified;
refusal means retain failure evidence and restore, not force admission.

## First trained-observer HW attempt FAIL; restoration PASS —2026-10-22

Initial storage admission blocked before HW (shared45MiB). Eight own completed
Oct7/8builds relocated to root with29568entries byte/mode/link verified, old
paths retained; three relocation controls PASS. Shared free space749752320B
at admitted window. Evidence: `evidence/older-build-relocation-2026-10-22`.

Bounded shared Genesys lease86.724s: PMU/FSBL and halt reached collector, but
XSDB returned `no register match: currentel`. Attempt FAIL before observer
download; no observer execution or DDR test. No fallback/cache bypass used.
Normal restore/physical TTL/CoreDMA/analyzer/MonInj/Ethernet PASS192.168.2.3;
lease released. No Kasli/Si/SD/flash/OTP writes. Raw evidence and failure retained:
`evidence/trained-observer-hardware-2026-10-22`. Next inspect backend register
definitions and explicitly map live PSTATE/EL fields, test offline then re-pin
before another bounded attempt. Existing hardware entry state remains unproven.

## Backend register definitions and FSBL-only metadata mode —2026-10-22

Read-only XSDB metadata capture under shared Genesys lease PASS, no stop/reset/
download/memory/register writes. Current running-target view exposes AArch32
r0..r12/cpsr/cp15, not currentel. This is not the post-FSBL EL3 view; do not
substitute its names or infer current EL/cache state from metadata. Runtime
left unchanged; no network test needed for this metadata-only observation.
Evidence: `evidence/a53-register-definitions-2026-10-22`.

New explicit definitions_only manifest mode uses existing PMU/FSBL lifecycle,
positively halts CPU0 at selected ELF terminal, reads `rrd -defs`, returns
without observer download/continue and always restores baseline. Four Tcl-model
groups PASS including proof that definitions-only never downloads. New pinned
manifest/preflight prepared; post-FSBL metadata hardware NOT_RUN. Next one
bounded definitions-only window, then review actual PSTATE/system-register
paths and test decoder before re-enabling observer execution. Original FAIL
and admission rules remain intact; no automatic alias guessing or cache bypass.

## FSBL root register metadata hardware PASS —2026-10-22

Definitions-only window85.652s under shared Genesys lease PASS, with normal
restoration/physical TTL/CoreDMA/analyzer/MonInj/Ethernet PASS192.168.2.3.
Post-FSBL stopped terminal exposes r0..r30,sp,pc,cpsr plus sys group. This
differs from the running AArch32 view, but supplies no live EL/cache proof.
No observer download/execution or DDR test; no Kasli/Si/SD/flash/OTP changes.
Evidence: `evidence/fsbl-definitions-hardware-2026-10-22`; original currentel
FAIL retained. Lease released.

Prepared expanded definitions-only capture: `rrd -defs sys` plus raw cpsr.
No field interpretation/alias guessing. Four Tcl model controls PASS, actual
artifact/script-pin preflight PASS. New next-sys-definitions-inputs manifest
is separate from historical proof. Next bounded metadata window, then review
backend system-register paths before observer admission.

## FSBL sys-root/cpsr metadata hardware PASS —2026-10-22

Initial storage admission rejected478MiB before HW. Four completed own route/
Ethernet builds relocated with full inventory verification and original-path
symlinks; no other project/toolchain deletions. Admitted free space798588928B.
Bounded shared lease86.997s: FSBL terminal sys-root metadata/cpsr capture PASS,
normal restore/TTL/CoreDMA/analyzer/MonInj/Ethernet PASS192.168.2.3. Shared lease
released; no observer/DDR test/Kasli/Si/SD/flash/OTP writes.

Backend sys root has numeric children0..15; raw cpsr1610613453 (0x600002cd).
No speculative field decoding or system-register name substitution used.
Evidence/inventories: `evidence/fsbl-sys-definitions-hardware-2026-10-22`.
Next capture definitions of all16advertised sys children in the same bounded
metadata mode; new pins/artifact preflight and four Tcl controls PASS. Unknown
register mapping still blocks observer admission, not normal runtime operation.

## FSBL system-register paths captured; mask gate remains closed —2026-10-22

All16sys child definition groups captured under shared Genesys lease, status
and mandatory normal restoration PASS. Physical TTL/CoreDMA/analyzer/MonInj/
Ethernet PASS192.168.2.3. No observer/DDR test/Kasli/Si/SD/flash/OTP writes.
Paths now evidenced: sys 1 sctlr_el3, sys 0 mpidr_el1; GP registers r0..r30.
CurrentEL/DAIF are not separately named in these definitions. Evidence:
`evidence/fsbl-sys-children-hardware-2026-10-22`. Lease released.

New pure supplied-data PSTATE decoder accepts only valid AArch64 modes. Three
test groups cover all32mode encodings, all16DAIF combinations and malformed
values. Captured debug cpsr0x600002cd decodes EL3h, DAIF0x2c0: A unmasked,
D/I/F masked. The existing all-four-mask observer gate therefore remains closed;
no control writes or weakened gate were applied. No live SCTLR capture yet.
Field reference: ARM-software/u-boot arch/arm/include/asm/system.h, SPSR_EL_*
and SPSR_EXCEPTION_MASK definitions:
https://github.com/ARM-software/u-boot/blob/master/arch/arm/include/asm/system.h
Saved SPSR_EL3 is not substituted for live debug CPSR/PSTATE.

Next implement reviewed explicit backend paths and PSTATE decoding in the
collector, with offline tests; then read-only control-state capture. Resolve
entry exception policy explicitly before any observer execution. Destructive
DDR tests still require cache/master ownership and remain NOT_ADMITTED.

## Post-FSBL live EL3 control observation PASS —2026-10-22

Explicit XSDB paths now used (sys 1 sctlr_el3/sys 0 mpidr_el1, GP rN). Live
cpsr supplies AArch64 EL/DAIF; only EL3t/h accepted before privileged reads.
Separate controls-only path reads two identical states without applying or
waiving execution admission. Nine collector/composition tests and six existing
lifecycle controls PASS; observed unmasked A is returned, execution still rejects.

Hardware shared lease89.255s PASS: CPU0 pc0xfffc0bf8, CurrentEL12,
SCTLR_EL30xc00818 with M/C/I all0; DAIF0x2c0, cpsr0x600002cd,
MPIDR0x80000000. No observer download/execution or DDR test. Mandatory normal
restoration/physical TTL/CoreDMA/analyzer/MonInj/Ethernet PASS192.168.2.3; lease
released. No Kasli device/Si/SD/flash/OTP writes. Evidence:
`evidence/fsbl-controls-hardware-2026-10-22`, pins fsbl-controls-plan-2026-10-22.

Storage gate initially rejected~387MiB before HW. Own completed Oct8Kasli
master build moved byte/mode/link-verified to root, original path retained;
shared free1943453696B at admission. Full inventory retained with evidence.
No installed toolchain/source/other-project cleanup.

Observer remains NOT_ADMITTED because A is unmasked. Next offline design
exception-aware OCM observation with explicit fault reporting and reviewed entry
policy; do not hide pending faults by blindly masking A or weakening the gate.
Other-core/R5/PL/PS-DMA ownership and lower-EL cache proof still pending; this
CPU0 snapshot does not authorize destructive DDR testing.

## Exception-aware EL3 observer built offline —2026-10-22

Separate `diagnostics/ddr/el3_exception_observer` image:2172RX-only bytes
at0xfffc8000, entry0xfffc8800. Sixteen128-byte vector slots record slot inx14
and branch to a common EL3-checking fault terminal. Fault captures CurrentELx16,
ESR_EL3x17,FAR_EL3x18,ELR_EL3x19,SPSR_EL3x20,DAIFx21; x15=0xf3,
PC0xfffc8878. FAR/ESR validity depends on exception class; raw values do not
imply a valid fault address for every exception. No eret/retry/fault clearing.
Normal entry preserves DAIF and captures original fields, successx15=0x33/
PC0xfffc8834. Separate deliberate BRK0x53 entry0xfffc8840 for later controlled
synchronous fault validation; normal entry never reaches it. No data memory/
stack/UART/cache/control writes in the executable.

Debugger loader must install/read back VBAR_EL3=0xfffc8000 while positively
halted BEFORE any continue, recording old VBAR and original PSTATE. This is a
future explicit control-register write, not implemented/admitted here. Changing
VBAR after starting would leave an unsafe exception window. No silent masking A
or reliance on partially overwritten FSBL vectors is allowed. Any fault terminal
must FAIL the observation and force full baseline restoration, never PASS.

Exact payload/layout gate and3tests PASS: all16vector branches reach handler,
vector/opcode/BRK drift rejected, injected masking/store/writable segment rejected.
Initial ELF load extended to0xfffc0000 through linker headers; checker rejected
it. Fresh v2 uses explicit PHDRS and passes exact0xfffc8000..0xfffc887c extent.
Evidence and rejected initial layout: `evidence/el3-exception-observer-build-2026-10-22`.
No hardware access; existing observer/mask admission remains unchanged.
Next implement separately pinned loader policy with VBAR readback/EL3/raw-state
checks and modeled failure paths before any bounded normal/fault-probe HW run.
This does not prove asynchronous SError delivery, master quiescence or DDR integrity.

## Exception-aware observer loader modeled offline —2026-10-22

New library `load_el3_exception_observer.tcl` requires parent's shared lease,
selected/halted CPU0, pinned ELF and FSBL terminal. No automatic connect/reset.
Two identical raw states required: EL3h, M/C/I clear, D/I/F already masked,
CPU0 affinity. A is preserved as observed; this separate policy requires verified
exception vectors before continue and does not change old observer admission.
Records oldVBAR/PSTATE, uses normal synchronized download, checks entry PC and
unchanged PSTATE/SCTLR/affinity, writes sys12vbar_el3 and verifies twice.
Any failed readback aborts before continue. No cache-sync bypass, DAIF write,
pending-fault clearing, DDR data access or reset after training.

Normal entry and deliberate BRK entry supported separately. After bounded
execution/positive halt, captures success/fault registers. Fault terminal always
throws EXCEPTION_CAPTURED, including deliberate BRK; parent must retain raw fault
and restore. A future explicit fault-test verifier may qualify the expected BRK
only; this library never reports fault as normal observer success. No eret/reuse.

Four Tcl model groups PASS: normal A-preservation/vector ordering, bad VBAR
readback/no-continue, deliberate exception/fault-register capture/no-normal-PASS,
wrongEL/cache/masks/terminal rejected before download. Evidence:
`evidence/el3-exception-loader-2026-10-22`. Installed XSDB rwr source path/value
semantics reviewed; real VBAR writes/readback/exception behavior NOT_RUN.
Next integrate separately pinned child with existing mandatory-restoration
lifecycle, verify ELF and loader hashes before/under lease, model failure cleanup
and expected-BRK validation before bounded hardware qualification. No HW this
checkpoint; normal runtime remains at last validated192.168.2.3 baseline.

## Exception observer integrated with mandatory restoration —2026-10-22

The existing trained observer parent now accepts a separately pinned manifest
with exception_observer=true. Modes remain mutually exclusive; exact exception
image gate replaces the legacy64-byte image gate only in this new mode. New
loader/checker and inherited-lease helper are mandatory hashed dependencies.
Parent repeats pins under the shared lease, child requires inherited lease and
checks image/storage before UART/reset. Existing bounded lifecycle always
restores the normal runtime and physical debug/Ethernet tests after success,
failure, interrupt or timeout. No exception fault becomes normal observation PASS.

Tcl dispatch installs and reads VBAR before continue without changing DAIF;
normal completion parser requires exact terminal, armed-vector marker and unique
complete register set. Fault marker/wrong entry/missing/duplicate result rejects.
Four new integration groups PASS: complete real Tcl dispatch model, fault decode
and restoration, malformed/duplicate results, real-artifact preflight with
stale/missing pins and mixed-mode rejection. Six lifecycle regressions and five
legacy observer models PASS. Final actual pinned artifact/script preflight PASS.
Hardware, real VBAR write/readback and fault handling remain NOT_RUN. Evidence:
`evidence/el3-exception-integration-2026-10-22`.

Offline command (default, no hardware):
```sh
python3 scripts/test_candidate_runtime_hw.py \
  --manifest evidence/trained-observer-integration-2026-10-22/runtime-inputs.json \
  --trained-observer-manifest evidence/el3-exception-integration-2026-10-22/inputs.json \
  --output /path/to/fresh-output
```
Next review current coordination/storage/server/UART, then one bounded normal
exception-aware observation with --execute/--server/--port/--interface. Full
restoration is mandatory. Deliberate BRK is not exposed by this parent mode;
future separate verifier must qualify a matching deliberate fault without
converting arbitrary exceptions into success. No DDR test/Si/SD/flash/OTP/Kasli
changes in this checkpoint; baseline remains last validated192.168.2.3.

## First exception-aware observer hardware FAIL; restoration PASS —2026-10-22

Shared Genesys lease87.366s. FSBL terminal/EL3/cache checks and synchronized
2172B OCM download passed; VBAR_EL3 write/readback passed before con, A unchanged.
After20ms host delay and checked stop, PC remained0xfffc8800 (entry), registers
did not show normal/fault marker. Execution NOT_ESTABLISHED, candidate FAIL.
Do not infer a cause, successful exception handling or a memory fault from this.
Full normal restoration/physical TTL/CoreDMA/analyzer/MonInj/Ethernet PASS
192.168.2.3; shared lease released. No DDR test/Kasli/Si/SD/flash/OTP writes.
Evidence: `evidence/el3-exception-observer-hardware-2026-10-22`.

Installed XSDB con source invokes resume-mode0; default does not block until
execution/stop. A short host delay is insufficient evidence of actual progress.
Prepared bounded10x100ms backend state trace with exact target identity and
suspended-state presence checks, then positive halt and unchanged terminal/
register verdict. This is diagnostic instrumentation, not a proven fix. Four
loader models plus4integration tests PASS; fresh pinned artifact preflight PASS.
Next one bounded trace window to distinguish resume behavior; preserve original
FAIL. No step/forced PC/cache-sync bypass/extra post-training reset introduced.
