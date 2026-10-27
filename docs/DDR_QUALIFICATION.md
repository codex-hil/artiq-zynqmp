# DDR qualification plan

Current admission and remaining gaps are summarized in
[DDR admission status](../diagnostics/ddr/ADMISSION_STATUS.md). Earlier sections
below retain their dated checkpoints; their NOT_RUN statements describe those
checkpoints, not a replacement for the current evidence table. Full DDR writes
remain NOT_ADMITTED.

Current physical evidence covers a128KiB application-owned scratch test with
four address-derived patterns and cache clean/invalidate, plus real runtime/
kernel/DMA workloads. That is not a complete capacity or sustained DDR test.

The source-reconstructed SDT contains two adjacent tuples for low DDR that merge
to `[0,0x80000000)`, and a high bank `[0x800000000,0x880000000)`:4GiB configured
in total, separated by a large non-DDR address gap. These windows must never be
flattened into one contiguous destructive sweep. They describe the exported
configuration, not fitted SODIMM capacity or successful address decoding.
Piotr's FSBL dynamically initializes DDR from SPD; preserve that path.

## Offline map inventory

```sh
python3 scripts/plan_ddr_diagnostic.py \
  --pcw /path/to/source-sdt/pcw.dtsi \
  --manifest evidence/kernel-health-build-2026-10-22/candidate-inputs.json \
  --output /path/to/fresh-ddr-inventory.json
```

The tool hashes the selected ELF artifacts, extracts their load/memory ranges
and reports configured DDR intervals. The retained output is
`evidence/ddr-map-audit-2026-10-22/inventory.json`. It explicitly refuses to label
the plan executable or authorize destructive testing. File-backed ELF bytes are
only part of runtime occupancy: BSS/heaps, mailbox/upload buffers, DMA trace
storage and active AXI/peripheral masters matter too. Subtracting ELF segments
alone does not make the remainder safe while ARTIQ runs.

## Dedicated diagnostic sequence

1. Establish the actual installed geometry and controller mapping under the
   shared Genesys lease, using documented read-only observations. No assumption
   of4GiB physical memory based only on SDT.
2. Use the existing OCM startup/linker infrastructure in `diagnostics/a53` as the
   basis for a separate diagnostic. Verify all load segments, stack, exception
   vectors and page tables are outside tested DDR. The current `ocm` feature
   deliberately does not test DDR; it is not a full-range tester already.
3. Reuse Piotr/AMD DDR training, then park other cores and prevent PL/peripheral
   DDR traffic through a reviewed exclusive load/restoration flow. Do not run
   a destructive test alongside the normal kernel worker or Ethernet runtime.
4. Verify execution level, MMU/cache policy and external-memory observations.
   Use a small uncached/address-derived test first, then bounded chunk sweeps,
   complement/address-line/cross-bank alias tests and a separate sustained test.
5. Publish UART progress, tested intervals, patterns, iteration count and exact
   first failure; bound elapsed time and restore/validate the full baseline.

No SPD/controller capture, new diagnostic image or full DDR hardware test was
performed at this checkpoint. The existing runtime is unchanged. Next work is
an offline bounded capture/geometry decoder and a review of the OCM diagnostic's
EL/cache assumptions before choosing writable test intervals.

## Read-only controller capture prepared

`capture_ddr_config.py` is offline by default. `--execute --server SERVER`
acquires the shared Genesys lease and runs the fixed, cable-selected DAP Tcl
snapshot under a45-second bound. It does not stop CPUs or reset/write registers.
Its14allowlisted MSTR/ECCCFG0/ADDRMAP addresses were checked against the retained
AMD `psu_init.h`; no error/status-clear or control writes are included.
`decode_ddr_config.py` reports programmed rank mask, device width, bus-width
proportion and ECC mode while preserving raw ADDRMAP words. It explicitly does
not reconstruct capacity from those words or authorize a memory sweep.
Two decoder and two capture-admission tests PASS. Capture hardware is NOT_RUN.

The OCM assembly audit found that direct EL1 entry does not initialize SCTLR_EL1.
Skipping DDR-based MMU setup is not proof of disabled MMU/cache: a dedicated
tester must explicitly establish and report its execution/cache state under a
reviewed bootstrap. No existing diagnostic was changed or executed here.
Evidence: `evidence/ddr-config-preparation-2026-10-22/`.

## Live controller configuration capture —2026-10-22

The14-register snapshot completed under the Genesys lease, using the uniquely
selected PSU/DAP target. MSTR=`0x81040010`: DDR4, active rank mask1(one rank),
x16 devices, full bus-width proportion. ECCCFG0 reports mode0. All12ADDRMAP
words are retained in `evidence/ddrc-snapshot-2026-10-22/`. The lock was released
and nonblocking reacquisition verified. No CPU stop, reset, DDR writes, runtime
replacement, Kasli/Si/SD/flash/OTP actions or extra network tests occurred.

These are live programmed values rather than static SDT assumptions. They do
not by themselves prove installed density, the complete CPU physical mapping,
correct high-bank decoding or error-free storage. Physical capacity remains
NOT_ESTABLISHED. Next decode the ADDRMAP fields against Piotr/AMD's dynamic
mapping algorithm and obtain independent geometry evidence before choosing full
DDR test limits. The restored normal runtime was left in place.

## Captured ADDRMAP inversion —2026-10-22

`decode_ddr_addrmap.py` implements a limited inverse of Piotr/AMD's dynamic
address-map packing. It accepts the captured DDR4/single-rank/full-width mode
with individually mapped row2..10, and rejects unsupported modes, bit collisions,
noncontiguous DRAM bit indices and HIF holes. No controller changes are made.

The captured map decodes to16row bits,10column bits,2bank bits and1bank-group
bit. HIF bits0..28 are unique and continuous. Full-width mode is64bits under
FSBL's `6-log2(BusWidth)` encoding, so the programmed geometry is4GiB. HIF3
selects bank-group0; bits11/12 select bank0/1; bits13..28 select row0..15.
This is consistent with the SDT's total configured capacity. It does not verify
SPD capacity, CPU high-bank remapping, absence of physical aliasing or integrity.

```sh
python3 scripts/decode_ddr_addrmap.py \
  --snapshot evidence/ddrc-snapshot-2026-10-22/snapshot.log \
  --output /path/to/fresh-geometry.json
```

Evidence and source-function references: `evidence/ddr-addrmap-2026-10-22/`.
Three ADDRMAP tests and two controller decoder tests PASS. A disabled highest row
is tested as a valid smaller map, while an internal missing row is rejected.
The decoder never marks destructive testing as allowed. Next obtain independent
SPD geometry and explicitly establish OCM execution/cache state before any test.

## SPD decoder and OCM layout gates

`decode_ddr4_spd.py` decodes a captured DDR4 base block only for symmetric
monolithic UDIMM/SODIMM, one/two ranks and supported width/density codes. It
cross-checks density-derived bytes against row/column/bank geometry and reports
CRC NOT_VERIFIED. It does not read EEPROM or authorize testing. Two synthetic
controls PASS, including parity with the original AMD rank-size C function.
No physical SPD dump has been acquired; unsupported stacked packages are rejected.

`check_ocm_image.py` checks all ELF load/memory segments, AArch64 executable entry,
vector alignment, BSS and this diagnostic's16KiB-stack symbol convention. The
retained OCM ELF PASS: entry0xfffc0388, stack0xfffc5000..0xfffc9000, no DDR loads.
Two boundary controls PASS. Evidence: `evidence/spd-ocm-preparation-2026-10-22/`.
This is static layout, not proof of live MMU/cache/EL state or other-master quiescence.

Next add explicit EL1 control-register reporting to the OCM diagnostic and verify
that image offline before a bounded exclusive boot/restoration run. Retain the
separate SPD acquisition/CRC gap; static layout and programmed4GiB are not a
license to start a destructive full-range sweep.

## OCM control-register reporting image

The OCM-only diagnostic now reads EL1 SCTLR/TCR/TTBR0/TTBR1/MAIR/VBAR plus
SP and PC after startup. It prints raw values and SCTLR M/C/I bits; it does not
change those registers or access DDR. Unexpected execution level reports
NOT_RUN. The new AArch64 image builds and passes the OCM ELF/vector/BSS/stack
layout gate. Evidence: `evidence/ocm-environment-build-2026-10-22/`.

`decode_ocm_environment.py` validates one EL1 report, all8register fields and
live PC/vector placement in executable OCM file extents plus the checked stack.
Two synthetic decoder tests and two ELF boundary tests PASS. Neither a decoded
report nor disabled local MMU/cache enables destructive DDR testing. No physical
run or live register observation has occurred at this checkpoint.

Next prepare an exclusive OCM load/UART capture/restoration wrapper. It must
preserve the DDR training dependency and restore the documented normal runtime,
while preventing any claim that the new image has already tested DDR.

## Exclusive OCM observation wrapper prepared

The existing candidate lifecycle now supports `--ocm-manifest`. It verifies the
OCM ELF/symbol hashes and layout, exact qualified PS setup and pinned loader/UART
scripts, both before and after acquiring the shared Genesys lease. OCM mode
excludes kernel/fault/extended-runtime suites. It runs the OCM-only image and
captures UART/control-register observations, then always executes the normal
baseline restore plus physical TTL/DMA/debug/Ethernet checks before releasing
the lease. Timeouts/interrupts retain the existing bounded-child/restoration flow.

The separate loader requires the exact cable and strict A53 core stops. It
reuses the old OCM peripheral initialization flow, explicitly excluding DDR init;
this is a volatile diagnostic load, not a full-range DDR test. The child requires
an inherited lease, verifies the layout before UART access, retains partial logs,
and requires the explicit DDR NOT_RUN marker. Artifact/loader manifest:
`evidence/ocm-observation-plan-2026-10-22/inputs.json`.

Two OCM-specific admission/loader-failure controls plus6existing lifecycle
controls and actual artifact preflight PASS. Hardware execution is NOT_RUN.
Next use one bounded `--execute` window with the verified server/UART/interface,
preserve the measured EL1/cache results and validate restoration. MMU/cache bits
remain observations, never an automatic authorization to write DDR.

### First bounded OCM attempt —2026-10-22

Hardware attempt FAIL before OCM download: XSDB `stop` returned
`The core is held in power-on-reset` while visiting the A53 cores. No OCM
register observation or DDR test occurred. Existing lifecycle restoration PASS:
normal runtime192.168.2.3, physical RTIO/debug and Ethernet checks PASS. Shared
Genesys lease covered the complete71.827s window. Evidence:
`evidence/ocm-observation-hardware-2026-10-22`.

Next inspect target state semantics and explicitly distinguish cores held in
power-on-reset from running/stopped cores. Do not broadly ignore stop errors.
Re-pin any changed loader and test the state admission before another bounded
OCM attempt. No Kasli/Si/card/flash/OTP writes in this window.

### Reset-aware OCM admission prepared offline —2026-10-22

Installed XSDB2025.2 `stop` implementation always sends RunControl suspend; its
documented error return includes already stopped/cannot stop. `targets` exposes
`suspended`. Loader now accepts an already suspended core, otherwise stops and
requires a fresh suspended state. Initial core parking additionally accepts only
two identical exact backend `The core is held in power-on-reset` errors on the
same selected target. No reset is released for that exception. CPU0 after its
processor reset must be suspended; POR cannot admit it. Other errors propagate.
This observes a point in time, not a guarantee against independent reset agents.

Eight modeled scenarios in2tests PASS;2OCM admission/restore controls and6existing
lifecycle tests PASS. No hardware access for this revision. Original failed
manifest/evidence preserved; revised pinned manifest:
`evidence/ocm-observation-plan-v2-2026-10-22/inputs.json`. Next one bounded
observation with full normal restoration. Live MMU/cache and DDR qualification
remain NOT_RUN; no automatic destructive DDR authorization.

### Second bounded OCM attempt —2026-10-22

Reset-state admission physically PASS: two cores stopped, two exact POR errors
confirmed twice; CPU0 suspended after processor reset. Download FAIL at
0xfffc0000: `Cannot flush CPU cache. Cannot read register hcr. Cannot set
privileged PE mode`. OCM program did not execute; partial-write extent is not
established. No UART MMU/cache observation or DDR test. Full normal restoration,
physical RTIO/debug and Ethernet PASS192.168.2.3 under72.713s exclusive lease.
Evidence: `evidence/ocm-observation-v2-hardware-2026-10-22`.

Installed XSDB `dow` supports `-bypass-cache-sync`, but it was not used: bypass
without proving the execution/cache state would undermine this diagnostic.
Next offline review processor-only reset versus existing qualified system-reset/
alternate-JTAG flow and explicit AArch64/exception-level initialization. Existing
`reset_genesys_ps.tcl` documents SD BootROM races and the need for alternate JTAG
before system reset. Do not assume that explains this failure without evidence.
No automatic force-memory/cache-sync bypass or destructive DDR test.

### System-reset OCM variant prepared offline —2026-10-22

Review found normal qualified loading performs a PS system reset in alternate
JTAG mode before PMU/FSBL, whereas failed OCM loading used only processor reset
from an active runtime. The OCM loader now reuses the exact volatile
BOOT_MODE_USER0xff5e0200=0x10e/system-reset/3000ms sequence from
`reset_genesys_ps.tcl`, then repeats checked core parking before generated
peripheral setup. It still skips DDR initialization and does not load FSBL or
PMU firmware. ELF and PS-init artifacts unchanged. No cache-sync bypass, forced
memory access or new SCTLR writes. This is a hypothesis-driven diagnostic
change, not proof of the HCR failure cause.

Two full Tcl reset-flow model tests PASS: correct ordering and no peripheral
init/download after reset failure. Two core-state and two OCM admission tests
PASS. Revised pins/review: `evidence/ocm-observation-plan-v3-2026-10-22`. No HW
access for this revision. Next one exclusive bounded OCM observation, followed
by full normal restoration/debug/Ethernet regardless of candidate outcome.

### Third attempt: debugger source lookup race —2026-10-22

Initial A53 parking FAIL before alternate-JTAG write/system reset. XSDB
`stop`/`wait_for_event` called `process_targets_state`/`get_source_line_info`,
which failed `Execution context is running`. Thus v3 did not test the system
reset hypothesis or reach OCM download. Full normal restore/physical RTIO/debug/
Ethernet PASS192.168.2.3, exclusive lease74.393s. Raw failure preserved in
`evidence/ocm-observation-v3-hardware-2026-10-22`.

Installed XSDB exposes `configparams source-line-view 0`; its
`get_source_line_info` returns immediately when disabled. V4 sets this debugger
presentation option after connect, before parking. No stop errors are ignored;
no cache synchronization, protection or state confirmation disabled. The setting
is local to the short-lived XSDB interpreter. Two reset-flow/two core-state/two
OCM controls PASS, including the exact sole allowed configuration and ordering.
V4 pins: `evidence/ocm-observation-plan-v4-2026-10-22`. V4 hardware NOT_RUN;
next one bounded observation/restoration. Full DDR test still NOT_RUN.

### Fourth attempt: APU L2 held in reset after system reset —2026-10-22

Initial parking and PS system reset completed. Subsequent parking failed
`APU L2 cache is held in reset`. Peripheral initialization, OCM download and
execution were not reached; MMU/cache/DDR test NOT_RUN. Full normal restoration/
physical RTIO/debug/Ethernet PASS192.168.2.3 under74.670s exclusive lease.
Evidence: `evidence/ocm-observation-v4-hardware-2026-10-22`.

Piotr's pinned AMD embeddedsw FSBL `xfsbl_handoff.c` has an explicit A53 power-up
sequence: checked power-island activation, execution-state handling, ACPU clocks,
then CPU0/L2/power-on reset release. The selected generated `psu_resetout` block
only fixes PCIe defaults; `init_peripheral` only writes the SMMU interrupt mask.
They do not replace APU power-up. Source revision/hashes/masks retained in
`apu-source-review.json`. Next offline review the complete supported debug/
power-up/AArch64 flow before implementing the OCM path. Do not simply suppress
L2 reset errors or write reset masks without the power/clock/entry requirements.
No new reset-release code or cache/protection bypass added in this checkpoint.

### Native debugger activation ordering prepared offline —2026-10-22

Closer review corrects the earlier FSBL shorthand: the reviewed
`XFsbl_SetCpuPwrSettings` power/clock/reset sequence is inside its
`XFSBL_CPU_SWRST` branch. `XFsbl_PowerUpIsland` polls without a local timeout and
returns its initialized success after the status clears. We do not transplant
that loop or manually clear L2/CPU reset masks.

Installed AMD XSDB `rst -processor` supports and forwards `-stop`, `-isa A64`
and `-clear-registers` to its capability-checked XilinxReset service. Its separate
SVF A53 reference resets CPU/L2 with an OCM bootloop and RVBAR before stopping;
this reference does not prove the active hw_server implementation.

V5 removes A53 suspension between system reset and PSU/DAP clock/peripheral
setup. It then calls native `rst -processor -stop -isa A64 -clear-registers`,
requires CPU0 suspended, checks secondary cores, reselects/rechecks CPU0 and
only then downloads. No manual power/reset implementation, DDR-init, cache bypass
or forced access added. A model now rejects suspension queries while still in
the post-system/pre-processor-reset state. Two reset-flow/two core-admission/two
OCM tests PASS; v5 preflight and source hashes retained in
`evidence/ocm-observation-plan-v5-2026-10-22`. Hardware behavior NOT_RUN. Next one
bounded attempt with full restoration; native activation may still fail and that
failure must be retained, not waived.

