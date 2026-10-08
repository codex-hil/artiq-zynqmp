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
artiq-host artiq_flash --dry-run -t kasli --srcbuild \
  -d /path/to/generated/genesys_drtio_master
```

Do not select an arbitrary USB device: identify the Kasli FTDI serial first,
then use artiq_flash's preinit selector. No Kasli has been flashed here.

## Current build status (2026-10-08)

Bootloader, ksupport and master runtime compile/link PASS. Generated headers
confirm DRTIO_ROLE=master and RTIO_FREQUENCY=125.0. Gateware is blocked by
missing Artix-7 support in shared Vivado. AMD's installed-tree Add action
rejects the expired authentication token; token renewal was requested.
Selective offline packages (117 archives, ~2.47GB including installer files)
were fetched from the original SMB installer and cached for the Add action.
No successful Kasli bitstream or physical DRTIO link is claimed.
