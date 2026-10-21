# Reconstructing the Genesys PS export

The local runtime still consumes a retained PS export. The source of that export
is Piotr's `boards/genesys_zu-5ev/0_platform/` Tcl flow, with the existing local
RTIO/CoreDMA variant settings. Do not substitute a generic Digilent preset:
Piotr's dynamic DDR/SPD boot path and the runtime's AXI wiring must be preserved.

The source-only remote reconstruction attempt is recorded in
`evidence/ps-source-export-2026-10-21/`. Its manifest pins the three input Tcl
files and source commit; `run.sh` holds the common Dell Vivado build lock for
the entire export. This attempt does not access hardware or replace any retained
PS export, SD package or qualified image.

## Export operation

In a fresh working directory containing the three pinned Tcl files, the job
runs Vivado2025.2 with:

```sh
vivado -mode batch -nojournal -log vivado.log \
  -source vivado_script.tcl -tclargs local-rtio-dma
```

Run new FPGA jobs on Dell under the shared lock described in
[REMOTE_VIVADO.md](REMOTE_VIVADO.md). Preserve `platform.xsa`, `mi_*.txt`,
`zynq_ultra_ps_e_0/` pin/interface/address/property reports, the generated XCI,
logs and exit code. The Migen importer consumes more than the XSA alone;
copying just `platform.xsa` does not reconstruct its full input tree.

## Acceptance sequence

1. Collect all output files with remote/local SHA-256 verification; confirm the
   Tcl inputs stayed unchanged. Keep failure logs if Vivado fails.
2. Compare all PS component parameter values against the retained export.
   Key requirements include M_AXI_GP0 enabled/32-bit, GP1/GP2 disabled,
   S_AXI_GP2 enabled/64-bit, PL0 requested125MHz, SD0 disabled, SD1 enabled
   on MIO39..51. Also inspect DDR, clocks, UART, GEM and other parameter changes;
   the short list is insufficient to approve an export.
3. Compare imported pin/interface/address reports semantically. Absolute paths,
   timestamps and XSA ZIP metadata may differ; retain these differences rather
   than treating whole-file hash differences as functional changes.
4. Generate local RTIO/debug HDL from the new export in a fresh directory with
   `build_rtio_debug.sh --generate-only`. Compare HDL/XDC/CSR/init with the
   qualified source-generated baseline. Review XCI changes explicitly, then
   normalize/synthesize the PS IP before choosing a pinned full-build input.
5. Generate SDT/PS initialization from the new XSA and compare with the retained
   qualified inputs. A matching PL alone does not prove matching PS startup.

No automatic acceptance is implied by successful export. Do not repoint normal
runtime profiles or release manifests before the relevant comparisons pass.
A changed configuration needs scoped qualification. A matching reconstruction
still does not establish latest-package cold boot or complete empty-host setup.