### Fifth attempt: CPU0 activation PASS, secondary reset admission FAIL —2026-10-22

PS reset, PSU initialization and native CPU0 reset `-stop -isa A64
-clear-registers` completed; CPU0 suspension confirmed. Secondary CPU1 stop
returned exact `The core is held in reset`, outside v5's POR-only allowance.
Download/execution/MMU-cache observation/DDR test NOT_RUN. Full normal restore,
physical RTIO/debug and Ethernet PASS192.168.2.3 under77.911s lease. Evidence:
`evidence/ocm-observation-v5-hardware-2026-10-22`.

V6 admits either exact core-reset error only after two identical responses on
the same selected target. CPU0 post-reset still requires suspended; APU L2 reset
is rejected, as are changing state/transport errors/missing state. Two core-state
controls (expanded scenarios), two reset-flow and two OCM tests PASS; new pins:
`evidence/ocm-observation-plan-v6-2026-10-22`. No new HW attempt for v6. This
change releases no secondary resets and does not disable cache synchronization.
Next bounded OCM load/observation with mandatory normal restoration.

### Sixth attempt: unconfirmed initial stop —2026-10-22

Initial parking failed: `stop` returned but the following target properties did
not confirm suspension. System reset/OCM load/execution/MMU-cache/DDR test
NOT_RUN. V6 logs do not identify the failing core, so no core number is inferred.
Full normal restore/physical RTIO/debug/Ethernet PASS192.168.2.3 under71.912s
lease. Evidence: `evidence/ocm-observation-v6-hardware-2026-10-22`.

Installed XSDB `wait_for_event` exits its timed loop without raising timeout;
`stop` therefore cannot itself prove a halt. V7 logs selected target name/id and
polls positive suspension up to21observations/20x50ms after successful stop,
then dumps final properties and fails. Missing state fails immediately; no stop
retry and no acceptance of an unconfirmed halt. This permits bounded state
propagation but does not claim stale state caused v6. Existing outer timeout
remains120s. Two core-state tests include delayed confirmation and bounded
non-suspension; two reset-flow/two OCM tests PASS. V7 artifact preflight/pins:
`evidence/ocm-observation-plan-v7-2026-10-22`. Next bounded observation/restoration.

### OCM observation physically PASS —2026-10-22

V7 reached OCM entry, ran at EL1 and completed UART capture. SCTLR_EL1=0xc52838:
M/C/I bits all0 (MMU, EL1 D-cache and I-cache disabled). PC0xfffc09ac and
SP0xfffc8d70 fit the checked OCM executable/stack ranges; VBAR0xfffc0000.
UART PING/PONG, timer polling and one timer IRQ(id30,other0) reported PASS.
CPU1 held reset; CPU2/3 held power-on-reset, each confirmed via identical exact
backend errors twice. This run required no delayed post-stop polls.

DDR explicitly NOT_RUN; no DDR initialization was requested by this OCM path.
Do not generalize EL1 M/C/I to EL3 cache state or whole-system quiescence. Raw
TTBR/MAIR values retained, not interpreted as valid mappings while M=0.
Normal ARTIQ restored192.168.2.3; physical RTIO/debug and Ethernet PASS.
Exclusive lease covered76.350s. No Kasli/Si/card/flash/OTP writes. Evidence:
`evidence/ocm-observation-v7-hardware-2026-10-22`. Nested decoder flag
`environment.hardware_executed=false` describes the pure decoder; the enclosing
capture's flag is true and raw UART establishes this physical observation.

Next offline define independent DDR geometry/SPD acquisition and a read-only
master/reset-state admission inventory. OCM EL1 state alone does not authorize
destructive DDR writes. Physical capacity/CRC, high-window alias checks and
other-master/cache ownership still require explicit evidence. Preserve this
known working OCM manifest for subsequent diagnostic extensions.

### Independent SPD acquisition preparation —2026-10-22

Qualified build's `app/src/xfsbl_ddr_init.c` is byte-identical to Piotr's port
source (SHAae48bfe6f1c478fd91bb16088d311ea5f8916e1ab43045184a614af868cd60a5).
Read function uses AMD XIicPs I2C1/100kHz, SPD0x51 and page controls0x36/0x37.
Mux0x75 is defined but unused in this function: do not infer a routing write.
Four send results are ignored, receive/idle statuses checked; full512-byte read
leaves the upper page selected, with no base CRC verification. Preserve this
understanding before adapting the reader. No I2C/HW access in this checkpoint.

Acquisition plan requires checked status/deadlines at every step, no scanning/
retry/bus clear, raw repeated captures, explicit page-state handling on all exits
and independent CRC. Reuse maintained AMD XIicPs/BSP. Exact plan, source hash and
remaining master/cache/window/test-interval gates:
`evidence/ddr-spd-acquisition-plan-2026-10-22/source-review-and-plan.json`.
Actual EEPROM acquisition/CRC remain NOT_RUN.

`compare_ddr_geometry.py --spd BYTES --snapshot LOG --output FRESH` compares row,
column, bank/group, ranks, bus width and total bytes against the existing
controller decoder. Mismatch exits nonzero; malformed inputs reject. Even a
match remains CRC/acquisition NOT_VERIFIED and cannot authorize DDR writes.
Three controls PASS (synthetic match, valid smaller/two-rank disagreement,
malformed input), plus two existing SPD/C parity controls PASS. Retained example
is explicitly SYNTHETIC, not a physical SPD dump. Next implement bounded base-SPD
acquisition using AMD code before any hardware attempt.

### Bounded SPD orchestration controls PASS —2026-10-22

New `diagnostics/ddr/spd_reader.h` fixed transaction state machine performs two
base128-byte reads, compares them and attempts one lower-page cleanup only when
transport confirms bus/driver quiescence. Admission requires exclusive ownership
and a known lower-page baseline; current FSBL leaves upper page, so no automatic
post-FSBL admission.100ms/stage plus10000poll limit; busy/unknown bus forbids
cleanup, failure remains explicit. Callback implementation is not yet supplied.

AMD source audit found MasterRecvPolled→MasterPolledRead unbounded receive wait;
therefore do not use those APIs as supposedly bounded callbacks. Future adapter
must use audited nonblocking AMD APIs. No controller rewrite. Host fake-transport
C controls PASS with ASan/UBSan: exact operations, each begin/completion failure,
mismatch, elapsed/poll deadlines and cleanup failure/busy refusal. Evidence:
`evidence/spd-reader-orchestration-2026-10-22`. README includes limitations and
reproducer. No HW/I2C access, no physical SPD/CRC/DDR qualification. Next offline
audit/build/test actual AMD adapter and page-state establishment before deployment.

### AMD nonblocking adapter candidate compiled —2026-10-22

`spd_xiicps.h` now binds orchestration to AMD MasterSend/MasterRecv plus manually
serviced master ISR. Candidate requires ZynqMP/initialized I2C1/non-repeated-start/
seven-bit/idle and exclusive no-GIC caller preconditions. Completion requires
expected event, zero residual bytes and idle bus; errors poison and prohibit
cleanup/reuse. Compile against real BSP AArch64 headers PASS (-Werror), mocked
API controls PASS with ASan/UBSan. Not linked or run on hardware; vendor ISR
not executed by these controls. Evidence: `evidence/spd-amd-adapter-2026-10-22`.

Remaining before hardware: actual AMD ISR/call-graph/register-model checks, page
baseline, controller/IRQ/callback snapshot/restore and bounded executable wrapper.
Adapter bind replaces callback; ownership integer is a caller precondition, not
a hardware GIC proof. Do not rebind after fault before outer restoration. No HW
access in this checkpoint. README contains reproducer and exact limitations.

### Actual AMD receive ISR model: fault guard required —2026-10-22

Host model executes four unmodified extracted AMD functions through the receive
ISR path with actual BSP macros and substituted MMIO. Six controls executed
with ASan/UBSan: no event,128-byte success, partial completion, NACK, hardware
timeout, stuck RXDV. In the last scenario, `MasterRead` attempts a129th read
after a128-byte buffer is exhausted. Model intercepts it before invalid store.
This is injected model evidence, not a physical Genesys defect.

Current adapter remains NOT_ADMITTED: a callback deadline cannot preempt this
ISR loop. Preserve original-negative case. Next minimal patch in isolated copied
AMD source: bound receive count and fail on residual RXDV; test original and
patched behavior. Shared BSP/original sources remain unchanged. No hardware
access or adapter deployment. Evidence:
`evidence/spd-vendor-isr-model-2026-10-22/results.json`. Full driver/send-path
integration, page/IRQ/callback restoration and CRC still open.

### Isolated AMD receive-bounds patch validated offline —2026-10-22

Two-function patch in fresh copied sources: count guard in MasterRead, and
ERROR for exhausted buffer with residual RXDV in master ISR. No shared BSP
changes. Original6-scenario negative proof retained; patched7-scenario model
(stuck RXDV and zero remaining count included) returns ERROR without extra
reads. ASan/UBSan controls PASS; two source-drift/idempotence tests PASS.
Three full C files compile as AArch64 objects against real BSP (-Werror).
No linked firmware, no hardware execution. Evidence/diff/manifests:
`evidence/spd-vendor-bounds-2026-10-22`. Next adapter+patched ISR integration
model, then page/controller/IRQ/callback restoration. SPD acquisition remains
NOT_ADMITTED; no physical DDR qualification follows from model bounds.

### Reader/adapter/actual AMD integration model PASS —2026-10-22

Eight scenarios execute the reader, adapter and11extracted AMD functions with
actual BSP macros and modeled MMIO: correct dual read/cleanup, NACK, partial,
stuck RXDV, no events, hardware timeout, completion+NACK, mismatch. ASan/UBSan
PASS; terminal errors and active timeouts forbid new transactions/cleanup;
valid captures require matching bytes and cleanup. Copy/source hashes verified.
Evidence: `evidence/spd-amd-integration-2026-10-22`.

Not a physical FIFO/timing/IRQ test; lower-page/no-GIC ownership are model
preconditions. No hardware access, source/BSP unchanged. Hardware remains
NOT_ADMITTED pending page identity, controller/GIC/callback state lifecycle, CRC
and bounded physical capture/restoration wrapper. Next offline lifecycle controls.

### Peripheral/driver snapshot restoration model PASS —2026-10-22

New spd_xiicps_state saves full driver/callback and CR/timeout/peripheral mask
only on quiet/empty/zero-status controller with external ownership/no-GIC
assertion. Restore refuses active/poisoned/dirty state before writes; checks
register readback, consumes snapshot/adapter, poisons mismatches. Integrated
model restores original non-null callback/ref, tests seven refused snapshots,
all failed/pending capture states, bad readback and double restore. ASan/UBSan
and real-BSP AArch64 header compile PASS. Evidence:
`evidence/spd-state-lifecycle-2026-10-22`. No HW access. GIC ownership/routing
and SPD page remain unimplemented; no physical admission. Next dedicated EE1004
page query classification/restore with exact protocol event semantics. Current
adapter retains generic NACK poisoning; Linux primary source referenced in README.

### Exact EE1004 page-query classifier/model PASS —2026-10-22

Dedicated pure classifier accepts only0x36/one-byte query with external route/
independent SPD identity evidence, idle/empty bus and exact ACK or address-NACK
events. Eleven uncertain/error variants reject. Saved-page selector/confirmation
logic tested: unknown and mismatched page refuse restoration claim. Actual AMD
MasterRecv+patched ISR generate both page responses in MMIO model; identity is
a fixture assertion, not physical proof. ASan/UBSan and AArch64 test-object
compile PASS. Evidence: `evidence/spd-page-classification-2026-10-22`.

No hardware or generic adapter change. Page writes/restoration are NOT_RUN and
not implemented by this classifier. Next bounded dedicated query lifecycle/
post-select confirmation, source of route/device proof and pending-count cleanup
after protocol NACK; then GIC/CRC before physical admission.

### Bounded dedicated page operation lifecycle model PASS —2026-10-22

New query/select operation has100ms/10000poll bounds, exact protocol response
classification and active/failure reuse refusal. Exact admitted page1 query
retires unused receive count only after idle/empty/clear-status proof and checks
transfer-size0readback; no abort/reset/FIFO clear/retry. Other errors remain
terminal. Selection transmission success requires a later matching query before
page restoration can be claimed. Generic data adapter NACK policy unchanged.

Actual AMD model restores both saved pages via five-operation sequences;8fault
scenarios reject or expose post-select mismatch. Missing identity refusal and
failed-object reuse checks PASS with ASan/UBSan; AArch64 header compile PASS.
Evidence: `evidence/spd-page-lifecycle-2026-10-22`. No HW access. Next compose
page/data/controller lifecycle with all-exit restoration, then identity/GIC/CRC/
linked bounded wrapper before physical admission.

### Composed SPD session/restoration offline PASS —2026-10-22

New spd_session composes controller snapshot, page discovery/selection/query,
dual read, saved-page confirmation and controller/callback restoration. Distinct
READS_RESTORED, FAILED_RESTORED and OUTER_RESTORE_REQUIRED outcomes prevent a
matching payload or successful controller restore from masking a page failure.
Overall3s/200000poll bound, per-stage limits retained; active/faulted operations
are not force-cleaned or reused.

Fourteen actual-AMD/MMIO-model composed cases (both saved pages x7normal/fault
profiles) PASS with ASan/UBSan; AArch64 header compile PASS. Prior component
controls retained. Evidence: `evidence/spd-composed-session-2026-10-22`. No HW
access/shared BSP changes; physical SPD/CRC/DDR tests NOT_RUN. Next CRC and
concrete independent route/device/GIC admission before linked diagnostic/wrapper.

### Base SPD CRC validation/gates offline PASS —2026-10-22

Checker validates supported DDR4 bytes0..125 against little-endian126..127 using
Python standard-library CRC. Unsupported byte0 high-bit profile rejects; no
module-block CRC claim. Decoder/comparison `--require-crc` rejects mismatch.
Legacy no-CRC exploratory mode remains marked NOT_VERIFIED, never physical
acceptance. C transport/restoration status alone does not validate CRC.

Nine test methods PASS, including1024single-bit corruptions, primitive check
vector, late base byte/endian/profile/truncation and required downstream/CLI
rejection. Evidence `evidence/spd-base-crc-2026-10-22` uses only synthetic SPD.
Reference primary i2c-tools source linked in DDR README. Physical SPD/CRC/DDR
NOT_RUN. Next concrete route/device/GIC evidence and linked bounded capture
wrapper; CRC validity alone does not establish identity or fitted capacity.

### Concrete route/IRQ audit; existing FSBL dump built —2026-10-22

Digilent primary manual confirms I2C1/MIO8SCL/MIO9SDA, matching Piotr config.
BSP0xff030000/encodedIRQ4012 plus AMD SPI offset gives IRQ50; proposed live
read-only GIC words recorded, not read here. Linked diagnostic FSBL confirms
dynamic DDR call; source enables SPD-based initialization in SDT flow.

First capture path now instruments existing Piotr FSBL after successful SPD
read: UART-only base128B dump, no new I2C or changed training/page operations.
FSBL/PMU build PASS in fresh output, originals/shared BSP untouched. Three
source/emitter/parser tests PASS, including actual injected C formatting. Parser
requires ordered complete frame, CRC and subsequent FSBL completion. Evidence:
`evidence/fsbl-spd-dump-build-2026-10-22`. Physical dump NOT_RUN. Next bounded
candidate loader window with strict UART parsing/full normal restoration.
Standalone adapter/GIC admission work remains offline and is not required for
this existing FSBL-based acquisition path. No HW access/card/flash writes.

### Physical base SPD/CRC capture; initial window FAIL, recovery PASS —2026-10-22

Diagnostic Piotr FSBL produced128base bytes on physical Genesys under exclusive
lease. CRC stored/computed2e87; SPD reports4GiB,1rank,64-bit bus,x16devices,
16row/10column/2bank/1group bits. Seven fields agree with earlier DDRC capture,
not a new simultaneous register snapshot. Raw UART and pins establish provenance;
pure parser flags remain false by design. Physical acquisition is now observed,
not synthetic; memory alias freedom/high-window mapping/stress still NOT_RUN.

Initial43.309s lifecycle FAIL: shared data disk full, cs_server/PL load and
restoration .Xil creation failed. Preserve FAIL. Relocated only own completed
diagnostic build to root storage after verifying4285entries, retained original
paths via symlink. Separate68.091s exclusive recovery PASS: normal runtime
192.168.2.3, physical RTIO/debug and Ethernet PASS. No diagnostic release
promotion or SD/flash/Si/OTP writes. Evidence:
`evidence/fsbl-spd-capture-hardware-2026-10-22`. Next free-space admission before
any reset, then remaining DDR master/cache/window/interval requirements offline.

### Pre-reset storage admission implemented —2026-10-22

Candidate execution now requires512MiB+1024inodes at output/work/.Xil/shared AMD
home+TMPDIR/hosttmp, before lease and again under it. Direct loader checks before
UART/reset. Real shared filesystem currently FAILs; no new hardware attempted.
Five storage tests/six lifecycle/three SPD wrapper tests PASS. Evidence:
`evidence/hw-storage-admission-2026-10-22`. New diagnostic v2 pins/preflight
retained separately. Check is point-in-time, not reservation/concurrent-growth
protection. Next safe own-build relocation/inventory and offline DDR ownership/
window planning. Normal ARTIQ remains restored192.168.2.3.

