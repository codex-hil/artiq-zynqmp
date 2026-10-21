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

## 2026-10-21 reconstruction result

Export exit0; all168downloaded files hash-verified and the three Tcl inputs
unchanged. All component/model/project/runtime parameter values match the old
PS XCI. All pin/interface/address/property reports match byte-for-byte. Fresh
Migen generation from a separately relocated importer view reproduces HDL,
XDC, CSR and all initialization files byte-for-byte.

All PS initialization files inside XSA also match byte-for-byte. The only
uncompressed member differences are timestamps in `platform.hwh`, `xsa.xml`
and `xsa.json`; full differences are retained in the evidence directory.
The original downloaded tree remains unchanged. `import-relocation.json`
records the one path-list relocation in the separate local importer view.

This closes source reconstruction of the retained PS export. It does not
claim a fresh normalized PS synthesis, complete rebuilt release or generated
SDT equivalence. Existing qualified manifests remain unchanged. Next check:
generate SDT from the new XSA and compare PS initialization/device-tree outputs
before assembling a source-regenerated release.

## SDT and downstream input equivalence

SDT generation from the reconstructed XSA completed successfully using the
existing shared2025.2 `sdtgen`, `scripts/generate_sdt.tcl` and the unchanged
board `system-user.dtsi`. All37output files match the qualified firmware's
SDT tree byte-for-byte, including PS initialization and device-tree includes.
See `evidence/ps-source-sdt-2026-10-21/` for input/tool hashes, invocation,
log and the complete file comparison.

The relocated raw XCI emitted by fresh HDL generation also exactly matches
`source-hdl-clean-release-2026-10-21`, the input already used by the reviewed
PS synthesis and full Dell FPGA build. Thus the source reconstruction connects
to that existing build proof without another identical synthesis. This is
input equivalence, not a new tool or hardware run. Existing package manifests
still pin the original qualified binary artifacts. Complete empty-host tool
bootstrap, firmware binary reproducibility and latest-package cold boot remain
open independently.

## Reusable remote export commands

The existing remote job tool now stages PS exports without a manual upload:

```sh
python3 scripts/remote_rtio_build.py prepare-ps \
  --source boards/genesys_zu-5ev/0_platform --job /path/to/fresh-ps-job
python3 scripts/remote_rtio_build.py submit --job /path/to/fresh-ps-job
python3 scripts/remote_rtio_build.py status --job /path/to/fresh-ps-job
python3 scripts/remote_rtio_build.py collect --job /path/to/fresh-ps-job \
  --output /path/to/fresh-collected-export
```

Preparation is offline and pins only the three Tcl sources and runner. Submission
rechecks those hashes before transfer and uses the shared Dell build lock.
Collection requires a completed job, downloads all regular output files except
`.Xil` cache files, verifies their hashes and preserves failed-job logs.
Successful export still reports `PS_EXPORTED_REVIEW_REQUIRED`; it does not
waive the parameter/HDL/SDT comparisons above. Absolute importer paths remain
unchanged in the downloaded evidence: relocate only a separate copied import
view, preserving the original and recording the change.

The new collector was exercised against the existing completed source export:
168files verified, no duplicate Vivado run. Evidence:
`evidence/ps-export-automation-2026-10-21/`. Three new controls cover offline
preparation/changed input rejection, missing/linked inputs and incomplete outputs.

## Verified importer view and PS comparison

```sh
python3 scripts/prepare_ps_import.py \
  --export /path/to/collected-export \
  --original-root /srv/nvme-fast-1/vivado-work/ORIGINAL_JOB \
  --baseline /path/to/selected-qualified-export \
  --output /path/to/fresh-import-view
```

The tool verifies the collected receipt and input indices, refuses missing,
changed or linked files and external IP references, then compares PS parameter
values and exported text reports with the selected baseline. Parameter/report
differences stop preparation. Omitting `--baseline` only prepares a verified copy;
it makes no configuration-equivalence claim.

Only pinned files are copied. `mi_xci_files.txt` is rewritten in the fresh copy
and `import-view.json` records the original/new references. The downloaded tree
is never edited. Point `build_rtio_debug.sh --generate-only` at that new view.
This compares PS export values/reports; it does not replace XSA metadata review
or SDT comparisons. A receipt is consistency evidence, not signed provenance.

The actual2026-10-21 export passed this tool and fresh Migen generation:
all16generated inputs match the previous relocated export byte-for-byte.
Three admission tests PASS. Evidence: `evidence/ps-import-automation-2026-10-21/`.
