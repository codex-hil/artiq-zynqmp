# KASLI03 master handoff

Accepted 2026-10-13 from rng-rpi `kasli/HANDOFF_KASLI03_ARTIQ.md`.
Read that handoff before deployment. User reports the Kasli loopback removed
and an SFP connection to Genesys attached. Exact downstream Kasli port awaits
operator confirmation; no remote link claim follows from this handoff.

Read-only identification PASS under all three shared Kasli locks:
DNA `0x0048458a64b04854`, XC7A100T, USB001:077, topology1-6.2.
UART channelC by-path `pci-0000:00:14.0-usb-0:6.2:1.2-port0`.
Evidence copied to `evidence/kasli03-handoff-2026-10-13/`.
No SRAM, flash or clock-profile modification performed during takeover.
Locks were released after identification.

## Image preparation

Use `kasli-v1.1-master.json`, master role, RTIO125MHz/DRTIO2.5Gb/s,
no EEM peripherals, WRPLL disabled. Preserve EEM9/10 high-Z. This is a
separate build from the earlier v2.1 image: never load that earlier image
onto this board. ARTIQ source remains pinned at486e8f897547d282d46a02c30463449c21e30cfe.

The common build script accepts `KASLI_CONFIG=/absolute/path/to/config.json`
and reads its variant rather than assuming v2.1. The current build output is
`/srv/codex-hil-data/artiq-zynqmp/build/kasli-v1.1-master-2026-10-13/`.
Build started, completion/timing acceptance pending. No hardware lock is held
for the offline build.

## Deployment gates

- Review routed setup/hold/pulse timing, DRC, part and image/firmware hashes.
- Establish a RAM-only firmware path. Upstream bootloader attempts flash boot
  before network boot. Do not run unknown previous flash firmware; prepare a
  controlled netboot-only bootloader overlay or verified RAM loader first.
  Keep original sources and flash storage unchanged.
- Confirm current USB topology and exact DNA immediately before SRAM loading.
- Acquire all required shared Kasli locks nonblocking. A cross-board session
  must also hold the Genesys lock, acquired in lexical order, for the whole
  load/test/restoration period, including both UARTs and network traffic.
- Use the handed-over checked SRAM restoration procedure. Si5324 initialization
  by ARTIQ is volatile but must be recorded and its restoration addressed.
- Use unique network identity. The default master device_db IP is only a
  placeholder, not board configuration or evidence of connectivity.

Genesys currently has a validated local core and laboratory internal-loopback
AUX services. The extracted real satellite backend has seven simulation tests
and generated HDL; a routed external satellite transport/reset/CDC integration
is still pending. Do not claim remote discovery, TSC synchronization or remote
TTL execution from the current state.

## Build checkpoint

Original v1.1 build completed: bitstream/bootloader/runtime PASS. Setup
WNS0.001ns, hold WHS0.061ns, pulse slack0.264ns; no violating endpoints.
Very small positive setup slack and inherited external timing warnings require
hardware qualification. Bit SHA256322910c4441297ad4757f0cd33bcf3d3bdf11e6f6e657394c28ba7b7d0dce7b4.
This flash-first image has not been selected for deployment.

`prepare_netboot_source.py` creates a separate detached worktree at the exact
pinned upstream revision and checked boot/network overlays. It disables the
flash-boot branch, fixes unique lab MAC02:4b:03:48:48:54, selects DHCP and
removes inherited static addresses/routes. No EEPROM/flash writes are introduced.
The reviewable overlay is `kasli03-netboot.patch`; the original source remains
unchanged. Upstream volatile clock initialization is retained, not yet tested
on this board.

Netboot-only build is running in `build/kasli03-netboot-2026-10-13` on the data
volume. Initial overlay compilation found a shadowed untyped None; this was
corrected before restarting the build. Firmware/bitstream acceptance pending.

## Bounded bootloader-only acceptance

`scripts/test_kasli03_netboot_hw.py` is prepared but NOT_RUN. It requires a
reviewed netboot-only qualification JSON plus exact bit SHA and passing timing.
`--dry-run` checks files only. Actual execution holds all three shared Kasli
locks; verifies USB topology and DNA before SRAM loading; captures exclusive
UART; requires bootloader CRC, SDRAM initialization/memory test, disabled flash
boot and the unique DHCP identity. It does not upload runtime or touch Genesys,
so no Si5324 runtime initialization is performed by this stage.

After any programming attempt it restores the handed-over full-checker image
with its existing guarded loader and checks UARTBone identity/EEMenable0/
GTPcontrol0/SFPTXdisable7 with bounded reads before releasing the locks.
This is not remote DRTIO or even runtime acceptance. Runtime clock changes need
a separate restoration plan before that later test.

The interrupted foreground build was restarted as the user systemd service
`artiq-kasli03-netboot-20261013.service`; check ActiveState/ExecMainStatus and
`systemd-build.log` in the netboot output directory. It runs a frozen build
script snapshot, holds no hardware locks and performs no device operations.

## Bootloader networking correction

Source inspection confirmed the upstream bootloader does **not** start a DHCP
client. `IPv4=use_dhcp` in its console is the selected configuration policy,
not a lease or proof of IPv4 connectivity. The runtime has its own networking.
The netboot-only image can listen on IPv6 link-local
`fe80::4b:3ff:fe48:4854` (derived from the forced lab MAC), TCP4269; the host
must provide the actual switch-facing interface scope. No IPv6 connection
has been tested yet. A separate static IPv4 profile would require a rebuild.
The startup wrapper checks `Waiting for connections...` but reports DHCP
as not implemented and does not claim network acceptance from that console.