### Own completed builds relocated; storage/pins PASS —2026-10-22

Six completed project outputs moved to root storage after22517entries verified
(hash/mode/symlink/source-unchanged checks). Original artifact paths retained
through symlinks; normal and diagnostic manifest artifact/layout preflights PASS.
Three preservation/failure/rollback tests PASS. Available shared space roughly
89→604MiB, current storage gate PASS. No hardware or shared-toolchain changes.
Evidence: `evidence/completed-build-relocation-2026-10-22`. Next bounded full
FSBL-SPD candidate/CRC/runtime/restoration attempt under usual rechecked storage
and hardware lease; original failed lifecycle remains retained.

### Complete diagnostic FSBL SPD/runtime window PASS —2026-10-22

The v2 pinned candidate completed under the shared Genesys lease (138.067s),
with storage admission before reset. Physical SPD base bytes exactly repeat the
first capture: SHA256 ab0343bdadbb16c6dbf91e7066817f67fcaaae28ec03be36c088e5481fb2bf83,
stored/computed CRC 0x2e87, reported 4GiB/one rank/64-bit bus/x16 devices.
Candidate and restored normal runtime both passed physical TTL/CoreDMA, standard
analyzer/MonInj clients, analyzer ring wrap, 20/20 ICMP and five byte-exact TCP
echo connections. Normal runtime restored at192.168.2.3; lease released.
Evidence: `evidence/fsbl-spd-complete-hardware-2026-10-22` (raw logs compressed;
summary records original raw hashes). Earlier disk-full FAIL remains preserved.
This validates the diagnostic FSBL handoff, not full DDR integrity, high-window
alias freedom or a promoted boot release. No Kasli/Si/SD/flash/OTP writes.
Next offline work: define trained-DDR OCM handoff, cache/master ownership and
explicit disjoint low/high test intervals before destructive-test admission.

## Sparse DDR alias plan prepared offline —2026-10-22

`scripts/plan_ddr_alias_probes.py --output /path/to/fresh-plan.json` enumerates
64-byte probes at logical address-bit offsets6..31 plus low/high boundaries.
Logical capacity offsets map explicitly into `[0,0x80000000)` and
`[0x800000000,0x880000000)`; no probe touches the intervening MMIO gap.
Distinct tags must be written across all probes before any verification, then
repeated with complements: an immediate write/read of each location would miss
aliasing. These are sparse logical-address checks, not full DRAM wiring coverage
or an integrity/stress test. Three boundary/bit-coverage/rejection controls PASS.
Evidence: `evidence/ddr-alias-plan-2026-10-22`. No hardware accessed.

Execution remains NOT_ADMITTED. The existing cold OCM loader skips DDR training
and cannot be reused unchanged. Next prepare a trained-DDR OCM handoff with
explicit EL3/EL1 cache policy and other-core/PS-DMA/PL-master ownership evidence.
Physical SPD and controller agreement do not substitute for these conditions.
Normal runtime remains at the last validated192.168.2.3 baseline.

## Trained-DDR handoff source audit —2026-10-22

Pinned generated FSBL handoff/exit/cache sources and OCM startup/loader reviewed.
FSBL disables data cache, exit masks EL3 M/C/I, but UART completion precedes
assembly exit. Current OCM startup re-enables EL3 C/I (0x1006), and cold loader
skips DDR training. Neither can be reused unchanged as the DDR tester. FSBL
also conditionally removes PL isolation when DONE is present: PL master
quiescence cannot be inferred from no new bitstream. No hardware accessed.
Source hashes/line anchors: `evidence/trained-ddr-handoff-audit-2026-10-22`.
Concrete observer-first contract: `diagnostics/ddr/TRAINED_OCM_HANDOFF.md`.
Next implement stackless EL3 entry observation and layout verification, with no
DDR loads/stores; trained handoff and destructive testing remain NOT_RUN.

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

## Exception-aware EL3 normal execution hardware PASS —2026-10-22

Bounded resume-trace window91.308s under shared Genesys lease PASS.
Post-FSBL training preserved; OCM-only2172B observer loaded, VBAR_EL3 written/
read back before continue, original A unmasked retained (DAIF0x2c0). Ten backend
samples suspended=0, then checked halt at0xfffc8834 withx0=12/x9=0xfffc8800/
x15=0x33; complete normal snapshot PASS. Original20ms no-progress FAIL retained;
this does not conclusively explain its root cause.

Live CPU0 SCTLR snapshots: EL3=0xc00818, EL2=0x30c50838, EL1=0xc52838;
M/C/I all0 in each. CPU0-only observation, not other-core cache or DMA-master
quiescence. No DDR pattern access/test. No deliberate BRK or asynchronous
SError delivery tested; vector installation plus normal execution is not fault
handling qualification. Next explicit bounded BRK-test verifier and restoration
controls before physical deliberate-exception validation.

Mandatory normal restoration/physical TTL/CoreDMA/analyzer/MonInj/Ethernet PASS
192.168.2.3; shared lease released. No Kasli/Si/SD/flash/OTP writes. Evidence:
`evidence/el3-resume-trace-hardware-2026-10-22`, raw compressed logs with original
hashes retained. Existing full-DDR/cache/master ownership requirements stay open.

## Deliberate BRK verifier and lifecycle mode offline PASS —2026-10-22

Explicit exception_brk manifest flag requires exception_observer=true, excludes
metadata/control modes, selects --exception-brk and the already checked
exception-aware image. Original normal mode still treats every exception as
failure. Tcl loader raises typed OBSERVER/FAULT_CAPTURED only at fault terminal.
BRK dispatcher accepts that transport outcome only, then Python independently
requires exact complete unique capture: slot4/current-EL-SPx synchronous vector,
x15f3/EL3, ESR0xf2000053 for BRK0x53, ELR0xfffc884c, faultPC0xfffc8878,
armedVBAR0xfffc8000 and saved EL3h/DAIF matching original state. FAR retained
raw without a valid BRK address claim. No retry/eret/faulted-core reuse.

Verifier returns EXPECTED_BRK_CAPTURE_RESTORE_REQUIRED, never normal observation
PASS. Parent may qualify this deliberate test only after mandatory complete
normal restoration/debug/Ethernet; it records observer_probe and observer
manifest SHA separately from runtime artifact manifest. Expected capture cannot
waive restore failure. Unknown exception, untyped Tcl error, wrong syndrome/ELR/
vector/PSTATE or missing/duplicate result remains FAIL. New verifier is pinned.

Four new BRK groups plus4integration regressions PASS, including all wrong-fault
fields, duplicate/normal/incomplete result rejection, actual Tcl dispatch and
failed-restoration refusal;4loader controls PASS. Real artifact/script preflight
PASS, no hardware in this checkpoint. Evidence/manifests:
`evidence/el3-brk-integration-2026-10-22`. Next one bounded deliberate-BRK window
under shared lease with full baseline restoration. This will validate a
synchronous exception path only, not asynchronous SError or DDR integrity.

## Deliberate EL3 BRK hardware and restoration PASS —2026-10-22

Bounded shared Genesys lease88.522s, observer_probe=brk. Exact pinned image,
trained FSBL entry and vector readback checked; original DAIF0x2c0 preserved.
Physical BRK0x53 reached current-EL-SPx synchronous slot4 and fault terminal
0xfffc8878. x15f3/CurrentEL12/ESR0xf2000053/ELR0xfffc884c/SPSR0x600002cd
match verifier. Handler DAIF0x3c0 retained as raw exception-entry state. FAR raw
not interpreted as a BRK memory address. Dedicated result is expected fault,
never normal observer completion. No eret or reuse of faulted core.

Mandatory normal restoration plus physical TTL/CoreDMA/analyzer/MonInj/Ethernet
PASS192.168.2.3; shared lease released. Evidence and both manifest bindings:
`evidence/el3-brk-hardware-2026-10-22`. Pure parser hardware flag stays false;
enclosing raw logs/lease/manifest summary establishes physical provenance.
No DDR patterns/alias/stress test or Kasli/Si/SD/flash/OTP writes. This proves
only the deliberate synchronous exception path, not asynchronous SError.

Next offline inventory of remaining A53/R5 cores, active PMU firmware, PS DMA/
peripheral and PL DDR masters, with pinned source/configuration evidence and
explicit read-only status/reset/ownership checks before any destructive DDR
admission. CPU0 OCM layout/cache/exception evidence does not substitute for
exclusive ownership of the low/high DDR windows.

## DDR-master static inventory and DMA trigger audit —2026-10-22

`audit_ddr_masters.py` reads the single PS module's direct PARAMETERS container
in the selected pinned XSA/HWH, not conditional source Tcl or bus-interface
parameters. It rejects missing/duplicate PS/required nonboolean ports. Optional
preset/QoS entries can omit VALUE without pretending a missing required port is
disabled. Four schema/port controls and actual XSA inventory PASS. No HW access.
Evidence: `evidence/ddr-master-audit-2026-10-22`. XSA5444a2b1... matches earlier
FSBL build input; this alone does not identify the currently restored PL image.

Configured M_AXI_GP0 and S_AXI_GP2 enabled; other inspected GP/ACE/ACP disabled.
Gateware wires GP2/HP0 FPD to RTIO DMA AXIReader. XSA USE_ADMA/GDMA=0 is not
live reset/idle proof. ENET0/SD1/QSPI enabled (plus non-DMA peripherals); every
PS memory-master group remains runtime ownership NOT_PROVEN. A53 secondary/R5
positive parked/reset checks and active PMU firmware audit remain required.

DMA source audit: inflight_cnt counts accepted AR bursts minus accepted final
R beats, internal rather than separate CSR. DMA.enable is CSR trigger; every
write event, INCLUDING ZERO, can start playback. Do not write0 as a stop action.
FSM waits FLUSH/WAIT_EOP/WAIT_CRI_MASTER before IDLE; readable enable.w defaults
zero in IDLE. Next model the complete IDLE/EOP/no-outstanding invariant and
reset/flow-control/error cases before accepting that status as bus-drain proof
or deciding whether additional instrumentation is necessary. No claim that
absence of a dedicated counter CSR makes proof impossible. Bind the eventual
rule to exact loaded source/bitstream and prevent new trigger writers.

Inventory never admits destructive DDR tests. Next offline DMA completion model
and reviewed read-only PS/secondary-core status allowlist. Existing normal
runtime remains at last validated192.168.2.3; no UART/JTAG/network/reset/Si/SD/
flash/OTP/Kasli activity in this checkpoint.

## Actual RTL DMA drain simulation and reset counterexample —2026-10-23

24normal-completion scenarios PASS with exact build-pinned clean Migen44e5627/
ARTIQ1461cf9/MiSoC8a909c8/LiteX8c01073 imports. Independent accepted AR/RLAST
monitor shows zero outstanding bursts at completed status0, peak13;2628R and
12300AR stalled cycles. OKAY/SLVERR, response/CRI delays and trigger0/1 covered.
SLVERR still drains: bus-error status must be checked separately. Finite
simulation, not formal proof or current bitstream/reset qualification.

Negative actual-RTL ResetInserter test CONFIRMS COUNTEREXAMPLE: isolated PL reset
returns IDLE while2accepted PS-side bursts remain outstanding. This does not
claim actual board reset ordering is wrong, but rules out IDLE-alone admission
after unknown reset ownership. Source hashes/revisions/raw per-case metrics:
`evidence/dma-drain-model-2026-10-23`; reproducer/requirements:
`diagnostics/ddr/DMA_DRAIN.md`. No production gateware modifications or HW access.

Next audit actual PS/PL/HP0 reset sequence and make read-only PS-master/core
status allowlist. Preserve trained DDR and establish all reset/transaction
owners before destructive-test admission. Last normal baseline192.168.2.3.

## Reset source audit and32-register ZDMA read plan —2026-10-23

Offline audit pins actual reset/boot/prepare/gateware/generated-FSBL sources.
Bootstrap does PS system reset before PMU/FSBL; FSBL can call generated PL
isolation/removal/reset operations when PL DONE; normal preparation calls PL
reset configuration again after bitstream load. Sys-domain reset derives from
negated PS pl_resetn0. Generated reset helper mentions GPIO Bank5/EMIO; the
complete exported wiring and HP0 transaction-owner reset timing are not yet
proven. Do not equate logical reset/status0 with drained AXI ownership. Existing
bootstrap catch-stop loops are not positive admission of all secondary cores.

`plan_zdma_snapshot.py` verifies all16canonical channel bases and vendor header
offsets/masks; emits32CH_STS/CH_CTRL2 reads only. No ISR/descriptor/interrupt
registers or writes. Decoder requires two exact complete32-bit observations;
busy/paused/error/enabled/reset-like control or changing state is not quiet.
Even all quiet fields stay NOT_OWNERSHIP/destructive_test_allowed=false.
Four source-drift/allowlist/decoder controls PASS, actual BSP plan generated.
Evidence: `evidence/zdma-reset-audit-2026-10-23`.

No HW/JTAG/UART/network/reset operations. Next implement a bounded shared-lease
read-only snapshot wrapper with exact address allowlist and raw provenance, then
review actual PL reset wiring/HP0 semantics and expand CSU/peripheral/core
ownership independently. No complete DDR write-test admission from this plan.
Normal baseline remains last validated192.168.2.3.

## Read-only live ZDMA64-read capture complete —2026-10-23

New wrapper defaults offline, pins register plan/vendor inputs/execution helpers,
rechecks under shared Genesys lease and enforces45s process-group bound. Fixed
Tcl reads only CH_STS/CH_CTRL2 for16channels twice via exact-cable PSU/AP0.
No stop/reset/UART/network/register writes, ISR clears or force-access mode.
Parser requires exact64ordered unique address/name/channel/sample rows within
one complete frame. Timeout retains partial raw log and releases lease.
Five Tcl/parser/stale-pin/timeout controls PASS; actual preflight PASS.
Evidence/pins: `evidence/zdma-capture-plan-2026-10-23`.

Physical capture COMPLETE under shared lease: all16channels CH_STS=0 and
CTRL2=0 in both samples. No hardware configuration change or baseline reset;
lease released. No fresh Ethernet/runtime test was performed or claimed.
Raw64reads and provenance: `evidence/zdma-status-hardware-2026-10-23`.
Enclosing capture marks hardware=true; pure decoder hardware=false intentionally.
Quiet fields do not establish transaction-owner exclusivity, PL HP0 drain,
secondary-core/PMU/CSU/GEM/SD ownership or destructive DDR admission.

Next offline extend reviewed status inventory to CSU DMA and relevant PS
peripheral masters, plus positive secondary/R5 state capture. Bind future
observations to the diagnostic window rather than assuming this running-runtime
snapshot applies after a later reset. No Si/SD/flash/OTP/Kasli changes.

## CSU status and core metadata live capture complete —2026-10-23

Vendor BSP-checked source/destination STS addresses0xffc80008/0xffc80808,
fields busy/outstanding/FIFO/unacknowledged-done, no SIZE/trigger/interrupt
acknowledgement writes. Fixed Tcl performs4STS reads plus six exact-cable
core metadata queries. Leased wrapper defaults offline, pins plan/vendor/helper
sources before and under lease,45s bounded process group, partial timeout log.
Parser requires complete ordered4-row frame and exact six-core metadata rows.
Four decoder/Tcl/strict-parser controls and actual preflight PASS.
Evidence/pins: `evidence/csu-core-plan-2026-10-23`.

Physical read-only capture COMPLETE: source/destination STS0 in both samples,
busy/outstanding/FIFO/done all0. A53#0/#1 metadata Running; A53#2/#3 Power On
Reset. R5#0 label Halted and R5#1 Lock Step Mode, but suspended0; these labels
are NOT positive halted/reset/cache ownership. All core ownership stays unknown.
Raw provenance: `evidence/csu-core-hardware-2026-10-23`. No stop/reset/force
access/UART/network/register writes or error clears. Lease released, baseline
configuration unchanged; no fresh runtime/network requalification claimed.

Next offline RPU lockstep/reset/clock register allowlist and PS peripheral
DMA activity review, then positive observations inside the actual diagnostic
window. Momentary CSU/ZDMA status and debugger labels cannot authorize DDR
destructive writes or establish PL HP0 drain. No Si/SD/flash/OTP/Kasli changes.


### RPU observation plan — 2026-10-23

`scripts/plan_rpu_snapshot.py` validates seven register addresses and relevant
masks against the AMD `rpu.h` and `crl_apb.h` used by the existing PMU build.
Evidence: `evidence/rpu-plan-2026-10-23`. Three unit tests and three mutated-header
rejection controls PASS. This is offline only; no board fields were read.
NCPUHALT, NVALRESET, reset controls and clock enables are reported separately;
none establishes completed AXI drain, R5 cache ownership or destructive DDR
admission. Next implement leased, bounded DAP capture without writes or core stops.


### Live RPU observation — 2026-10-23

