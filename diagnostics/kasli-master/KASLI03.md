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
