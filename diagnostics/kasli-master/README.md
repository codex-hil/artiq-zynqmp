# Kasli v2.1 DRTIO test master

Standard Artix-7 Kasli v2.1, not Kasli-SoC. RTIO125MHz / DRTIO2.5Gb/s,
master role, WRPLL disabled, no EEM peripherals. SFP0 is Ethernet;
SFP1–3 are downstream DRTIO links. Local RTIO includes the user LEDs.
This test configuration does not replace an existing system's peripheral
JSON. Genesys satellite firmware and remote-link tests remain separate.

Use ARTIQ486e8f897547d282d46a02c30463449c21e30cfe (same host/protocol
snapshot as Genesys integration), Migenbeffe831bf1a691eaebf9ddbb4660f8b3e7fd964,
MiSoC0e99d28d88c25ca86b39d2452417cb500fc52abd, VexRiscv-verilog
2e4f43d72404a986c9d7251d9d543cf7aef077bc. Separate worktrees preserve the
original checkouts. Initialize the VexRiscv submodule in the MiSoC worktree.

## Build

Shared Vivado2025.2 must include Artix-7/XC7A100T support. The initially
installed ZynqMP-only device set cannot build Kasli. The minimal Nix shell
reuses pinned Rustnightly2021-09-01 and LLVM/Clang/LLD20 from ARTIQ's flake:

```sh
export ARTIQ_SOURCE=/srv/codex-hil-data/artiq-zynqmp/work/kasli-master
nix develop --impure --expr \
  'import /home/codex-hil/artiq-zynqmp/work/artiq-new-wip/diagnostics/kasli-master/tools-env.nix' \
  --command bash /home/codex-hil/artiq-zynqmp/work/artiq-new-wip/diagnostics/kasli-master/build.sh \
  /srv/codex-hil-data/artiq-zynqmp/build/kasli-master-rebuild
```

Override PYTHON, ARTIQ_HOST_SITE, MIGEN_SOURCE, MISOC_SOURCE or VIVADO for
another host. Python needs current sipyco plus Migen/MiSoC build dependencies.
The old Genesys Python environment alone has an obsolete sipyco; the script
uses the already installed host environment's packages. The local generated
Tcl includes checked first-stage CDC constraints for Vivado2025.2 without
modifying the shared Migen checkout. Two Vivado threads limit host load.

## Artifacts and deployment

Successful output tree: generated/genesys_drtio_master/gateware/top.{bit,bin},
software/bootloader/bootloader.bin, software/runtime/runtime.{elf,fbi};
artifacts.sha256 records hashes. Compile/route/timing success is distinct
from hardware validation, which requires the actual Kasli.

Generate the local master device database:

```sh
artiq-host artiq_ddb_template diagnostics/kasli-master/kasli-v2.1-master.json -o device_db.py
```

core_addr192.168.2.70 is a host-side placeholder, not an IP flashed into
network storage. Set the actual Kasli address/MAC/storage separately once
identified. For a future complete build, preview the flashing script with:

```sh
PATH=/srv/codex-hil-data/artiq-zynqmp/toolchains/kasli-openocd/bin:$PATH \
  artiq-host artiq_flash --dry-run -t kasli --srcbuild \
  -d /path/to/generated/genesys_drtio_master
```

Do not select an arbitrary USB device: identify the Kasli FTDI serial first,
then use artiq_flash's preinit selector. No Kasli has been flashed here.

## Current build status (2026-10-09)

BUILD_PASS_HARDWARE_NOT_RUN. Bootloader, ksupport, runtime, top.bit and top.bin
are complete. Vivado2025.2 synthesis, placement, routing and bitgen PASS.
Setup WNS0.141ns, hold WHS0.037ns, pulse-width slack0.264ns; no violating
endpoints. DRC before bitgen0 errors. The inherited upstream timing report
still flags external ports without delays, multiple-clock pins and the unused
sma_clkin_p clock source; build qualification does not establish physical
DDR/DRTIO performance or production constraint completeness.

OpenOCD+bscan-SPI was built from this same upstream flake and linked at
`/srv/codex-hil-data/artiq-zynqmp/toolchains/kasli-openocd`. Dry-run flash
script generation PASS, with no USB/JTAG or flash writes. First deployment
must identify the actual Kasli cable and back up its existing image/storage.

Outputs: `build/kasli-v2.1-master-2026-10-08/`, results.json and artifacts.sha256.
Packaged source-build layout:
`kasli-v2.1-master-125mhz-artiq10-test.tar.gz`. It uses ARTIQ10 snapshot486e8f8,
RTIO125MHz, WRPLL off and no EEM peripherals; substitute the real existing
system configuration before replacing a production Kasli master.

The initial device-support/token blocker was resolved by official offline
Add from the SMB installer. Evidence: evidence/artix7-install-2026-10-09.json.
The build script now emits both .bit and .bin; upstream's initial
-no_binary_bitfile option emitted only .bin. Existing route checkpoint was
used to export .bit without repeating synthesis or place/route.