`capture_rpu_state.py` defaults offline, validates vendor/plan/helper SHA-256
before and under the shared Genesys lease, then permits only fourteen fixed
DAP reads under a 45-second process-group bound. It never stops or resets cores.
Physical capture COMPLETE, both samples identical: global0x50, configs0x4/0x4,
statuses0x3f/0x38, clock0x03000302, reset0xfc0. Split bit=0; both
NCPUHALT=0/NVALRESET=1, R50/R51/AMBA reset bits=0. These observations do not
show cores held in reset or establish cache/AXI drain. Evidence is in
`evidence/rpu-hardware-2026-10-23`. No baseline change or fresh Ethernet test.
Full DDR writes remain NOT_ADMITTED. Next review other active PS DMA masters
and collect qualifying observations within the eventual diagnostic window.


### PS peripheral observation plan — 2026-10-23

`plan_peripheral_dma_snapshot.py` checks actual BSP base/offset/field definitions
for GEM0 NWCTRL, SD1 present state and QSPI DMA STS. Plan/provenance and three
passing unit groups: `evidence/peripheral-dma-plan-2026-10-23`. Hardware NOT_RUN.
Only32-bit configuration/present-state/DMA-status reads are planned; no FIFO,
interrupt acknowledgement, transfer trigger or reset access. Enable bits do not
prove descriptor drain; QSPI done count is unacknowledged completion count.
No DDR admission or other PS master ownership follows. Next implement bounded
leased capture, then account for GEM rings/buffers in the diagnostic handoff.


### Peripheral hardware snapshot — 2026-10-23

`capture_peripheral_dma_state.py` completed six read-only DAP reads under the
shared Genesys lease, with vendor/plan/helper hashes checked before and inside
the lease and45s process-group limit. Both samples: GEM0 NWCTRL0x1c,
SD1 present-state0x1f70000, QSPI DMA STS0. RX/TX remain enabled; SD transfer/inhibit
bits and QSPI busy/outstanding/FIFO are0. No device writes or baseline changes.
Four offline tests PASS; raw evidence `evidence/peripheral-dma-hardware-2026-10-23`.
Momentary fields are not ownership/drain proof. Next audit active GEM rings/buffers
and diagnostic-window policy; no destructive DDR admission follows this snapshot.


### 2026-10-23 — Qualified runtime GEM memory audit (offline)

Audited the normal CPU0 ELF, SHA29f9a64abeb88ab724ca8e6d372d5f7f0cf51080e3790efbcf1040201e8947c3.
Linked emac_bd_space is [0x800000,0xa00000), TX/RX pbuf pointer tables
[0x600000,0x600800)/[0x600800,0x601000). PBUF_POOL and lwIP heap are also
in low DDR; exact half-open symbol ranges in `evidence/gem-memory-audit-2026-10-23`.
Adjacent AMD source writes q->payload into TX descriptors, allocates RX pbufs
from PBUF_POOL and reserves64KiB per RX/TX descriptor area. Thus descriptor
exclusion alone cannot protect Ethernet payloads. XEmacPs_Stop disables
interrupts and RX/TX but contains no DMA-drain polling. Reset documentation
also warns descriptor lists survive reset. Source hashes/line anchors retained;
this is not a reproducible source-to-binary equivalence proof or live pointer dump.
Two audit test groups PASS (missing/duplicate/overlap/type/address controls).
No hardware access or changes. Destructive DDR remains NOT_ADMITTED.
Next inspect the diagnostic FSBL/PMU boot path to establish whether GEM is
started there at all, then define a boot-window ownership gate instead of
assuming that stopping a running networked CPU stops the Ethernet master.


### 2026-10-23 — Diagnostic FSBL/PMU Ethernet boot-window audit (offline)

Pinned diagnostic FSBL8eb8ddde/PMU9f5c58c5 match existing observer inputs;
ELF symbol inventories have no named XEmacPs/lwIP/netif entry points. Source
JTAG branch returns before DeviceInit and takes stage4/handoff; generated PS
init releases GEM0 reset. PMU includes GEM reset/ROM callback definitions.
These facts do not prove live DMA absence or PMU inactivity. Source hashes and
line anchors: `evidence/fsbl-network-window-2026-10-23`; reproducible audit script
added. `diagnostics/ddr/BOOT_WINDOW_OWNERSHIP.md` defines required in-window
observations, reject/restore policy and still-closed DDR write admission.
No hardware access. Next integrate existing read-only peripheral/master frames
into the trained-observer lifecycle, before network runtime/CPU1 worker startup.


### 2026-10-23 — Same-boot peripheral observation integrated (offline)

Optional peripheral_inputs manifest now binds the existing source-checked
GEM/SD/QSPI read plan and every parser/helper script into observer preflight,
repeated under the parent Genesys lease. Normal exception-aware OCM observer
runs first; its child then reads the three registers twice before any normal
network runtime/CPU1 worker starts. Active RX/TX, SD transfer/inhibit, QSPI
busy/outstanding/FIFO/unknown or unstable samples fail the candidate; parent
restoration lifecycle remains mandatory. No auto-stop/reset/drain workaround.
Fixed child exception handling to replace any earlier PASS with FAIL when a
later observation fails. Necessary quiet fields never authorize DDR writes.
Three new test groups (field/unstable/missing controls, nested pin/mode rejection,
parent restoration) and four exception-observer regression tests PASS. Fresh
manifests and offline preflight: `evidence/boot-peripheral-integration-2026-10-23`.
Historical evidence pins retained; regression test generates temporary current
pins. Hardware NOT_RUN. Next bounded physical observer/read/restore window,
then extend same-window coverage to remaining CSU/ZDMA/RPU/core/PL owners.


### 2026-10-23 — Physical same-boot peripheral observation PASS

93.081s bounded diagnostic/restoration cycle under shared Genesys lease PASS.
Trained FSBL -> exception-aware EL3 OCM observer -> two peripheral samples in
same boot, before network runtime/CPU1 worker. GEM0 NWCTRL0 (RX/TX disabled),
SD1 present-state0x1f70000; decoded transfer/inhibit bits0,
QSPI DMA STS0. All necessary observed fields PASS; DDR test NOT_RUN and admission
stays closed for remaining core/PMU/PL/PCAP/DMA ownership/drain requirements.
Normal runtime restored192.168.2.3, physical TTL/CoreDMA/analyzer ring-wrap/
MonInj and Ethernet tests PASS. Lease released. No Si/SD/flash/OTP/Kasli writes.
Evidence: `evidence/boot-peripheral-hardware-2026-10-23` includes raw logs/hashes,
observer results and restoration qualification. Next extend in-window observation
to existing ZDMA/CSU/RPU/core inventory without admitting DDR writes.


### 2026-10-23 — Same-boot ZDMA/CSU/RPU/core observation integrated (offline)

Extended normal trained exception-observer child with optional master_inputs:
ZDMA64reads, CSU4reads plus six core metadata queries, RPU14reads. Existing
fixed Tcl/parsers are reused, sequentially after peripheral observation and before
normal runtime startup. Parent pins nested manifests, vendor inputs and complete
execution dependencies before and under shared lease. Child rechecks inputs;
nonquiet ZDMA/CSU fields fail candidate and require normal restoration. RPU/core
states stay observations only, never a DDR write admission. No new register writes.
Six boot-window test groups and four observer regression tests PASS; malformed
frames/stale nested pins reject. Fresh execution manifests and test logs in
`evidence/boot-master-integration-2026-10-23`. Hardware NOT_RUN at this checkpoint.
Next physical bounded combined observation/restore/validation cycle; remaining
PMU/PL/PCAP ownership and transaction-drain proof still unresolved.


### 2026-10-23 — Combined same-boot master hardware observations PASS

104.687s full reset/trained-FSBL/EL3-OCM/peripheral/master/restoration cycle PASS
under shared Genesys lease. Sequential same-boot observations: all16 ZDMA
channels STS/CTRL2=0 twice; both CSU STS=0 twice; GEM RX/TXdisabled,
SD transfer/inhibit fields0, QSPI DMA STS0. RPU global0x50, configs0x4/0x4,
statuses0x3f/0x38, clock0x03000302, reset0xfc0, stable. Metadata CPU0suspended1,
CPU1Reset/suspended0, CPU2/3PowerOnReset/suspended0, R50Halted/suspended0,
R51LockStepMode/suspended0. Metadata labels do not establish held-reset/cache
ownership. Positive core/reset and PMU/PL/PCAP/drain requirements still unresolved;
DDR writer NOT_RUN and NOT_ADMITTED. Normal runtime restored192.168.2.3;
physical TTL/CoreDMA/analyzer ring-wrap/MonInj and Ethernet PASS. Lease released.
No Si/SD/flash/OTP/Kasli writes. Raw logs/hashes and physical restoration evidence:
`evidence/boot-master-hardware-2026-10-23`. Next offline audit PMU/core reset
control and PL HP0 reset/ownership, then prepare necessary register observations;
do not repeat unchanged combined capture without new coverage.


### 2026-10-23 — APU reset plan and PMU core-control source audit (offline)

Reviewed PMU pm_proc.c: RPU0 sleep enables AIB isolation, asserts reset,
clears NCPUHALT, deasserts reset, disables isolation. Wake calls ROM R50 reset
handler then sets NCPUHALT. APU wake delegates to ROM. This source sequence is
consistent with observed RPU reset0/NCPUHALT0, but does not prove execution or
exclude future PMU wake. Do not require held-reset as the only possible RPU
idle model, or silently invoke sleep/wake callbacks during observation.
Added source-checked CRF APU reset-control plan at0xfd1a0104: four soft-reset,
four POR bits and L2 reset decoded separately, unknown bits retained. Two decoder
tests and two changed-header controls PASS; actual vendor header validation PASS.
Evidence `evidence/apu-reset-plan-2026-10-23` pins header and PMU source/anchors.
No hardware access. Next integrate two fixed APU reset-control reads into the
same-boot observation, then review PMU request/event paths and PL HP0 drain.
DDR writes remain NOT_ADMITTED; no policy to stop PMU or mutate core resets added.


### 2026-10-23 — APU reset-control same-boot integration (offline)

Added fixed read-only Tcl for two32-bit CRF RST_FPD_APU reads0xfd1a0104,
plus strict ordered-frame parser and vendor-header/plan/helper preflight. Extended
the existing same-boot collector with APU controls after ZDMA/CSU/RPU. Exact
cable/PSU selection, parent shared lease and mandatory restoration remain intact.
Soft/POR/L2 reset controls and unknown bits are observations, not automatic DDR
admission or PMU-release exclusion proof. Fresh complete nested pins in
`evidence/boot-apu-integration-2026-10-23`. Nine offline tests PASS including
real Tcl read-address/count controls, malformed frames, stale pins and restoration.
Hardware NOT_RUN. Next bounded combined hardware capture/restore/qualification,
then PMU request/event authority and PL HP0 reset/drain audit. No DDR writer.


### 2026-10-23 — Same-boot APU reset controls physical PASS

110.194s diagnostic/restore/validation cycle under shared Genesys lease PASS.
CRF RST_FPD_APU0xfd1a0104 read twice0x300e: CPU1/2/3 soft-reset controls1,
CPU2/3 POR controls1, CPU0soft/POR0, CPU1POR0, L2reset0, unknown bits0.
These are stable sampled controls, not proof that PMU cannot later release reset.
Existing same-boot ZDMA/CSU/peripheral necessary fields also PASS; DDR test
NOT_RUN/NOT_ADMITTED. Normal runtime restored192.168.2.3, physical TTL/CoreDMA/
analyzer ring-wrap/MonInj/Ethernet PASS; lease released. No Si/SD/flash/OTP/Kasli
writes. Raw logs/hashes and qualification: `evidence/boot-apu-hardware-2026-10-23`.
Next offline PMU event/request and PL HP0 reset/drain audit; do not repeat this
unchanged hardware cycle. Remaining PMU/PL/PCAP ownership unresolved.


### 2026-10-23 — PMU wake authority routes audited (offline)

Pinned current PMU ELF9f5c58c5 contains PmIpiHandler/PmProcFsm/PmProcWake/
PmMasterWake. Adjacent source routes: PM IPI handler -> PM_REQUEST_WAKEUP ->
permission checks -> PmMasterWakeProc -> PM_PROC_EVENT_WAKE -> processor wake
callback; hardware GPI wake handler is registered for A53/R5 wake events; slave
wake can call PmMasterWake. APU callback delegates to ROM; RPU callback sets
NCPUHALT after ROM reset handler. SLEEP_WHEN_IDLE does not disable PM service.
This is capability evidence, not proof an event occurred or is currently enabled.
Source hashes/line anchors and linked symbol checks reproduced by
`scripts/audit_pmu_wake_routes.py`; evidence `evidence/pmu-wake-audit-2026-10-23`.
Positive anchor/hash and missing-anchor rejection controls PASS. No hardware access.
Cannot close future-wake exclusion from two sampled reset values. Do not stop
PMU or change event masks without a separately reviewed, restorable policy.
Next offline identify non-destructive wake mask/status register observations and
inspect PL HP0 reset/drain coverage. DDR write admission remains closed.


### 2026-10-23 — PMU event observation allowlist (offline)

Source-checked six-register plan: IOMODULE GPI1/GPI2/IRQ_PENDING/IRQ_ENABLE
0xffd40024/28/34/38; LOCAL GPI1_ENABLE/GPI2_ENABLE0xffd60224/228. Two samples,
32-bit reads only. Processor wake signal/enable bits decoded separately; masked
signal is only a current observation. Excludes IRQ_ACK, IPI acknowledgements,
enable/disable writes and event clearing. Actual DAP accessibility NOT_RUN;
no force-access fallback permitted. Vendor headers, source read/ack line anchors
and decoder controls: `evidence/pmu-event-plan-2026-10-23`. Two tests and changed
address rejection PASS. No hardware access. Next integrate fixed leased capture
with existing same-boot lifecycle and test strict frame/timeout behavior offline;
PMU future-wake and DDR ownership remain unresolved. No DDR write admission.


### 2026-10-23 — Same-boot PMU event capture integrated (offline)

Added fixed Tcl12reads (six reviewed PMU registers twice), strict frame parser,
vendor/plan/helper preflight and same-boot collector integration. Exact cable PSU
selection, inherited shared Genesys lease and parent restoration preserved.
No ACK/event/mask writes or force-access fallback. Pending/signal/enable fields
remain observations only; PMU future-wake exclusion and DDR admission unresolved.
Nine offline tests PASS including real Tcl exact read addresses/order/count,
malformed frames, nested pin rejection and parent restoration controls. Complete
fresh nested manifests: `evidence/boot-pmu-integration-2026-10-23`.
Physical DAP accessibility NOT_RUN. Next bounded diagnostic/read/restore cycle;
if access fails, retain error and restore without a force-access retry. No DDR writer.


### 2026-10-23 — PMU AP0 read rejected; normal restoration PASS

Physical combined diagnostic under shared Genesys lease: candidate FAIL at first
PMU read0xffd40024, AXI AP transaction error, DAP status0x30000021. No PMU
sample obtained; no repeated/force-access/read-alias workaround. Known PMU-local
header addresses are not proven AP0-accessible. Do not infer a board defect or
PMU values from this failure. Earlier raw master frames retained but enclosing
combined candidate remains FAIL. Full cycle115.36s; mandatory normal restore,
physical TTL/CoreDMA/analyzer ring-wrap/MonInj/Ethernet PASS at192.168.2.3.
Lease released. No Si/SD/flash/OTP/Kasli writes. DDR test NOT_RUN/NOT_ADMITTED.
Evidence: `evidence/boot-pmu-hardware-2026-10-23`, raw failure and restoration logs.
Next offline inspect PMU-local address visibility and maintained AMD interfaces;
do not repeat the failed AP0 read without a reviewed change. Independent PL HP0
reset/drain source audit remains safe and authorized while PMU access is unresolved.


### 2026-10-23 — Passive PL AXI read observer prototype (simulation only)

Added standalone diagnostic Migen prototype counting accepted AR versus accepted
RLAST, with saturating bounds, sticky accounting/response errors and quiet output
requiring separate external epoch qualification. Newly reset monitor never asserts
quiet without that qualification; zero local count cannot certify prior external
transactions drained. It drives no AXI signals and is NOT integrated into current
bitstream/CSR/reset tree. Three simulation groups PASS: stalls/handshakes, overflow/
unmatched completion/error stickiness and unqualified fresh-reset state.
Evidence `evidence/axi-read-observer-2026-10-23`. No hardware access or FPGA build.
Not an AXI protocol checker: no per-ID or beat-length validation, no end-to-end
PS drain proof. PMU AP0 access remains failed/unresolved; no retry performed.
Next simulate observer alongside actual DMA and independent bus accounting,
including completion/backpressure/reset cases, before any integration/build.
DDR writes remain NOT_ADMITTED; production gateware unchanged.


### 2026-10-23 — Passive observer with actual DMA simulation PASS

Extended existing real-DMA backpressure bench with passive observer and independent
AR/RLAST scoreboard comparison every cycle. All24 combinations of AXI delay0/3/17,
CRI stall0/31, responseOKAY/SLVERR and trigger0/1 PASS. No legal-run accounting
errors; completion drains to zero; SLVERR sets sticky observer response error and
prevents quiet even after drain. Negative isolated-DMA-reset test also PASS:
DMA IDLE does not clear the independently running observer's outstanding count,
which stays nonzero with quiet0 when PS responses are withheld. Production DMA
source/gateware unchanged. Evidence summary/pins:
`evidence/axi-read-observer-dma-2026-10-23/results.json`.
No hardware access or FPGA build; PMU AP0 access remains unresolved.
Next define observer CSR/reset epoch wiring and verify monitor-reset loss of
history against an independent owner model before planning a Dell build.
DDR writes remain NOT_ADMITTED; simulation quiet is not physical drain proof.


