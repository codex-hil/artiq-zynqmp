# Genesys local runtime build recipe

This recipe connects the component entry points exercised during bring-up. It
keeps HDL generation separate from Vivado and preserves Piotr's PS/DDR work.
It requires the documented source/tool environments and an existing matching
PS export; it is not a complete empty-host bootstrap or a single verified
end-to-end release command. Every output directory must be fresh.

## 1. Check out and select sources

```sh
git clone --branch bringup/genesys https://github.com/codex-hil/artiq-zynqmp.git
cd artiq-zynqmp
git submodule update --init -- common/artiq common/migen
```

`diagnostics/release/genesys-local-sources.json` pins the HDL source set actually
used, including ARTIQ, Migen, MiSoC and LiteX. Supply MiSoC and LiteX checkouts at
those commits and the existing Python environment. The host compiler/NAC3 and
firmware Rust toolchains have their own documented pins in ARTIQ_HOST.md and
CLEAN_BUILD.md; do not update them implicitly when generating gateware.

## 2. Generate HDL on Optiplex

```sh
export ARTIQ_SOURCE=/path/to/artiq
export MIGEN_SOURCE=/path/to/migen
export MISOC_SOURCE=/path/to/misoc
export LITEX_SOURCE=/path/to/litex
export PYTHON=/path/to/hdl-venv/bin/python
export VIVADO_THREADS=8
bash scripts/build_rtio_debug.sh \
  /path/to/matching-ps-export /path/to/fresh-hdl --generate-only
```

`generation.json` records Python/source identities, tracked patch hashes,
original PS IP hashes, the42first-stage CDC registers and generated input hashes.
No Vivado invocation occurs in this mode. The PS export is an explicit input,
not regenerated or modified here. The script retains its original local full
build mode when `--generate-only` is omitted; use the remote backend for new
heavy builds.

A clean checkout at24e04e4 reproduced `top.v`, `top.xdc`, `csr-map.json` and all
init files byte-exactly against the physically tested baseline. The Tcl differs
only in maxThreads2→8. XCI metadata differs: exact changes are retained in
`evidence/source-hdl-generation-2026-10-21/xci-differences.json`. Component
parameter values are unchanged, but that does not prove identical Vivado upgrade
behavior. Do not silently replace or accept a mutated XCI.

## 3. Build PL on Dell

Follow [REMOTE_VIVADO.md](REMOTE_VIVADO.md): transfer only the pinned generated
inputs into a fresh job directory and use the common remote build lock. Record
the exact XCI selected as input. The evaluated candidate uses the explicitly
post-upgrade pinned XCI recorded in `evidence/dell-vivado-2026-10-21/pinned-ip-rebuild`.
A fresh unnormalized XCI requires separate normalization/diff review before
claiming an unchanged-input build. The reusable `scripts/remote_rtio_build.py` automates preparation, submission
and collection; XCI diff review remains an explicit step.

Retrieve the new bitstream/reports/CSR map and input files, verify remote/local
hashes, then run `scripts/check_remote_rtio_build.py`. Timing/report PASS is
separate from hardware qualification. The candidate already passed physical
checks; changing inputs creates a new candidate requiring scoped revalidation.

The complete fresh-source path above passed on2026-10-21. See
`evidence/source-release-chain-2026-10-21/remote-build/results.json` and
`source-build-payload-comparison.json` in the same evidence directory. The
resulting raw FPGA configuration bytes exactly match the JTAG-qualified
candidate; only the .bit header time differs. No new hardware test was run.
This equivalence does not close the external PS-export/bootstrap or latest SD
cold-boot gaps, and the existing package still pins its original qualified .bit.

## 4. Build matching firmware

Use the same CSR map throughout. Refer to [CLEAN_BUILD.md](CLEAN_BUILD.md) for
exact tool setup and full invocation examples:

```sh
export RUSTUP_HOME=/path/to/port-rustup
bash scripts/build_kernel_worker.sh ABI_TOOLS FRESH_WORKER MATCHING_CSR_MAP
bash scripts/build_debug_services.sh MATCHING_SYSTEM_TOP_DTS MATCHING_CSR_MAP \
  FRESH_CPU0 AARCH64_GNU_PREFIX
vivado-container shell /path/to/source/scripts/build_boot_firmware.sh \
  MATCHING_PS_XSA FRESH_BOOT_FIRMWARE AARCH64_GNU_PREFIX
bash scripts/build_sd_worker.sh ABI_TOOLS FRESH_WORKER/worker32.elf FRESH_SD_BRIDGE
```

The current worker has a buildable clean-source recipe and physical test PASS,
but builds in different paths are not bit-identical. Preserve the actual hashes.
BSP/FSBL/PMU regeneration must use matching PS configuration; Piotr's DDR source
is applied by `build_boot_firmware.sh`. Firmware builds use open-source Rust/GNU
compilers and AMD's BSP tooling in the shared container, without Vitis IDE or
PetaLinux.

## 5. Package and qualify

`scripts/build_boot_image.py` packages the matching PL, FSBL, PMU, CPU0 and SD
bridge. Preserve its `artifacts.json`, BIF, source manifests and partition-header
readback. The integrity verifier binds reused artifacts to exact qualified roles;
it intentionally rejects newly built unqualified replacements against an older
profile. Do not change that profile merely to make verification pass.

[The bounded candidate JTAG wrapper](CANDIDATE_JTAG.md) qualifies new inputs under
the board lease and restores the old baseline. Its initial and extended hardware
sessions passed. A packaged image still requires a separate cold SD boot test;
this recipe does not write cards, flash or OTP.

Remaining automation: complete source-to-package orchestration; remote job
submission/normalization/collection now has a reusable tool, with its first
source normalization queued for validation. The source HDL regeneration result closes the
fresh HDL checkpoint; original PS generation and empty-host provisioning remain
explicit dependencies rather than implied successes.

The final artifact assembly now has `make package-local-candidate`, binding
JTAG-qualified input hashes and the SD worker payload; see SD_BOOT.md. This
closes candidate packaging automation, while end-to-end source orchestration
and cold-boot qualification remain distinct open steps.

## Offline verification in one command

For the retained2026-10-21 artifacts on this host:

```sh
make verify-local-release PYTHON=python3 \
  RELEASE_CONFIG=diagnostics/release/qualified-local-2026-10-21.json \
  RELEASE_REPORT=/path/to/fresh/release-verification.json
```

The configuration contains explicit host-local paths; select matching retained
artifacts when using another host. No Vivado, network, board access or bootgen
is invoked. The command rechecks the extended hardware proof's binding to all
candidate/restoration artifacts, strict source-build inputs/timing/DRC/routing,
raw configuration equivalence, package role hashes, embedded tested worker,
BOOT.BIN hash and serialized CPU0/CPU1 partition payloads. Any failed check
prevents a PASS report. Existing reports are never overwritten.

`LOCAL_RELEASE_CHAIN_PASS_COLD_BOOT_NOT_RUN` confirms offline consistency.
It does not establish signed provenance, an empty-host build, fresh hardware
execution, serialized FSBL/PMU/PL equality, BSS initialization or cold boot.
The recorded configuration and report live under
`evidence/source-release-chain-2026-10-21/combined-verification.json`.
Run `make test-local-release` for negative proof/role/configuration controls.
