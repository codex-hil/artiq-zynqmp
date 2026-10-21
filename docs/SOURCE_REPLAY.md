# Replaying the verified Genesys source path

This is the order of the component steps exercised on2026-10-21. Use a prepared
Python/Rust/AMD environment, the pinned sources in
`diagnostics/release/genesys-local-sources.json`, and fresh output directories.
It is not an empty-host installer or a claim that every rebuilt firmware binary
is reproducible. Heavy FPGA work runs on Dell; hardware stays on the debug host.

## PS export and importer

From a checkout of `bringup/genesys` with its ARTIQ/Migen submodules initialized:

```sh
python3 scripts/remote_rtio_build.py prepare-ps \
  --source boards/genesys_zu-5ev/0_platform --job /large-disk/ps-job
python3 scripts/remote_rtio_build.py submit --job /large-disk/ps-job
python3 scripts/remote_rtio_build.py status --job /large-disk/ps-job
```

After completion:

```sh
python3 scripts/remote_rtio_build.py collect \
  --job /large-disk/ps-job --output /large-disk/ps-export
python3 scripts/prepare_ps_import.py \
  --export /large-disk/ps-export \
  --original-root /srv/nvme-fast-1/vivado-work/ps-job \
  --baseline /path/to/qualified-ps-export --output /large-disk/ps-import
```

The job basename determines its Dell directory. Successful export still requires
review; importer comparison covers PS values and reports. Review XSA member
changes and generate SDT using `scripts/generate_sdt.tcl` with `sdtgen` and the
board `system-user.dtsi`. Match its full file tree to the selected firmware's
SDT, not merely a subset of PS initialization files. See [PS_EXPORT.md](PS_EXPORT.md).

## HDL, normalization and full FPGA build

Set the explicit dependency paths documented in [BUILD_RECIPE.md](BUILD_RECIPE.md):

```sh
VIVADO_THREADS=8 bash scripts/build_rtio_debug.sh \
  /large-disk/ps-import /large-disk/hdl --generate-only
python3 scripts/remote_rtio_build.py prepare --source /large-disk/hdl \
  --job /large-disk/normalize-job --mode normalize
python3 scripts/remote_rtio_build.py submit --job /large-disk/normalize-job
```

After completion, collect and inspect the XCI diff. Normalization includes PS IP
synthesis; it does not authorize parameter changes. Select the exact reviewed
normalized XCI hash explicitly:

```sh
python3 scripts/remote_rtio_build.py collect --job /large-disk/normalize-job \
  --output /large-disk/normalized
python3 scripts/remote_rtio_build.py prepare --source /large-disk/hdl \
  --job /large-disk/pl-job --mode build \
  --normalized-xci /large-disk/normalized/ip/platform_zynq_ultra_ps_e_0_0/platform_zynq_ultra_ps_e_0_0.xci \
  --expected-xci-sha256 REVIEWED_SHA256
python3 scripts/remote_rtio_build.py submit --job /large-disk/pl-job
```

Collect only after completion. Collection performs strict input/timing/DRC/
routing checks; report PASS remains separate from hardware qualification.
`compare_bitstreams.py` separates raw FPGA configuration from .bit timestamps.
The exercised reconstructed export produces exactly the prior raw XCI/HDL,
and that configuration's physical candidate already has extended JTAG evidence.
A future changed output must be qualified within its actual scope.

## Firmware and release

Follow [CLEAN_BUILD.md](CLEAN_BUILD.md) for CPU0/CPU1 and boot firmware, preserving
Piotr's DDR initialization. Follow [CANDIDATE_JTAG.md](CANDIDATE_JTAG.md) for
bounded qualification and [SD_BOOT.md](SD_BOOT.md) for coherent packaging.
Rebuilt binaries must not be substituted into old qualified manifests merely
by changing their hashes. CPU1 currently compiles and passes physical tests but
is not byte-reproducible across build paths.

On the prepared host, the retained qualified artifact chain can be checked with:

```sh
make verify-local-release PYTHON=python3 \
  RELEASE_CONFIG=diagnostics/release/qualified-local-2026-10-21.json \
  RELEASE_REPORT=/large-disk/fresh-release-report.json
```

This command accesses files only. It verifies recorded proof bindings, source
input hashes, FPGA checks/equivalence, package roles and serialized boot payloads.
It does not write an SD card or qualify cold boot. The latest packaged runtime's
cold boot remains NOT_RUN; the board retains its documented restored baseline.