### 2026-10-23 — Observer reset-history test and status CSR prototype PASS

Added two read-only CSRStatus objects: outstanding and flags(accounting_error,
response_error,quiet,epoch_qualified). Qualification deliberately tied0; no host
arm/clear CSR, no allocated addresses, no production wiring/FPGA build.
Independent PS-side scoreboard retains accepted bursts while ResetInserter resets
the monitor: localcount0 does not certify drain, quiet/epoch remain0. Late RLAST
sets accounting error. Two simulation/CSR/RTL inspection test groups PASS.
Initial testbench manual count expected one request while ARVALID stayed high
for two cycles; replaced it with an independent per-handshake scoreboard.
Evidence `evidence/axi-observer-reset-csr-2026-10-23`. No hardware access.
Next integrate status-only observer into optional diagnostic gateware, preserving
normal CSR ABI; review reset/clock scope and generate HDL offline before a Dell
build. No epoch qualification mechanism or DDR write admission implemented.


### 2026-10-23 — Optional diagnostic DMA observer integration, HDL PASS

Added --dma-observer only for local-rtio-dma. Default Top/LocalRTIO constructors
retain prior behavior. Optional read-only bank6 exports outstanding0xa0003000
and flags0xa0003004; existing register map including analyzer unchanged by test.
Epoch qualification tied0, no arm/clear write CSR. Monitor shares sys clock/reset
with local RTIO: reset history loss remains explicit, not PS drain proof.
Two optional integration/map/invalid-mode tests PASS; existing physical-interface
AXI->CSR->RTIO/TTL simulation regression PASS. Standalone LocalRTIO Verilog
elaboration PASS; no full PS top or Vivado run/hardware programming.
Evidence/map/artifact hashes: `evidence/local-dma-observer-2026-10-23`.
Next inspect full generated PS-top HDL and explicit source bundle, then build
optional diagnostic on Dell under shared build lease. Do not replace normal
runtime or infer DDR admission from this instrumentation. PMU AP0 unresolved.


### 2026-10-23 — Full observer PS/PL HDL generated; Dell build queued

Extended build_rtio_debug.sh with validated DMA_OBSERVER=0/1 environment option;
default0 unchanged. Generation pins LocalRTIO/DMA and both observer modules,
including tracked source patch identity. Full PS/top HDL plus CSR/init/Tcl/IP
files generated without Vivado;42first-stage CDC registers, standalone CSR map
byte-content equivalence PASS. Used verified PS export and explicitly selected
prior normalized XCI SHA1712fe0fe3f57bddb295133cf851956939ceda3391a96e160d3687004a2f304d.
Dell hostname verified; job artiq-dma-observer-20261023 submitted with transferred
file hashes verified. State WAITING_FOR_BUILD_LOCK; no preemption. Evidence
`evidence/dma-observer-full-build-2026-10-23`. No build PASS or new bitstream claim.
No hardware access. Next collect same remote job, inspect timing/DRC/IP hashes,
then design bounded optional diagnostic probe/restoration before board use.
DDR write admission stays closed; observer epoch qualification remains0.


### 2026-10-23 — Dell observer implementation PASS; hardware NOT_RUN

Same session-held job finished exit0; retrieved files match remote SHA-256.
Strict input/IP/timing/DRC/route checker PASS. Setup1.728ns, hold0.003ns,
pulse2.5ns; internal no_clock/unconstrained endpoints0. Existing external I/O
coverage limitations no_input_delay1/no_output_delay5 remain; DRC only reviewed
RTSTAT-10 warning. BitSHA9649c982dc8353fc6f9b83f5397707143ff1dc4526fc104292aa1512cc2cafca.
Evidence/reports: `evidence/dma-observer-build-pass-2026-10-23`.
Staged candidate inventory combines this optional diagnostic PL/map with known
normal baseline firmware. Inventory is NOT executable yet: current parent hardcodes
prior release build-input binding. Next add explicit hash-bound build receipt and
read-only observer before/after runtime qualification, negative preflight tests,
then bounded physical candidate/restore cycle. Do not bypass current gate by
replacing the prior-release evidence manifest. No board access; normal runtime
unchanged. No DDR write admission, epoch qualification tied0.


### 2026-10-23 — Optional observer runtime hardware PASS / baseline restored

Integrated explicit observer-build input hash and source-helper pins into existing
candidate parent; strict build input/timing/DRC checks rerun before and under lease.
Observer candidate excludes boot/OCM/fault modes; four-read probes before/after
normal debug/Ethernet tests validate stable zero count/error-free fields with
quiet/epoch0. Two offline actual-build/stale-pin/restoration test groups PASS.
Physical full candidate+normal-restore cycle152.61s under shared Genesys lease
PASS. Diagnostic bit9649c982 loaded with known baseline firmware: before/after
samples outstanding0,flags0. Physical TTL/CoreDMA/analyzer ring-wrap/MonInj/
Ethernet PASS on candidate, then normal bit/runtime restored and same tests PASS,
IP192.168.2.3. Lease released. No Si/SD/flash/OTP/Kasli writes.
Evidence: `evidence/dma-observer-runtime-hardware-2026-10-23`; pinned manifest/tests
`evidence/dma-observer-runtime-integration-2026-10-23`.
Idle samples do not prove the observer counted real in-flight bursts physically;
next prepare bounded active-workload observation to capture nonzero outstanding
and return to zero, or safely bound sampling without a claim if too fast. Epoch
qualification remains0; PMU access/ownership and DDR write admission unresolved.
Do not leave diagnostic image as normal baseline; restoration completed.


### 2026-10-23 — Physical active observer detected bursts; workload FAIL/restored

One bounded active cycle under shared Genesys lease167.043s. Candidate loaded,
initial outstanding0/flags0. Workload phase1 observed, complete128pair sample
frame:128nonzero count samples, peak27, all flags0. This is physical positive
active-accounting observation, not conservation/drain proof. Workload then exited
with host protocol error KernelStartupFailed(expected KernelFinished), phase2
missing. Entire candidate FAIL; no successful final idle/drain qualification.
No blind retry or increased stress. Raw workload/sampling logs and separately
decoded sampling in `evidence/dma-observer-active-hardware-2026-10-23`.
Mandatory normal runtime restoration PASS192.168.2.3; physical TTL/CoreDMA/
analyzer ring-wrap/MonInj/Ethernet PASS. Lease released. No Si/SD/flash/OTP/Kasli
writes. Root cause of long-workload kernel/protocol failure NOT_PROVEN.
Next offline inspect worker/protocol failure paths and workload timing/return
handling; preserve decoded sampling if later workload completion fails. No repeat
hardware before a specific reviewed change. DDR write admission stays closed.


### 2026-10-23 — Physical active observer/workload/final-zero cycle PASS

Single shorter-workload cycle156.565s under shared Genesys lease PASS.
Workload128traces completed phase1+phase2/exit0 in8.536s. Sampling interval
0.403..6.460s stayed fully within workload:128/128nonzero counts, peak27,
all flags0. Initial/final pairs outstanding0/flags0. Physical active-accounting
and sampled return-to-zero demonstrated, not full AXI conservation or historical
PS drain proof; epoch qualification remains0. Shortened workload resolves observed
failure in this run without increasing firmware30s command timeout; previous
failed long-workload evidence retained. Candidate TTL/CoreDMA/analyzer ring-wrap/
MonInj/Ethernet PASS, then normal bit/runtime restored192.168.2.3 and same tests
PASS. Lease released. No Si/SD/flash/OTP/Kasli writes. Evidence
`evidence/dma-observer-short-hardware-2026-10-23` includes overlap timings and
raw samples/workload/restore qualification. No further unchanged active retries.
Next offline consolidate precise DDR admission gaps: PMU/private register access,
PL/PS reset epoch and PCAP ownership; use this observer as diagnostic evidence,
not an automatic write-test permit. DDR writer still NOT_RUN/NOT_ADMITTED.


### 2026-10-23 — AMD PCAP status and PMU option review (offline)

Existing AMD XFpga_PcapStatus returns Xil_In32(CSU_PCAP_STATUS); maintained driver
waits separately on WR_IDLE/RD_IDLE. Source-checked status plan0xffca3010 decodes
read/write idle, PL_INIT/PL_DONE independently, retains other status bits; no
PROGRAM/RDWR/RESET/CTRL writes or configuration readback. Two decoder tests and
changed-address rejection PASS. Actual header/source hashes and anchors in
`evidence/pcap-status-plan-2026-10-23`. Hardware NOT_RUN.
PMU maintained ENABLE_PM_VAL option gates PM module registration; disabled path
ModPmInit is empty. This would remove those PM IPI/event handlers, not prove
whole-PMU inactivity: other modules/ROM, FSBL PM setup dependencies, DDR callbacks
and wake/reset effects must be reviewed before any diagnostic image. No option
changed or image built. Next integrate bounded PCAP status observation into a
trained-boot profile that explicitly excludes the known failed private-PMU AP0
probe; keep PMU ownership unresolved, never suppress its failure as a PASS.
DDR write admission remains closed. No hardware access.


### 2026-10-23 — PCAP trained-boot profile integrated (offline)

Added source-pinned PCAP parser/preflight and fixed two-read AP0 Tcl0xffca3010.
Collector now accepts only two explicit inventories: historical private-PMU
attempt, or ZDMA/CSU/RPU/APU/PCAP without failed private-PMU probe. New profile
reports not_observed=['pmu'] and pmu_ownership=NOT_PROVEN; no suppress-as-PASS.
Necessary PCAP read/write-idle fields participate in candidate rejection, not
DDR admission. Nine offline tests PASS including real Tcl two-addressed reads,
missing/malformed frames, nested pins and mandatory restoration. Fresh manifest
`evidence/boot-pcap-integration-2026-10-23`. No hardware access.
Next single bounded trained-boot PCAP capture/normal-restore/validation; retain
PMU access failure and unresolved ownership. No PCAP reset/program/status writes.
DDR write admission remains closed.


### 2026-10-23 — PCAP read complete, idle criterion FAIL; restored PASS

Bounded trained-boot profile cycle114.904s under shared Genesys lease.
Two physical PCAP status reads0xffca3010 identical0xa0000a46: read_idle1,
write_idle0,PL_INIT1,PL_DONE0. AP0 access succeeded; conservative read+write-idle
criterion not met, entire candidate FAIL. No controller write/status clear/reset
or reprogramming used to force acceptance. This is not proof of active transfer:
PCAP reset/enable/direction and unconfigured-PL status semantics remain to review.
Other observations retained; PMU omitted explicitly/ownershipNOT_PROVEN.
Normal runtime restored192.168.2.3 with TTL/CoreDMA/analyzer ring-wrap/MonInj/
Ethernet PASS; lease released. No Si/SD/flash/OTP/Kasli writes. Evidence
`evidence/boot-pcap-hardware-2026-10-23`. Full DDR remains NOT_RUN/NOT_ADMITTED.
Next offline inspect AMD PCAP reset/control/direction sequencing and status
meaning before changing any criterion; no blind retry or register mutation.


### 2026-10-23 — PCAP status requires reset/mode context (offline)

AMD XFpga_PcapInit releases reset/selects PCAP/write direction before transfer;
write-completion waits WR_IDLE, readback waits RD_IDLE. FSBL bitstream path
asserts PCAP reset after transfer. These source paths show why status alone
cannot distinguish reset/disabled context from incomplete transfer; no reset/
mode/direction values were captured in prior failed run. Do not retrospectively
mark that run PASS or infer ongoing transfer. Added read-only four-register plan
(status/reset/control/direction) checked against actual xilfpga header. Two
field-independence/invalid-sample tests PASS; source hashes/line anchors in
`evidence/pcap-control-plan-2026-10-23`. No hardware access or criterion change.
Next integrate contextual read-only capture, report observation-only rather than
inventing a transfer-completion rule; retain prior criterion failure and PMU gap.
DDR write admission remains closed; no controller write/reset/reconfiguration.


2026-10-23: PCAP context eight-read capture integrated/tested offline. Physical
attempt blocked by absent exact Genesys USB UART, before reset/JTAG in both
candidate and restoration loaders. No board change; baseline not reverified.
See evidence/boot-pcap-context-unavailable-2026-10-23/assessment.json and fresh
boot-pcap-context-integration-2026-10-23 inputs. Reconnect exact board USB before
continuation. DDR admission remains closed; no completion inferred from reset.


2026-10-23 physical PCAP context PASS: two identical status0xa0000a46,
reset1/control1/direction0 observations. Reset control asserted is context,
not completion/exclusive ownership proof. Normal runtime192.168.2.3 restored
TTL/CoreDMA/analyzer/MonInj/EthernetPASS. USB blockage superseded. Full DDR
NOT_RUN/NOT_ADMITTED; PMU and PLHP0/reset epoch remain unresolved. Evidence
boot-pcap-context-hardware-2026-10-23; no repeat unchanged capture needed.



## 2026-10-23 — Generated HP0/reset topology audited (offline)

Reproducible anchor/hash audit confirms generated pl_resetn0 -> asynchronous
assert/two-flop sys_rst release, HP0 clock=sys_clk, sys-domain observer and
qualification tied0. Reset erases observer accounting; source and reset/CSR
simulation controls PASS. Generated GPIO bank5 toggle is visible, but this audit
does not establish PS-internal mapping or HP0 FIFO/reset/drain semantics.
Evidence `evidence/hp0-reset-epoch-audit-2026-10-23`; no hardware access.
Normal runtime remains last physically restored192.168.2.3. DDR NOT_ADMITTED.
Next inspect PS IP reset coverage/PS interconnect, then design a positively
qualified epoch or separately qualified no-PL diagnostic boot; never qualify
from reset+delay+zero alone. PMU future-owner exclusion also remains unresolved.



## 2026-10-23 — AFIFM2 reset differs from fabric reset (offline)

Pinned AMD source review: AFIFM2 has separate RST_FPD_TOP control mask0x200;
PMU generic handler asserts/releases controls. Generated psu_afi_config releases
AFI0..5 reset with mask0x1f80. This is not proof of HP0 outstanding completion
or disposal, and pl_resetn0 reset alone does not establish this PS reset action.
AMD UG1087 RDISSUE specifies configured maximum outstanding commands: field0
means one command, not zero pending transactions. Do not use RDISSUE/QoS limits
as an idle counter. Source anchors/hashes and reference URLs retained in
`evidence/afi-reset-audit-2026-10-23`; two audit controls PASS. No HW access/reset.
Next review isolation/quiesce acknowledgment semantics before a fixed read-only
observation plan. No AFI writes or arbitrary drain delay. Normal runtime remains
last restored192.168.2.3; full DDR NOT_RUN/NOT_ADMITTED, PMU ownership unresolved.



## 2026-10-23 — AIB route scope excludes an inferred HP0 drain certificate

Pinned AMD xpfw_aib source/header review: AFI_FS0/1 routes are named FPD->AFI_FS,
FS2 LPD->AFI_FS. No PL->AFIFM2->DDR exclusion established from these routes.
XPfw_AibEnable returns void after bounded ACK polling; a missing ACK only logs
and returns. Call completion must not be interpreted as isolation success.
Generated psu_ps_pl_isolation_removal_data requests PL power-up and polls power
status; that is not an HP0 outstanding counter. Two audit controls PASS, including
changed-route rejection; evidence `evidence/aib-route-audit-2026-10-23`.
No hardware access/AIB write, normal baseline unchanged, DDR NOT_ADMITTED.
Next prepare an explicit diagnostic PL profile without any DDR master and verify
its generated AXI outputs; qualify a new reset epoch separately rather than
repurposing reverse-direction isolation bits. PMU/core ownership remains open.



## 2026-10-23 — No-DDR-master diagnostic PL full HDL generated (offline)

Added separate Top variant `ddr-diagnostic`; normal variant defaults unchanged.
Enumerates exported PS slave AXI channels, rejects empty/incomplete/unreviewed
VALID inventory, and explicitly ties ARVALID/AWVALID/WVALID inactive. No RTIO/DMA
engine instantiated. Actual full PS/top generation confirms saxigp2 HP0 request
constants through imported aliases. Two unit controls PASS (six mock requests,
incomplete/unknown ports rejected). Reproducer `scripts/generate_no_ddr_master.py`
pins source helpers, actual PS XCI and all generated outputs, requires fresh path,
and invokes no Vivado. Evidence `evidence/no-ddr-master-hdl-2026-10-23`.
Generated artifacts in root state directory; no synthesis/bitstream/netlist or
physical validation claimed. Existing hardware manifests are historical pins,
not permission to re-pin their old image proofs to changed gateware source.

No hardware access; normal runtime remains last restored192.168.2.3. New request
inhibition does not resolve prior transactions or PMU/core ownership. Full DDR
NOT_RUN/NOT_ADMITTED. Next prepare explicit Dell build receipt/constant-netlist
checks for this variant, then bounded no-write boot/restore qualification before
any DDR writer. No AIB/AFI reset writes, flash/OTP/SD changes.



## 2026-10-23 — No-master diagnostic Dell build RUNNING

