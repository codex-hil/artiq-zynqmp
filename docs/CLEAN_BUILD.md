# Clean-checkout build checkpoint

On 2026-10-21 the CPU1 kernel worker was built successfully in two separate
clean detached worktrees and fresh output directories, using the installed
open-source toolchains. This validates this component's build recipe on this
host. It does not establish a complete clean-host build, bit-identical output,
a new bootable image, or hardware qualification of the rebuilt workers.

## CPU1 recipe

```sh
git clone --branch bringup/genesys https://github.com/codex-hil/artiq-zynqmp.git
cd artiq-zynqmp
# Supply the shared verified tools and the CSR map of the matching PL image.
export RUSTUP_HOME=/path/to/rustup
export KERNEL_REMAP_PATHS=1
bash scripts/build_kernel_worker.sh \
  /path/to/abi-tools /path/to/fresh-output /path/to/matching/csr-map.json
```

Use Rust 1.87.0 with the `armv7-unknown-linux-gnueabihf` target. The tool directory
is prepared by `scripts/setup_abi_tools.py` from the exact Ubuntu packages and
SHA-256 values in `scripts/abi-tools.json`. It supplies LLVM/Clang 19, ARM GCC
and binutils without changing host packages. Cargo uses the committed lockfile;
the test used the existing Cargo cache, not an empty dependency cache.

`KERNEL_REMAP_PATHS=1` canonicalizes Rust source/output paths. It is optional;
historical qualified images use their original recipe. Outputs include
`worker32.elf`, `start64.elf`, `rtio_csr.h` and `artifacts.sha256`.

Evidence in `evidence/kernel-clean-build-2026-10-21` includes build logs, source
revision, tool-manifest and lockfile hashes, exact ELF and PT_LOAD comparisons.
Path remapping removed absolute checkout strings, but the two workers still
had 62 differing loaded bytes. An additional fixed Rust metadata experiment
also failed to make the images identical and was reverted. Do not infer binary
or behavioral equivalence from successful compilation. The qualified existing
worker remains selected by the hardware profiles.

## Remaining release chain

| Component | Existing entry point | External input / remaining qualification |
|---|---|---|
| PS and initial DMA PL | `scripts/build_rtio_dma.sh` | Vivado 2025.2, initialized Migen/ARTIQ dependencies; fresh release-chain build pending |
| Analyzer/MonInj PL | `scripts/build_rtio_debug.sh` | Matching verified PS DMA export; recipe reuses generated PS IP |
| CPU0 services | `scripts/build_debug_services.sh` | Clean-worktree build and six service tests PASS; existing SDT and shared AMD BSP environment reused |
| CPU1 worker | `scripts/build_kernel_worker.sh` | Clean-worktree compile PASS as above; byte reproducibility unresolved |
| CPU1 cold-boot bridge | `scripts/build_sd_worker.sh` | Fresh build PASS; embedded worker segment verified byte-exact |
| PMU/FSBL | `scripts/build_boot_firmware.sh` | Matching PS XSA and AMD sources, including Piotr's board-specific DDR work |
| Boot image | `scripts/build_boot_image.py` | New CPU0/CPU1 package PASS with qualified existing FSBL/PMU/PL; cold boot NOT_RUN |

These are existing component entry points, not yet a verified end-to-end script.
Read the shared Vivado environment instructions before FPGA work. Neither Vitis
IDE nor PetaLinux is needed for this laboratory runtime. A recursive checkout of
all historical PetaLinux submodules is unnecessary for the CPU1 recipe above.

Next steps: identify remaining binary differences; rebuild CPU0 and the SD bridge
from a clean checkout; record matching inputs for the complete release chain.
Only then package and separately qualify the new image on hardware under the
shared board lease. Do not overwrite the qualified baseline during build work.


## CPU0 and SD packaging checkpoint — 2026-10-21

A clean detached worktree at `58f1e93` built CPU0 services and the SD bridge.
The worker input came from the path-remapped build at `35518ff`; the metadata
experiment in the later source revision affects only the CPU1 build script,
which was not used in this CPU0/bridge run. Exact revisions and hashes are in
`evidence/release-package-2026-10-21/results.json` and `artifacts.json`.

