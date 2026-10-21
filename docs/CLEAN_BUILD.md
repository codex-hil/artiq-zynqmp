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
| CPU0 services | `scripts/build_debug_services.sh` | Matching `system-top.dts`, CSR map, GNU AArch64 toolchain and shared AMD BSP environment |
| CPU1 worker | `scripts/build_kernel_worker.sh` | Clean-worktree compile PASS as above; byte reproducibility unresolved |
| CPU1 cold-boot bridge | `scripts/build_sd_worker.sh` | Matching worker32 ELF; fresh release packaging pending |
| PMU/FSBL | `scripts/build_boot_firmware.sh` | Matching PS SDT and AMD sources, including Piotr's board-specific DDR work |
| Boot image | `scripts/build_boot_image.py` | Matching FSBL/PMU/PL/CPU0/CPU1 bridge and bootgen; packaging alone is not cold-boot proof |

These are existing component entry points, not yet a verified end-to-end script.
Read the shared Vivado environment instructions before FPGA work. Neither Vitis
IDE nor PetaLinux is needed for this laboratory runtime. A recursive checkout of
all historical PetaLinux submodules is unnecessary for the CPU1 recipe above.

Next steps: identify remaining binary differences; rebuild CPU0 and the SD bridge
from a clean checkout; record matching inputs for the complete release chain.
Only then package and separately qualify the new image on hardware under the
shared board lease. Do not overwrite the qualified baseline during build work.