Fresh job `artiq-no-ddr-master-20261023` submitted using existing bounded remote
service/shared Dell build lock; host identity verified. SSH retained by submit
--wait (local exec session21743; preserve/poll, do not duplicate). Status active/
RUNNING at submission checkpoint. Explicit normalized PS XCI hash1712fe0f...304d
selected from prior qualified result, no automatic IP approval. Separate profile
allows no CSR map without changing local-RTIO required inputs. Post-route Tcl
requires unique PS SAXIGP2ARVALID/AWVALID/WVALID pins and each net TYPE GROUND;
missing pin or nonconstant net fails before bitstream. Result collector requires
exact three-net proof and report hash. Thirteen remote lifecycle/input/report
controls PASS including absent/changed constant-proof rejection.

Evidence `evidence/no-ddr-master-dell-build-2026-10-23`; source/artifact pins
retained. No build PASS/bitstream/hardware claim yet. No board access, baseline
unchanged; DDR NOT_ADMITTED. Next collect SAME job and review actual pin mapping,
timing/DRC/IP provenance; never relax a failed constant proof without inspection.



## 2026-10-23 — No-master diagnostic Dell build PASS (not hardware)

Same jobartiq-no-ddr-master-20261023 completed exit0 in3min21s; session21743
finished. Collected files SHA-verified and strict input/IP/timing/DRC/routing
checks PASS. Post-route PS8 SAXIGP2ARVALID/AWVALID/WVALID each unique and
connected to GROUND; exact netlist proof report retained. Setup2.776ns,
hold0.055ns,pulse2.5ns; internal missing clocks/unconstrained endpoints0,
DRC violations0. Four output-delay omissions remain for blinking LED outputs.
BitSHAdf35fe96f15249a8afd7de516c8112bbe3230c4227488c5493105a3fbf58912d.
PSXCI unchanged selected1712fe0f...304d. Evidence/reports:
`evidence/no-ddr-master-build-pass-2026-10-23`; artifact inventory explicitly
not an executable hardware manifest. No hardware access, baseline unchanged.

Next integrate explicit new-build preflight and no-write trained-boot PL load
into mandatory candidate/normal-restore lifecycle; preserve fresh helper pins,
negative controls and old failure evidence. No automatic reuse of normal-runtime
CSR qualification against a no-CSR image. Full DDR NOT_RUN/NOT_ADMITTED; prior
transaction history/PMU ownership still separate from constant request netlist.



## 2026-10-23 — No-master PL trained-window hardware PASS; normal restore PASS

Explicit new-build/image/helper gate added to trained observer only. Strict
build input/timing/netlist verification rerun before and under lease. CPU0 first
reaches positively stopped normal OCM observer terminal; diagnostic PL then
loaded without normal RTIO CSR preparation or AFI/AIB configuration changes.
PCAP same-boot context requires stable PL_DONE1 after load; all existing necessary
peripheral/master fields checked. No CPU1 worker/network runtime started in
candidate. Two gate controls plus five existing observer lifecycle controls PASS.
Fresh nested pins `evidence/no-master-boot-integration-2026-10-23`.

Physical full cycle132.586s under shared Genesys lease PASS, bitdf35fe96...58912d
loaded and PL_DONE observed. Candidate remains no-DDR-write observation only;
constant requests do not prove disposal of older PS transactions or PMU ownership.
Full DDR NOT_RUN/NOT_ADMITTED. Mandatory normal runtime restored192.168.2.3,
TTL/CoreDMA/analyzer ring-wrap/MonInj/Ethernet PASS; lease released. No Si/SD/
flash/OTP/Kasli changes. Raw evidence `evidence/no-master-boot-hardware-2026-10-23`.
Next offline design bounded OCM DDR diagnostic and explicit PMU/core/history
admission policy; do not repeat unchanged no-master load or bypass unresolved
ownership. No automatic destructive-test permission from this successful cycle.



## 2026-10-23 — Bounded DDR pattern engine host/AArch64 object PASS (offline)

Added freestanding C engine with callback-only memory I/O, no physical backend
or loader. Complete unique/aligned address list validated before first I/O:
max8192words, both actual configured windows, MMIO gap excluded. Four phases
zero/ones/address tags/complement; write-all/barrier/read-all detects aliases.
First fault/mismatch returns phase/address/expected/actual and completed counts.
Four actual-C host-model controls PASS including alias/fault injection and invalid
range no-I/O. Freestanding AArch64 relocatable object compiles with warnings as
errors; no undefined runtime symbols. This is NOT an executable OCM image.
Evidence `evidence/ddr-pattern-offline-2026-10-23`; source/reproducer/limitations
in `diagnostics/ddr/bounded_test/README.md`. No hardware access, baseline unchanged.

Next OCM code/stack/address-list/report placement and existing exception capture
integration, plus explicit ownership admission. Callback timeout cannot interrupt
stalled physical AXI by itself. PMU/core/history ownership unresolved; full DDR
NOT_RUN/NOT_ADMITTED. No deployment command provided or physical stores executed.



## 2026-10-23 — OCM-resident model image linked/checked (offline)

Integrated bounded engine with OCM-only model callbacks, startup and16-slot
exception vectors. Physical DDR addresses are lookup tags into four OCM cells;
no DDR backend or deployment loader. AArch64 ELF vectorsfffc8000/entryfffc8800,
code3312bytes, all memory extents inOCM, stackfffe0000..fffe4000. Startup rejects
wrongEL/cacheMMU/DIF state, installs/readbacksVBAR, clearsOCMBSS, runsmodel;
exception terminal retains diagnostic registers. No cache/interrupt-mask changes.
Two tests PASS: actual model C executes on host; actual cross-linked ELF layout,
missing-runtime symbols and invalid-stack rejection. Existing layout checker
returns execution-stateNOT_PROVEN. No A53/QEMU execution/exception injection.
First assembler immediate-mask incompatibility fixed; failed output preserved.
Evidence `evidence/ddr-ocm-model-offline-2026-10-23` includes source/ELF hashes.

No hardware access, normal baseline unchanged. Full DDR NOT_RUN/NOT_ADMITTED.
Next dedicated OCM model entry/exception capture loader with explicit image and
layout pins, then no-DDR hardware qualification under mandatory restore. PMU/
secondary-core/history ownership must close separately before physical backend.



## 2026-10-23 — OCM model loader/report gate tested (offline)

Added library loader for exact positively halted predecessor observer terminal,
EL3/noMCI/DIF/CPU0 admission, checked download controls, VBAR readback, bounded
100ms run then confirmed halt. Fixed13word reads only model report/result inOCM;
no physical DDR addresses accessed by capture. Gate pins ELF/symbols/helpers,
reruns OCM layout and exact entry/report/terminal addresses. Parser requires
successPC/x0/x15,16writes/16reads,phase3/error0,exact final address/complement tag
and matching data; faults/malformed/missing/duplicate frames reject.
Two actual-Tcl/real-image/stale-pin controls PASS, report/model MMIO allowlist
mocked. Evidence `evidence/ddr-ocm-loader-offline-2026-10-23`. No hardware access
or A53 model execution claimed; library not yet called by parent lifecycle.
Next integrate optional source-pinned model stage AFTER same-boot no-master
capture into inherited-lease child and mandatory normal restoration; prepare
fresh nested manifests/negative controls, then one bounded no-DDR physical run.
Full DDR NOT_RUN/NOT_ADMITTED; PMU/core/history requirements unchanged.



## 2026-10-23 — OCM model executes physically on A53; restore PASS

Integrated optional model stage AFTER trained OCM observer/no-master PL and
same-boot necessary master/peripheral checks. Parent requires no-master window,
exact nested ELF/layout/helper pins, reruns before/under shared lease. Child
selects exact CPU0 and requires halted predecessor terminal; captures fixed OCM
report. Seven offline loader/observer controls PASS. Fresh complete manifest
`evidence/ddr-model-boot-integration-2026-10-23`.

Initial attempt rejected by storage gate BEFORE hardware (<512MiB on sharedSSD).
Own completed2026-10-05 abi-acceptance build moved to root state disk:1578files/
551043483bytes SHA-verified plus symlink targets before old location replaced by
symlink. No tools/installers/other-thread files removed; relocation receipt kept.
Then physical cycle137.22s under shared Genesys lease PASS. Actual A53 reaches
model_done0xfffc888c/x15=0x33/x0=0; OCM report16writes/16reads/phase3/error0,
exact final address/tag/data matches, model_result0. These are OCM MODEL cells,
not physical DDR transactions. No injected exception/SError proof in this run.
Normal runtime restored192.168.2.3 TTL/CoreDMA/analyzerwrap/MonInj/EthernetPASS;
lease released. Evidence `evidence/ddr-model-boot-hardware-2026-10-23`.

No Si/SD/flash/OTP/Kasli writes. Full DDR NOT_RUN/NOT_ADMITTED. Next offline
model exception-injection qualification and explicit PMU/core/history ownership
policy before any physical DDR backend; no repeated unchanged model success run.



## 2026-10-23 — OCM model deliberate BRK physical capture PASS/restored

Added separately selected OCM_MODEL_BRK build: same layout, BRK#0x53 replaces
model call atfffc8880 after BSS initialization, before callbacks. Preflight
checks actual opcode d4200a60 for BRK mode and BL opcode class for normal mode;
BRK image cannot masquerade as normal. Decoder requires exact faultterminal/
vector4/EL3/ESRf2000053/ELRfffc8880/PSTATE/DAIF and zero report, distinct expected
fault status. Four offline loader/mode/negative controls PASS; fresh pins in
`evidence/ddr-model-brk-integration-2026-10-23`.

Physical cycle135.411s under shared Genesys lease PASS: exact deliberate
synchronous BRK captured, callbacks not reached. This does not qualify data abort,
SError or an unresponsive AXI transaction. Normal192.168.2.3 restored physical
TTL/CoreDMA/analyzerwrap/MonInj/EthernetPASS; lease released. No physical DDR
backend/DDRwrites,Si/SD/flash/OTP/Kaslichanges. Evidence/raw byte hashes:
`evidence/ddr-model-brk-hardware-2026-10-23`.
Next offline close explicit PMU/core/history ownership policy and define a bounded
physical-memory backend only once admission is justified. Do not repeat unchanged
model/BRK run; full DDR NOT_RUN/NOT_ADMITTED.



## 2026-10-23 — Actual target PMU configuration profiles reviewed offline

Used installed MicroBlaze GCC13.3 target preprocessor withSDT/PSU_PMU and actual
BSP headers, preserving firmware sources. Baseline enables PM, scheduler, FPGA
load/readback and secure services. ENABLE_PM_VAL0 removes PM but leaves the
other service macros. Broader explicit service-reduced profile removes those
four top-level facilities; remaining subfeature macros are NOT proof services
are compiled/active or PMU dormant. SLEEP_WHEN_IDLE persists in all profiles.
Actual-header profile assertions and fresh-output rejection PASS. Inputs/macros/
hashes in `evidence/pmu-profiles-review-2026-10-23`.

FSBL source anchors show conditional XFsbl_PmInit->XPm_InitXilpm/
XPm_SetConfiguration path with error exit, so do not install no-PM as a drop-in
replacement in existing trained boot. This review builds no firmware and grants
no PMU stop/mask/DDR admission. Next prefer boot-compatible post-handoff PMU
quiescence/telemetry acknowledgment design, or a matched dedicated boot profile;
retain AMD platform code. No hardware access, normal runtime unchanged. Full
DDR NOT_RUN/NOT_ADMITTED; core/history exclusion remains explicit.



## 2026-10-23 — PMU post-handoff protocol rules modeled (offline)

Defined boot/sequence-bound request->quiescence acknowledgment, only outside an
active handler at a reviewed AMD core-loop boundary. Seven explicit obligations
include scheduler/interrupt/core-release/PMU-memory exclusion and history drain;
these remain evidence requirements, not trusted host claims. No automatic resume
on timeout/disconnect after ACK: full PS restoration required. Four tests PASS,
including all128condition combinations, stale epoch/sequence, malformed fields/
clock rollback and timeout semantics. Receipts explicitly OFFLINE, never DDRpermit.
Transport/mailbox/IPI command UNSELECTED: model ELF RW extent spans linker gap
throughfffe4000; a mailbox placed there could be cleared by download. No private
PMU AP0 retry/alias or device reads. Design `diagnostics/ddr/PMU_QUIESCE_PROTOCOL.md`,
evidence `evidence/pmu-quiesce-protocol-offline-2026-10-23`.
No runtime firmware/board change. Next isolated AMD module/hook/transport source
integration and footprint/ROM-NMI/error review, before any deployment. Full DDR
NOT_RUN/NOT_ADMITTED; unresolved obligations cannot be bypassed by a model ACK.



## 2026-10-23 — Isolated AMD PMU boundary telemetry objects compile (offline)

Fresh source copy preserves original AMD PMU application. Exact-anchor patch
adds optional ARTIQ_PMU_BOUNDARY_TELEMETRY call at core-loop boundary before
sleep/scheduler. Header keeps32B static PMU-local BSS observation record;
ack always0/unresolved7f, no transport/host address or interrupt/service changes.
Actual patched AMD core compiles enabled/disabled with MicroBlazeGCC13.3/-Werror;
record symbol32B BSS only when enabled. Two controls PASS: actual C observations
cannot ACK even after counterwrap/forged field; changed/duplicate hook rejected.
Evidence `evidence/pmu-boundary-offline-2026-10-23`; original source hash retained.
No linked firmware/deployment/HW access or quiescence claim. Next isolated full
PMU link with unchanged AMD BSP/boot services, inspect local-memory capacity/
placement, and select a proven non-disruptive telemetry route. No private AP0
retry/alias guessing. Normal baseline unchanged; DDR NOT_RUN/NOT_ADMITTED.



## 2026-10-23 — Full diagnostic PMU telemetry firmware linked (offline)

Replayed actual existing AMD compile/link recipe in fresh isolated application
copy, adding only telemetry define; existing BSP/libraries/PM boot services
retained. All application units rebuilt, full ELF links. Local layout checker:
MicroBlazeentryffdc0050, telemetry32B zero-init RAMffdd7cf4, stackffddc2bc..
ffddd2c0,9248bytes before extension table. Total sections120440bytes. LegacyRWE
segment flags preserved/reported. Two actual-image controls PASS, including
corrupt-size and DDR-segment rejection. Source/recipe/BSP hashes and link/layout/
size reports `evidence/pmu-boundary-link-2026-10-23`. ELF286fb256...46e56b1;
no hardware/boot/telemetry access/coherence/quiescence claim. ACK always0.

Next review PMU debug-target read-only address-space access without halting,
resetting or retrying failed AP0privateaddress; telemetry transport remains
unqualified. Only after explicit new-image boot/restore integration and read
qualification consider one diagnostic cycle. Full DDR NOT_RUN/NOT_ADMITTED;
normal runtime unchanged. No firmware/Si/SD/flash/OTP/Kasli writes.



## 2026-10-23 — Documented external PMU RAM read physical PASS

Reviewed AMDUG1085 PMU view: local register file is PMU-only, while PMU RAM/
global registers have external32-bitAXI slave. This distinguishes failed private
AP0addressffd40024 from documented RAMffdc0000..ffddffff; no alias guessing or
private-register retry. XSDB2025.2 local mrd help confirms MEM-AP route. Dedicated
fixed allowlist two readsffdc0050, source-Tcl controls PASS, matching current
normal restore PMU ELF243e7751...eb31e (not diagnostic9f5c58 image).
Under shared Genesys lease two AP0read valuesb000ffdd match immutable code word.
No CPUtarget memory read/stop/reset/force/controlwrite or firmwareload. Raw logs/
source/reference hashes `evidence/pmu-ram-transport-2026-10-23`; lease released.

This closes access to this RAM code word only, not telemetry coherence or PMU
quiescence. Normal runtime not changed; no new network regression claimed.
Next integrate diagnostic PMU ELF with existing trained-boot/mandatory-restore
flow and fixed RAM record capture with sequence/readback validation. No generic
memorydump/privateMMIO probe; full DDR NOT_RUN/NOT_ADMITTED.



## 2026-10-23 — Diagnostic PMU boot/live boundary RAM telemetry PASS/restored

Optional PMU image override explicitly pinned/layout checked within normal
trained-observer/no-master window, excluding model stage. Existing normal
candidate/restore PMU pins unchanged. Dedicated fixed budget4samples: sequence,
8word burst, sequence; parser retains torn samples, accepts only equal-even
sequence plus magic/version/ACK0/unresolved7f/reserved0/nonzero count. Seven
capture/observer controls PASS. Fresh nested manifest
`evidence/pmu-boundary-boot-integration-2026-10-23`.

Physical cycle138.659s under shared Genesys lease PASS. Diagnostic PMUELF
286fb256...46e56b1 booted with trainedFSBL; two samples match sequence rule,
loopcounts5412/5415. Two concurrent/torn samples5418/5421 explicitly rejected,
no extra retries. This shows live boundary observation, not exclusion/coherence
proof under all reorder/wrap scenarios; PMU remains running, ACK0/unresolved7f.
No private register access, stop/mask/quiesce or physical DDR backend.
Normal PMU/ARTIQ restored192.168.2.3 TTL/CoreDMA/analyzerwrap/MonInj/EthernetPASS;
lease released. No Si/SD/flash/OTP/Kasli changes. Raw byte hashes and restoration:
`evidence/pmu-boundary-boot-hardware-2026-10-23`.

Next offline exact-session request channel/ordering and IRQ/ROM exclusion design
at qualified boundary before any ACK/park implementation; no unchanged telemetry
run. Full DDR NOT_RUN/NOT_ADMITTED; telemetry is not a write-test permit.



