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