The upstream wire format is `F`, four-byte big-endian runtime binary length,
raw runtime.bin payload, `OK`, then `B` to request execution. runtime.fbi has
an extra header and is not the raw netboot payload. Do not send runtime until
its clock configuration/restoration and shared hardware lease are addressed.

`qualify_netboot_build.py --build BUILD --source SOURCE --output JSON` checks
the exact upstream revision and reviewed overlay, selected bootloader path,
v1.1 master config/part, timing summary/violating endpoints, DRC severity,
completion marker and all firmware/bitstream hashes before issuing the
qualification required by the hardware wrapper. Negative control using the
completed original flash-first build was correctly rejected for selecting the
wrong bootloader source. Positive netboot qualification awaits routing.

## Failed deployment and correction — 2026-10-13

The first netboot-only qualification was insufficient and is **withdrawn**.
The built bootloader was not embedded: standard Kasli CPU reset points at flash
0x400000. SRAM loading therefore ran the existing 2024 MiSoC bootloader, passed
its DDR tests, then started old ARTIQ8 `VOR2309003` from flash. That runtime
configured Si5324 internal125MHz and reported lock/reboot. No flash programming
commands were issued, but flash content was not re-read after this test.

The bounded test correctly failed its required netboot UART checks. Its finally
path restored full-checker SRAM and verified identity/EEM0/GTP0/SFPdisable7.
Exact original Si5324 registers were not captured/restored; do not describe the
clock profile as unchanged. Raw UART and results are in
`evidence/kasli03-netboot-hardware-2026-10-13/`.

Corrected source is the separate `work/kasli03-bram-netboot` worktree. Build uses
`KASLI_ROM_SIZE=131072`: MiSoC resets CPU at zero and removes the SPI-flash core.
ARTIQ's builder needs a local initialization hook because the generic MiSoC
hook loads `software/bios/bios.bin`, while ARTIQ builds `bootloader.bin`.
The checked overlay initializes ROM words from the compiled bootloader and
records reset address/ROM size/hash in `bram-boot.json`. Flash boot code is
removed from this no-flash laboratory image, not merely hidden behind a branch.
Qualification and the hardware wrapper now require this embedded-ROM evidence.
The old image negative control is rejected for lacking it.

Corrected build is running as `artiq-kasli03-bram-netboot-20261013.service`,
output `build/kasli03-bram-netboot-2026-10-13`. No corrected image has been loaded.
Next physical test remains bootloader-only; runtime clock restoration is a
separate acceptance step. Original sources and prior artifact/log trees remain.

The first integrated-ROM attempt exposed upstream runtime assumptions:
unconditional SPI-flash imports/reload/FLASH_BOOT_ADDRESS do not compile when
MiSoC omits the flash core. This is not solved by claiming a complete runtime.
For the bounded next test, the BRAM builder intentionally compiles only the
bootloader; the qualifier marks bootloader-only scope and does not require
runtime artifacts. Runtime support without flash remains a separate offline
implementation step. Corrected firmware and actual ROM initialization PASS;
`bram-boot.json` generated. FPGA routing remains pending.

## Embedded bootloader hardware PASS

Routed BRAM image SHA4fb33ce837d29cfe727e97c6e0e5cd86f761b7b60c8800c26eb35a5891a99715,
WNS0.092/WHS0.051/pulse0.264ns. Qualifier now also compares the complete
`mem.init` word sequence to compiled bootloader bytes and checks generated HDL
reset-zero and ROM initialization wiring. Positive qualification PASS.

Physical SRAM boot PASS: 2026 upstream bootloader, CRC, DDR initialization and
memory test, disabled flash boot, correct forced MAC and network listener startup.
No runtime uploaded, old flash runtime absent from UART, no Si5324 setup observed.
First host assertion falsely rejected hyphen-separated MAC; corrected to match
actual upstream display and repeated full load/test/restoration PASS.
Both sessions restored full-checker and CSR baseline under all three shared
Kasli locks. Raw evidence in `evidence/kasli03-bram-netboot-hardware-2026-10-13`.
Network TCP connectivity and remote DRTIO remain NOT_RUN.

## Flash-free runtime compile PASS

`prepare_flashfree_runtime.py` creates a separate worktree from the reviewed
BRAM overlay, enables runtime compilation, and guards upstream SPI-dependent
imports/functions with has_spiflash. In no-flash builds, management flash/reboot
return Error and panic halts; upstream configuration returns NoFlash. Flash
builds retain their original behavior. The reviewable patch is
`kasli03-flashfree-runtime.patch`. First overlay shape check caught duplicate
local/remote function names; the corrected script changes only local handlers.

Full bootloader/ksupport/runtime compile PASS in
`build/kasli03-flashfree-runtime-2026-10-13/generated-fixed`. Generated mem.rs,
csr.rs and regions.ld are byte-identical to the physically tested BRAM image.
Runtime hardware NOT_RUN. Evidence kasli03-flashfree-runtime-build-2026-10-13.json.
Next: establish host-scoped IPv6 netboot connectivity and a bounded runtime
clock-profile capture/restoration plan before firmware execution.