## 2026-10-23 — Session request/echo command compiled, observation-only (offline)

Added PMU-local request/echo32B records. Only kind1 OBSERVE accepted; nonce64,
monotonic sequence64, nonzero even generation, zero reserved, XOR corruption
check and repeated generation read. Publication clears echo generation first,
writes payload/statusOBSERVED/ACK0 then commits generation after mbar1. Four
mbar1 instructions verified in actual linked MicroBlaze disassembly. No park,
interrupt mask, resume or quiescence command. Three actual-C/source controls PASS:
partial publication, stale generation/sequence, bad checksum and kind2 rejected;
valid echo cannot assert ACK. Cooperative publication protocol, not authentication
or protection from malicious concurrent writers; no hardware transport exercised.

Fresh full firmware links; local-layout checkerPASS, telemetry nowffdd7e40,
requestffdd7e20/echoffdd7df4;8896bytes before table. Old hardcoded telemetry gate
rejects changed address and must not be reused. ELF8ae05823...810d9. IRQ/exception/
ECC/power source review retains unresolved exclusions. Evidence
`evidence/pmu-request-offline-2026-10-23`. No firmware/HW writes,baseline unchanged.
Next explicit new-image/symbol-derived fixed request publication/readback gate,
then bounded observational echo/mandatory restore test; no IRQ/ROM exclusion or
DDR admission inferred. Full DDR NOT_RUN/NOT_ADMITTED.



## 2026-10-23 — PMU session echo PASS; storage blocked restore; separate recovery PASS

Integrated separate request-image gate into no-master trained boot. Exact symbol/
ELF/helper pins, kind1 only, fresh-zero request/echo records required. Fixed9word
writes only to request32B: invalidate generation, payload, full readback then
publishgeneration2/readback. Four fixed response snapshots bind nonce64/seq1/
statusOBSERVED/ACK0/reserved0. Six transport/observer controls PASS. Fresh nested
manifest `evidence/pmu-request-boot-integration-2026-10-23`.

Physical request/echo PASS, all4snapshots match nonce2afa586f3b265f9b/seq1.
PMU did NOT park/quiesce; no DDR backend. Automatic restoration then FAILED
before reset: concurrent disk consumption dropped sharedSSD from579735552 to
514957312bytes, below536870912minimum. Original FAIL/restorationFAIL retained,
not relabeled fullcyclePASS. Did not repeat candidate/request. Reacquired shared
Genesys lease for recovery; own completed2026-10-05 abi-suite copied/SHAverified
and replaced by preserved-path symlink on rootstate disk. Recovery77.18s then
restored originalPMU/ARTIQ192.168.2.3; physicalTTL/CoreDMA/analyzerwrap/MonInj/
EthernetPASS. Both leases released. Exact recovery script/logs/relocation and
assessment `evidence/pmu-request-boot-hardware-2026-10-23`.

No Si/SD/flash/OTP/Kasli changes. Next offline disk reservation/recovery guard
before more diagnostic loads: point-in-time headroom insufficient under concurrent
writers. Then progress IRQ/ROM exclusion policy; no unchanged request retry or
quiescence inference. Full DDR NOT_RUN/NOT_ADMITTED; normal baseline restored.



## 2026-10-23 — Allocated restoration reserve integrated/tested offline

Parent now allocates768MiB real blocks on each distinct runtime filesystem under
board lease BEFORE candidate access. posix_fallocate+fsync+st_blocks check;
files immediately unlinked, FDs parent-only (not inherited by children), so no
orphan reserve paths after process exit. Requires reserve+existing512MiB headroom,
then reruns unchanged storage admission. Deduplicates same-filesystem roles.
Lifecycle releases blocks BEFORE restoration after success/error/interrupt;
release failure recordsFAIL but still attempts restore. Context cleans partial
allocation/preflight failures. Results record allocation/release metadata.

Seventeen allocation/lifecycle/storage controls PASS, including parent refuses
before HW subprocess, actual blocks/no visible file, partial allocation cleanup,
KeyboardInterrupt, and release-error recovery. Actual default768MiB allocation/
release on root filesystem verified. No board access/HW-cycle claim. Evidence
`evidence/restore-reservation-offline-2026-10-23`. Does not guarantee against other
writers consuming space AFTER release, inode/quota/I/O faults or SIGKILL during
restore. No storage gate lowered/bypassed. Old helper-pinned manifests remain
historical and require fresh reviewed pins for future stages.
Next offline enough-space inventory and fresh guarded integration preflight,
then resume PMU IRQ/ROM exclusion work, not unchanged request replay. Normal
ARTIQ remains restored192.168.2.3; full DDR NOT_RUN/NOT_ADMITTED.



## 2026-10-23 — Fresh reserve-aware preflight and maintained IRQ-mask review

Regenerated complete nested helper pins against new allocated-reserve parent;
actual offline parent preflight PASS in
`evidence/restore-guarded-request-preflight-2026-10-23`. No unchanged request
execution. Offline sharedSSD checkpoint969580544bytes is BELOW1342177280
(reserve768MiB+normal512MiB), so hardware would not be admitted. Space must be
rechecked/reserved before next load; no threshold reduction or override.

Compiled maintained MicroBlaze interrupt/exception disable assembly using actual
BSP includes. Objects show IE-only clear0x2 versus EE clear0x100 via fallback
mfs/andi/mts. Canonical XPAR_MICROBLAZE_USE_MSR_INSTR is not assumed present;
no incorrect msrclr claim. Source Xil_ExceptionDisable conditionally calls both
helpers, so future laboratory guard should preserve exception diagnostics using
interrupt-only helper and explicit MSR readback. Actual object/mask/flow controls
PASS; `evidence/pmu-irq-policy-2026-10-23` contains commands/source/object hashes
and disassembly. No linked guard or target execution. IE0 is not ROM/NMI/error/
DDR exclusion; scheduler/history/secondary-core obligations remain.
Next isolated, default-disabled laboratory guard source design at qualified
boundary with no return to scheduler/no resume, ACK0 until remaining ownership
is established. Review whole control flow before any target attempt. No hardware
access; normal baseline unchanged; full DDR NOT_RUN/NOT_ADMITTED.



## 2026-10-23 — Default-disabled lab guard compiled/flow checked (offline)

Added explicit --lab-guard firmware variant; normal build has no guard function/
record and kind2 remains rejected. Opt-in validated requestkind2 uses maintained
interrupt-only helper, reads MSR before/after, reports state2 only for exact IE
clear with other bits preserved (otherwise state3). Both commit ACK0/unresolved7f
and enter no-return nop/backward-branch loop, no scheduler/sleep/resume dispatch.
New64B recordPMU-localffdd7f68, terminalffdc4734. Static checker binds actual
relative helper-call target, local layout, complete instructions, no return or
external conditional branch and pure terminal loop. Four controls PASS: actual C
host-child guard/failed-MSR, actual linked flow corruption rejection, no guard in
default ELF, and default requestkind2 rejection. Both full MicroBlaze builds link.
Evidence `evidence/pmu-lab-guard-offline-2026-10-23`; no target execution.

No HW/interrupt-mask/firmware change on board; normal ARTIQ unchanged. This is a
laboratory stop-loop candidate, NOT exclusive DDR ownership: exception/ROM/NMI/
error paths, prior transactions and secondary cores remain unqualified. Next
explicit image/layout/terminal observation gates and reserved-space restoration
preflight before considering one bounded guard entry/recovery trial. Old request
addresses/manifests must not be reused. Full DDR NOT_RUN/NOT_ADMITTED.



## 2026-10-23 — Guard image/request gates and explicit recovery Tcl (offline)

New exact guard gate reruns local layout/flow checks and regenerates nm/objdump
from selected ELF, comparing symbol/disassembly files. Fixed requestffdd7f20/
guardffdd7f68,64B record, terminalffdc4734; no reuse old addresses. Kind2 request
publisher checks fresh BSS, writes9bounded words only request32B, readback before
commit. Four fixed16word record attempts; requires exact session/state2/IE1->0
with all other MSR bits preserved/ACK0/unresolved7f, malformed/failure rejects.
No targetPC/continuous-state or ROM exclusion inferred from record.

Recovery must NOT depend on parked PMU servicing ordinary reset. Added exact
MicroBlaze PMU debugger selection, explicit stop and bounded positive halt check,
baseline download/resume BEFORE normal system reset/PMU-FSBL/ARTIQ restore.
Unconfirmed halt never downloads; bootstrap marker is not restoration PASS.
Four actual-Tcl/real-ELF/negative controls PASS; evidence
`evidence/pmu-guard-gates-offline-2026-10-23`. No new-image load/guard entry or
PMU stop on hardware. Next integrate this recovery step and guard capture in
parent lifecycle under shared lease with real block reserve/fresh pins; enough
space must precede any trial. Full DDR NOT_RUN/NOT_ADMITTED; normal baseline
unchanged. ROM/NMI/error/history/core requirements remain unresolved.



## 2026-10-23 — PMU lab-guard attempt FAIL; reserved-space/debug recovery PASS

Integrated explicit guard image gate and separate no-master trained child mode.
Parent restoration for this mode first positively halts exact PMU via debugger,
downloads/resumes original pinned PMU, then normal full reset/boot/debug/Ethernet;
missing bootstrap marker rejects recovery. Real block reserve held before target
access/released before restore. Sixteen offline gate/reserve/lifecycle controls
PASS. Fresh pins `evidence/pmu-guard-boot-integration-2026-10-23`. Enough room
obtained by relocating own completed2026-10-17 Kasli result:1334files862500246B
SHAverified, absolute/internal symlinks checked, old path preserved. No KasliHW.

Single physical cycle143.959s under Genesys lease: requestkind2 published, FIRST
guard-recordAP0readffdd7f68 failed APtransactiontimeout. No guard/MSR record, so
entry/IEclear NOT_PROVEN. No retry/force/alias/alternative-address read. Whole
candidateFAIL preserved. Exact PMUdebug halt/download/resume bootstrapPASS;
normal192.168.2.3 restored TTL/CoreDMA/analyzerwrap/MonInj/EthernetPASS. Two
filesystems768MiB real block reservations allocated/released; no storage failure.
Lease released. Evidence/rawbytehashes
`evidence/pmu-guard-boot-hardware-2026-10-23`. No Si/SD/flash/OTP/Kasli changes.

CauseUNDETERMINED: tight RAM instruction-fetch arbitration or interrupt-related
access dependencies are only hypotheses, not board fault diagnosis. Next offline
review PMU RAM/debug/arbitration and linked terminal before a specifically changed
candidate. No unchanged guard retry, no treating timeout as successful quiescence.
Full DDR NOT_RUN/NOT_ADMITTED; normal baseline restored and usable.

## 2026-10-23 — PMU RAM arbitration requirement identified offline

Official UG1085 v2.5 p113 requires sleeping PMU for external APB RAM access;
tight instruction fetch can starve external access. Failed guard ends in nop/
backward branch, so its no-load/store property was insufficient. This is a
documented test-design defect consistent with timeout, not proof of guard entry.
UG984 sleep/wakeup semantics and installed BSP reviewed. No HW or image changes.
Next: specifically changed default-off sleep terminal, linked-flow negative
controls and fresh pins before any bounded leased trial. ACK remains0; full DDR
NOT_ADMITTED. Evidence `evidence/pmu-guard-ram-review-2026-10-23`.

## 2026-10-23 — sleep guard compiled and qualified offline

Fresh enabled/default-disabled PMU builds PASS. Guard now publishes with barrier,
then sleep at0xffdc4738/backbranch; wakeup re-enters sleep without scheduler.
Linked checker rejects former nop loop, missing barrier, helper mutation/escape.
Three host/static test cases PASS; no physical sleep or DDR admission claim.
Old artifacts/manifests preserved. Existing hardware gate rejects changed terminal;
fresh sleep-specific manifest/gate and wake residency review are next. No HW access.
Evidence `evidence/pmu-sleep-guard-offline-2026-10-23`.

## 2026-10-23 — fresh sleep guard integration preflight PASS offline

Exact sleep terminal/image gate and fresh nested manifests prepared; historical
manifests preserved/rejected. Full parent preflight PASS. Eight guard tests PASS,
including first record-read timeout unwind without retry/alias. No HW access.
Next bounded leased capture with storage reserves and explicit PMU restoration;
wake residency and coherent live record remain unproven. DDR NOT_ADMITTED.
Evidence `evidence/pmu-sleep-guard-integration-2026-10-23`.

## 2026-10-23 — physical sleep guard capture and restoration PASS

Single Genesys lease143.994s, changed sleep image7a82b8f2...f51c4. Four coherent
nonce-bound records: MSR80000106->80000104, IEonly cleared; state2/ACK0/unresolved7f.
No timeout/retry. Explicit PMUdebug bootstrap and normal reset/load/TTL/CoreDMA/
analyzerwrap/MonInj/Ethernet restorationPASS192.168.2.3. TwoFS768MiB reserves
released before restore; lease released. No Si/SD/flash/OTP/Kasli changes.
Sampled record is not continuous PC/sleep/ROM-NMI/all-core exclusion proof;
full DDR NOT_ADMITTED. Next offline remaining exclusion obligations, no unchanged
repeat. Evidence `evidence/pmu-sleep-guard-hardware-2026-10-23`.

## 2026-10-24 — post-guard exclusion obligations audited offline

Updated authoritative DDR admission status after physical sleep-guard PASS.
Seven whole-system obligations remain qualified/unclosed. Exact candidate source
shows preserved EE can reach hardware/software exception diagnostics/MMIO and
non-sleep loops; ordinary guard flow alone is insufficient. No HW access.
Next exact linked exception-vector/helper/transitive footprint audit, preserving
exception reporting. No unchanged capture retry; DDR NOT_ADMITTED. Evidence
`evidence/ddr-post-guard-review-2026-10-24`.

## 2026-10-24 — linked PMU exception inventory, exclusion still open

Offline exact-image direct-edge audit:13function blocks/26edges/148memoryops,
software/hardware exception selfloops verified. printf bra r3 atffdcc9ec remains
unresolved; conditional/unsupported control retained, effective addresses unproven.
Two decoder tests PASS. No HW or exception-policy changes. Next ELF-backed printf
jump-table and memory-footprint review; DDR NOT_ADMITTED. Evidence
`evidence/pmu-exception-flow-2026-10-24`.

## 2026-10-24 — printf indirect table bound to exact ELF offline

22table words atffdd35d0 resolve to7aligned targets inside xil_printf;9instruction
words pinned. Two actual-ELF tests PASS with corrupt-target/opcode controls.
Index-bound domination remains unproven; table inventory is not whole-path proof.
No HW/firmware changes; DDR NOT_ADMITTED. Next linked CFG bound/delay-slot review,
then memory footprint. Evidence `evidence/pmu-printf-table-2026-10-24`.

## 2026-10-24 — printf delay-slot structural dominance PASS offline

All printf instruction words bound to ELF. Contextual delay-slot graph shows
index-check instructions dominate indirect jump, assuming callees return normally.
Two tests PASS incl synthetic bypass/text mismatch rejection. Register-value/CMPU
semantics, callee ABI and memory footprint remain unresolved; DDR NOT_ADMITTED.
No HW/firmware changes. Evidence `evidence/pmu-printf-cfg-2026-10-24`.

## 2026-10-24 — printf range/direct exception MMIO review offline

CMPU/BLTID source semantics narrow surviving index to0..21 under prior CFG/callee
assumptions;10boundary arithmetic controls PASS. Direct errorMMIO/UART addresses
classified, notDDR; UARTpoll forward progress unbounded. Full format/ctype/varargs/
stack/helper footprint remains open. No HW/firmwarechanges;DDR NOT_ADMITTED.
Next exact format/ctype/varargs and exception-stack audit. Evidence
`evidence/pmu-printf-range-memory-2026-10-24`.

## 2026-10-24 — exact exception format/varargs/frame inventory offline

ELF format contains four%x integer fields, no%s/dynamic pointer formatting.
Four handler register arguments match linked printf spill/varargs offsets inside
28byte callerframe. Ctype257bytes localPMU. Six negative frame adjustments sum276
but are NOT runtime stack bound; entrySP/nesting/priorframes remain unresolved.
No HW/firmwarechange;DDR NOT_ADMITTED. Next ordinaryguard-entry stack chain and
exception-entry/nesting review. Evidence `evidence/pmu-format-stack-2026-10-24`.

## 2026-10-24 — ordinary PMU guard stack chain identified offline

ExactELF Init->Main->guard;CoreLoop/telemetry inlined. Retained64+28=92bytes,
conditionalSPffddd504. Prior276frameinventory+92=368 is NOT runtime bound.
Hardwareexception clearsEE/setsEIP perAMD;reset/nonmaskablebreak and actualcore
faultconfiguration unresolved. No HW/firmwarechanges;DDRNOT_ADMITTED. Next linked
breakvector/coreconfiguration/ROM review. Evidence
`evidence/pmu-guard-stack-entry-2026-10-24`.

## 2026-10-24 — ROM/RAM vector bridge identified as open boundary

