# DDR qualification plan

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
