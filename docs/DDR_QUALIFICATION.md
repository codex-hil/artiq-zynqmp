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