BSP basevectorsffd00000 lies in PMUROM; auditedELF vectors are RAMffdc0000.
RAMbreakslotffdc0018 has8zero filebytes/no handlersection. Prior handler/stack
review is conditional on unproved ROM->RAM eventbridge, not fullhardwarepath.
Physicalguard/restorePASSunchanged. NoHW/ROMreads/firmwarechanges. Nextmaintained
AMDROM/eventforwardingAPI source review;DDRNOT_ADMITTED. Evidence
`evidence/pmu-rom-vector-boundary-2026-10-24`.

## 2026-10-24 — vector mapping depends on uncaptured GPO0 remap

UG1085p119 and exactheader define GPO0bit0 ROM/RAM64bytevector remap. Thus prior
baseaddress alone does NOT establish liveROMentry; mappingUNKNOWN. ROMextension
table mechanism found but not general exception/break forwarding proof. NoHW or
remapwrites. Next linkedstartup/BSP audit then bounded PMUlocal readonlytelemetry
plan ifneeded;DDRNOT_ADMITTED. Evidence `evidence/pmu-vector-remap-review-2026-10-24`.

## 2026-10-24 — opt-in PMU-local GPO0 snapshot built offline

--vector-snapshot requires labguard;localreadonlyXil_In32 GPO0,version1/rawfield
in reservedrecordwords,ACK0/sleep preserved. ActualELF layout/guardPASS;read
ffdc4738 fromffd40010,terminalffdc474c. C host good/badMSR with/withoutflagPASS.
NoHW;oldparser/layoutpinsrejectnewformat. Next strictreadmutationchecker and
versionedtransport/freshgates;DDRNOT_ADMITTED. Evidence
`evidence/pmu-vector-snapshot-offline-2026-10-24`.

## 2026-10-24 — vector-v1 read-address/parser/integration gates PASS offline

Strict singleGPO0read+version/store checks;newliteraladdress transport and parser
rejectlegacy/mismatched/unstable records. Nineguardtests+fullparentpreflightPASS.
Freshnestedmanifests preservehistoricproofs. NoHW. Nextboundedleasedsnapshot+
reservednormalrestoration;bit0samplewillnotadmitDDR. Evidence
`evidence/pmu-vector-snapshot-integration-2026-10-24`.

## 2026-10-24 — physical PMU-local GPO0 snapshot PASS, normal restored

Singlelease147.988s. Version1/rawGPO0=0 captured once byPMU, fourcoherentrecord
reads;bit0clear=>defaultROMvectors atsample. No remapwrite/ROMread/privatealias.
ACK0/IEcheckPASS. ExplicitPMUbootstrap/fullnormalTTL/CoreDMA/analyzer/MonInj/
EthernetrestorePASS192.168.2.3;twoFS768MiBreservesreleased/leasefree. NoSi/SD/
flash/OTP/Kasli. ROMeventbehavior/futuremap stillopen;DDRNOT_ADMITTED. Nextoffline
independentcore/historyexclusion, no unchangedrepeat. Evidence
`evidence/pmu-vector-snapshot-hardware-2026-10-24`.

## 2026-10-24 — core/history ordering gap and observe-dispatch fix offline

Master/core snapshots precede PMUguard;no-masterPL suppressesnewrequests only,
notearlierPSdrain/globalepoch. No newHWcapture selected. Nextresetdomain/FSBL
release audit. Fixed observe-onlybranch accidentallyusingguardprofileargs;actual
ASTbranchPASSguardNone,priorbugnegativecontrolrejected. LastHWguard unaffected.
Changedhelperhash invalidatesolddeploymanifests;no repinninghistoricalproofs.
DDRNOT_ADMITTED. Evidence `evidence/ddr-core-history-review-2026-10-24`.

## 2026-10-24 — reset/release semantics narrowed offline

UG1085:APUreset notgracefulrequesttermination;PMUSRST preservesstate unlikePOR.
ExactFSBLJTAGbranch bypassesordinarypartitionload,setsRPUusagebits(policyonly).
No inference that ordinarycore-releasebranchesran. Threeobligations separated:
currentexecution/futurerelease/priortransactiondrain. NoHW/resetchanges.
NextPMURPUsleep/wake/reset transitions+interconnectresetguarantees;DDRNOT_ADMITTED.
Evidence `evidence/ddr-reset-release-review-2026-10-24`.

## 2026-10-24 — documented AIB drain found; vendor timeout is not propagated

UG1085p420 AIB blocksnew/completespostedtransactions withACK. ExactRPU sleep
callsvoidXPfw_AibEnable thenreset/NCPUHALT anddisablesisolation;returnsSUCCESS.
Actualvendorfunction hostmockPASS:missingACK15pollsreturnsnormally,immediateACK
1poll. ThusRPU successNOTdrainreceipt. NoHW/firmwarechange. NextdiagnosticACK
protocol+pathcoverage/controlaccessreview beforeanyisolationcandidate;DDRNOT_ADMITTED.
Evidence `evidence/pmu-rpu-aib-review-2026-10-24`.

## 2026-10-24 — explicit AIB ACK/hold reference model PASS offline

RPUmaster-onlymask30000;freshREQ/ACK,boot/sequence/type/requestchecks,finitepolls,
allbitsACK required. Partial/timeout=>FAILED_HELD,noautorelease;successstillnotDDR
permit. Fourmodeltests+vendorbodytestPASS. OCM/LPDDDRothermasks rejected;control
access/ownershipcoverageunproven. NoHW/MMIO/firmwareintegration. Nextfixedreadonly
REQ/ACK/TYPEschema+decoder;DDRNOT_ADMITTED. Evidence
`evidence/aib-ack-protocol-offline-2026-10-24`.

## 2026-10-24 — fixed AIB readonly schema/decoder PASS offline

TwoREQ/TYPE/ACK/REQsamples,8fixedAP0reads,no writes/reset/force. ActualTclmock+
strictdecoder2testsPASS;changed/malformed/ownedstateshandled,no writepermit.
ABA/nonatomicsnapshot/ownershiplimitations explicit. NoHW/standalonelauncher.
Nextoptionalparentownedobserverintegration/freshpins;DDRNOT_ADMITTED. Evidence
`evidence/aib-readonly-offline-2026-10-24`.

## 2026-10-24 — parent-owned post-guard AIB observation integrated offline

Explicitbooleanrequiresguard/no-master;exactprobe/decoderpins passedtoinherited
leasechild. Eightreadsafterguard,nowrites,retryornewfirmware. Fullpreflight+
11integration/transport/dispatch/lifecycletestsPASS. Freshmanifests preservehistory.
NoHW. Nextboundedchangedobservation+reservedrestoration;DDRNOT_ADMITTED. Evidence
`evidence/aib-guard-integration-2026-10-24`.

## 2026-10-24 — AIB readonly capture PASS; PMU restore download FAIL

PostguardREQ/ACK00c00000/TYPE19cf000f twice;selectedRPUMbits30000clear,notglobalzero.
OverallFAIL/restorationFAIL:positivePMUdebughalt thenbaselineELFdowffdc0000 error
MicroBlazedataregisterread. No normalreset/load/debug/Ethernet;currentbaseline
NOT_RESTORED/UNKNOWN. No unchangedretry/force/resetbypass. Lease released;board
requiresphysicalpowercycle thenleasednormalrecovery beforeotheruse. Storage
reservesworked;earlierpreHWspaceblock+verifiedownartifactrelocationpreserved.
DDRNOT_ADMITTED. Evidence `evidence/aib-after-guard-hardware-2026-10-24`.

## 2026-10-27 — normal runtime recovered after user reboot PASS

OneGenesyslease87.214s;exactnormalartifactsverified,PMUdownload/FSBL/PL/CPUloadPASS.
TTL/CoreDMA/analyzer/MonInj/EthernetPASS192.168.2.3. Lease/reservesreleased.
No diagnosticguard/AIBwrite/Si/SD/flash/OTP/Kasli. PreviousrestoreFAILpreserved;
rootcauseUNKNOWN,notunchangedretryapproval. Currentbaselineusable;DDRNOT_ADMITTED.
Evidence `evidence/genesys-cold-recovery-2026-10-27`.

## 2026-10-27 — pre-download PMU register gate prepared offline

Restorationloggap:stop/suspended followedbydow withoutcore-registerread. Added
exactr0zero-dict gatebeforeRAMdownload+stage markers;no retry/force. Installed
XSDBnvlist implementationreviewed. FourTclmock+sixlifecycle testsPASS;physical
newgateNOT_RUN/rootcauseUNKNOWN. Oldpinsinvalidated,historypreserved. Current
normalbaselineunchanged;DDRNOT_ADMITTED. Evidence
`evidence/pmu-restore-register-gate-2026-10-27`.

## 2026-10-27 — normal-only restoration qualification plan PASS offline

Newwrapper defaultsnoHW,exactnormalartifact/helperpins,sharedlease/realreserves.
One r0-gatedPMUbootstrap thennormalruntime/tests;7orderedmarkers,no retry/guard/
AIBwrites. Threewrapper+fourTcltestsPASS;offlineplanv2PASS. Nextboundednormal-only
physicalqualification,notguard-stateproof. Baselineunchanged;DDRNOT_ADMITTED.
Evidence `evidence/pmu-restore-qualification-plan-2026-10-27`.

## 2026-10-27 — normal-only r0-gated PMU restore physical PASS

OneGenesyslease80.475s;stop/halt/r0zero/download/resume7orderedmarkersPASS.
Fullnormalreset/boot/TTL/CoreDMA/analyzer/MonInj/EthernetPASS192.168.2.3.
Realreservesreleasedbeforeload/leasereleased. No guard/AIBwrite/Si/SD/flash/OTP/
Kasli. NormalcontextONLY,notguard-stateproof;oldFAIL/rootcauseUNKNOWN unchanged.
Nextofflineguardrecoveryobligationreview;DDRNOT_ADMITTED. Evidence
`evidence/pmu-restore-normal-hardware-2026-10-27`.

## 2026-10-27 — restoration contexts compared; changed no-AIB guard plan

RetainedPASS/FAILsamePMU/PL/MSR/GPO0;extraAIBreads differ,butcausationUNKNOWN.
FreshplanexplicitnoAIB,newr0gate andshared7orderedstagevalidator. Fullpreflight+
16Tcl/wrapper/image/lifecycletestsPASS. NoHW;nextONEboundedchangedguardcontext
qualification,abortwithoutretryonfailure. Normalbaselineuntouched;DDRNOT_ADMITTED.
Evidence `evidence/pmu-restore-context-comparison-2026-10-27` and
`evidence/guard-context-recovery-plan-2026-10-27`.

## 2026-10-27 — changed no-AIB guard-context recovery physical PASS

Onelease145.512s;guardPASS thenr0/download/resume7orderedstagesPASS. Fullnormal
TTL/CoreDMA/analyzer/MonInj/EthernetrestorePASS192.168.2.3. Reserves/leasereleased.
InitialpreHWstorageblock preserved,owncompletedbuildverifiedrelocation1380entries
oldpathsymlink;thresholdunchanged. No AIB/Si/SD/flash/OTP/Kasli changes.
PriorFAIL/rootcauseUNKNOWN unchanged;notAIBcausalproof. Nextofflineclassify
existingAIBinstance/initializationcoverage;DDRNOT_ADMITTED. Evidence
`evidence/guard-context-recovery-hardware-2026-10-27`.

## 2026-10-27 — retained AIB bits map to USB slave interfaces offline

REQ/ACK00c00000=USB0S/USB1S instances7/8 LPD->USB,notUSB-DMA-toDDR isolation.
14AXImapheadercrosscheck+2testsPASS;5ACKmodeltestsPASSinclrealUSBbaselinepreserve.
PMUSBtransitionpathfound,actualinitializerUNKNOWN. AMDspecialRPUreset permits
continue-after-timeout;notgeneralvendorbug,stillnotstrictdrainreceipt. NoHW.
NextisolatedCstrictRPUMACK/hold/mockbackend;DDRNOT_ADMITTED. Evidence
`evidence/aib-directed-map-2026-10-27`.

## 2026-10-27 — strict AIB callback protocol C offline PASS

NoMMIObackend/firmwareintegration. RPUmasksubsetonly,onepreservingrequestwrite,
fullACK/unchangedREQ-TYPE,finitepoll/deadline,callbackerrors/timeouts noautorelease.
ActualCoptimized+ASan/UBSanfixturesPASS;5PythonmodeltestsPASS. ResultneverDDRpermit;
callbackbounds/competingwriters/sessioncoverage unresolved. NoHW. NextMicroBlaze
objectcompile/stack-call audit+sessionbinding. Evidence
`evidence/aib-strict-c-offline-2026-10-27`.

## 2026-10-27 — strict AIB actual MicroBlaze object build PASS offline

ReplayedactualPMUrecipe+nonLTOstacktwin;1264byte.text identical,data/bss0.
Staticframes116+48=164internalonly,notfinalbound. Compileradds36bytememset;
readelf/relocation exposeUNDdespitefatLTO-nmempty. Callbackaddresses/stackopen.
No finalfirmware/backend/HW. NextCsessionbinding thenisolatedlinkaudit;
DDRNOT_ADMITTED. Evidence `evidence/aib-strict-microblaze-2026-10-27`.

## 2026-10-27 — one-shot C session + isolated PMU LTO link PASS offline

Boot/nonce/sequencebind,consume-beforecallback,no retry/rearm;actualhostoptimized+
ASan/UBSan session/corefixturesPASS. Audit-onlyPMUlink+layoutPASS,no mainhook/MMIO
backend/deployment. Finalframesexecute172/snapshot48,notfullbound. Tokensnotphysical
bootproof,concurrentwritersunexcluded. NoHW. Nextboundedbackend/address/callback
contract+core/restorationaccessreview;DDRNOT_ADMITTED. Evidence
`evidence/aib-session-link-offline-2026-10-27`.

## 2026-10-27 — fixed-address backend policy adapter offline PASS

REQ/TYPE/ACKreads mappedfixed;soleREQwrite preservesinitialUSBbits/selectedmask,
rechecksREQ-TYPE,oneattempt/no clear/retry. Actualadapter+session+protocoloptimized/
ASanUBSanfixturesPASS;session/corefixturesPASS. No physicalMMIO/backend/HW.
OCM/debug/restorationaccessunderisolation notproven;sourcehold/concurrentwriters
open. NextMicroBlazelink/callbacktable+boundedtransportaudit;DDRNOT_ADMITTED.
Evidence `evidence/aib-backend-policy-offline-2026-10-27`.

## 2026-10-27 — backend PMU LTO callback/address audit PASS offline

Exactlinkedcallbackstores/readenumtablePASS;actualELFmutationsrejected. Stack
internalread172+48+28=248excludestransport/caller. NoMMIO/deployment/HW. Newtime
obligation:backendREQ-TYPErechecksoccurafterprotocoldeadlinecheck,beforewrite;
no claim allpostdeadlinewritesprevented. Nexttimedfaultinjection/budgetcontract;
DDRNOT_ADMITTED. Evidence `evidence/aib-backend-link-offline-2026-10-27`.

## 2026-10-27 — backend recheck deadline bug reproduced/fixed offline

Before100tickrecheck/10budgetstilldispatchedwrite;actualC reproduced. Newcallback
start/timeoutABI,backendentry+postrechecktimechecks blocklate dispatch. Transport
errorcodesmappedIOuncertain,notfalsecancellation. FourCoptimized/ASanUBSan suites
PASSincllatecompletion/no rollback. NoHW. Oldtargetauditstale;nextrebuildABI/
stack/linkbeforetransport/deployment. DDRNOT_ADMITTED. Evidence
`evidence/aib-deadline-fix-offline-2026-10-27`.

## 2026-10-27 — changed deadline ABI MicroBlaze/LTO audit PASS offline

Actualrecipe auditlink/localfootprintPASS. ElevennativeABIwords bindstart r7/r8,
timeout r9/r10/calleesavedpairs. Hostdeadline optimized+ASanUBSan18scenario variants
PASSinclhigh64bitbase/>32bittimeout. Finalwriteframe76(previous44);internalread/
writepaths248excludeexternalcost. NoHW/MMIO/deployment. Nexttimer/transportbounded
faultcontract;DDRNOT_ADMITTED. Evidence `evidence/aib-deadline-target-audit-2026-10-27`.

## 2026-10-27 — real PMU timer/MMIO contract not ready

ActualBSP MBbusyloop/noTickTimer,compiledlibnoXTime_GetTime. SchedulerPIT1 reload
10ms/softwaretickIRQ,notguarddeadlinewithIEclear. VolatileIn/Out no ordinaryerror
status orhungaccesspreemption. ATBcoverage/enableforPMU->AIBnotproven. NoHW/writes.
PhysicalbackendNOT_READY;nextPITownership+accessrouteinventory/read-onlyplan,
DDRNOT_ADMITTED. Evidence `evidence/pmu-time-mmio-contract-2026-10-27`.

## 2026-10-27 — GPO0 write-only discovery invalidates mapping inference

UG1087GPO0/DEBUG_REMAP WO:earlierread0NOTROMselectionproof;mappingUNKNOWN.
Vector-v1deployment/builderblocked,directMicroBlazecompile#error;archivalparser
rawonly/UNKNOWN. Refusal/transporttestsPASS. Historicalrawbytes/successes/failures
preserved,incorrectnarrativesannotated. PITpreloadWO,counterRO,controlmixed:
newplan8PMUlocalcounter-onlyreads,no executableHW yet. NoHW;DDRNOT_ADMITTED.
Evidence `evidence/pmu-writeonly-correction-2026-10-27`.