```sh
bash scripts/build_debug_services.sh \
  /path/to/matching/system-top.dts /path/to/debug/csr-map.json \
  /path/to/fresh-cpu0 /path/to/aarch64-gnu-toolchain
bash scripts/build_sd_worker.sh \
  /path/to/abi-tools /path/to/worker32.elf /path/to/fresh-bridge
python3 scripts/build_boot_image.py \
  --fsbl /path/to/matching/zynqmp_fsbl.elf \
  --pmufw /path/to/matching/zynqmp_pmufw.elf \
  --bitstream /path/to/debug/top.bit \
  --worker-boot /path/to/fresh-bridge/worker-boot.elf \
  --application /path/to/fresh-cpu0/amd/app/build/lwip_echo_server.elf \
  --output-dir /path/to/fresh-package
bootgen -arch zynqmp -read /path/to/fresh-package/boot.bin pht
```

Local output is `build/release-sd-package-2026-10-21/boot.bin` under the shared
artifact root. Partition headers were read back successfully. The CPU1 bridge
contains the exact worker payload at `0x20200000`, with its EL3 startup at
`0x20000000`. All 33 original worker CSR registers are preserved by the selected
debug PL map. No new PL, PMU or FSBL build was performed here.

This package is a candidate, not the selected hardware baseline. No card was
written and no cold boot was performed. Remaining release work includes the
CPU1 reproducibility diagnosis, complete source/tool provenance for reused
inputs, and a separately authorized hardware qualification window.


## Candidate consistency and provenance checks

Before selecting a candidate, verify all package input/output hashes against
its recorded manifest and bind reused PL/FSBL/PMU to their exact roles in the
qualified profile:

```sh
python3 scripts/verify_release_package.py \
  --package /path/to/fresh-package \
  --baseline-profile diagnostics/drtio/profiles/kasli04-genesys-native-dma.json \
  --output /path/to/fresh-report.json
```

This command is offline and refuses to overwrite a report. Current candidate
passes; `evidence/release-package-2026-10-21/role-consistency.json` records it.
Tests reject changed applications/boot images, incomplete manifests, unpinned
baseline inputs and swapped FSBL/PMU roles. This verifies local consistency,
not trust in a modified manifest, BIF/ELF compatibility or cold boot.

The provenance report in that evidence directory pins the original PS XSA,
SDT and GNU toolchain manifest and confirms the built FSBL board-specific DDR
source matches the tracked source. Provenance remains partial: the complete
source state of the original PS/PL build and installed AMD sources has not
been reconstructed into an immutable release manifest.

A scratch single-codegen-unit experiment also compiled twice but did not
produce identical loaded bytes. It did not change the tracked kernel recipe;
see `evidence/kernel-codegen-repro-2026-10-21`. Byte reproducibility remains
an open release-quality item and does not invalidate earlier physical results
for the separately pinned qualified baseline.


## Source inventory

`evidence/release-sources-2026-10-21/manifest.json.gz` contains the current
installed AMD `embeddedsw` inventory: 84,410 files, 1,438,248,478 bytes, plus
symlink/directory entries. It also records clean Git identities for the CPU0
source worktree, initialized ARTIQ and Migen checkouts. Summary and archive
checksums are in the adjacent `results.json`.

To capture another source state without building or touching hardware:

```sh
python3 scripts/capture_release_sources.py \
  --git port=/path/to/clean-source \
  --git artiq=/path/to/initialized/artiq \
  --git migen=/path/to/initialized/migen \
  --tree amd-embeddedsw=/path/to/installed/embeddedsw \
  --output /path/to/fresh-source-manifest.json
```

Tree entries include content hashes, sizes and modes; symlinks are recorded
without following their targets. Git entries identify commits and hash tracked
patches; untracked files are explicitly excluded. Capture external untracked
inputs as separate `--tree` arguments. Ordinary concurrent modification of a
file during hashing is rejected, but the command is not an atomic filesystem
snapshot: keep source trees idle throughout capture.

This closes the present-day installed-source inventory gap. It does not prove
that these files were unchanged during an older build. Rebuilding old PS/PL and
boot firmware against a captured source state is still required for a complete
release provenance chain. The existing hardware baseline remains unchanged.
