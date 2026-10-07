# Genesys ZU-5EV Ethernet diagnostic

This is a hardware golden test using maintained AMD emacps/lwIP code, not an
ARTIQ networking implementation. It keeps Piotr's PS configuration and FSBL
DDR/SPD patch. No new GEM or DMA driver was written. The tested firmware is
AArch64, AMD standalone secure EL3, GEM0 with TI DP83867 PHY at MDIO address 15.

Vendor versions from Vivado 2025.2: emacps 3.23, lwIP 2.2.0 (`lwip220_v1_3`),
xiltimer 2.3. Exact source and ELF hashes are in
`evidence/ethernet-build-2026-10-07.json`; original vendor files are unchanged.
`amd-2025.2-echo.patch` shows all changes to generated copies.

Build inside `vivado-container shell`:

```sh
scripts/build_ethernet_firmware.sh \
  /srv/codex-hil-data/artiq-zynqmp/build-vivado/fsbl-reproduced/sdt/system-top.dts \
  /srv/codex-hil-data/artiq-zynqmp/build-vivado/ethernet-new \
  /srv/codex-hil-data/artiq-zynqmp/toolchains/arm-gnu/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-elf
```

Use a fresh output directory. Output: `app/build/lwip_echo_server.elf` and
`artifacts.sha256`. This script was exercised from scratch in
`build-vivado/ethernet-reproduced` and its resulting ELF passed physical tests.
It reuses the SDT and toolchain from `scripts/build_boot_firmware.sh`.
No Vitis IDE, SDK or PetaLinux is required. The board MAC used in this test is
locally administered `02:38:3b:7f:02:0d`; choose another address for another
physical board. DHCP supplies the IP. Failure is explicit; the original
unchecked static-address fallback is removed.

The AMD example says TCP port 6001 in its header but binds port 7; we correct
the header. Its TI RGMII autonegotiation deadline is five seconds and checks
the timeout before the next PHY status read. On this board/switch, link
completed around the fifth iteration, so the unmodified example repeatedly
reported failure. We increase the deadline to 20 seconds and include the PHY
address in the log, preserving vendor initialization and clock programming.

## Physical repeatable test

Run on the host, with Genesys USB permissions already established:

```sh
make test-hw-ethernet-bringup \
  PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python \
  O=/srv/codex-hil-data/artiq-zynqmp/build-vivado/ethernet-suite \
  JTAG_SERVER=tcp:172.17.0.3:3121 JTAG_CABLE=210383B7F02DA \
  SERIAL=/dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0 \
  PMU_ELF=/srv/codex-hil-data/artiq-zynqmp/build-vivado/fsbl-reproduced/pmu-app/build/zynqmp_pmufw.elf \
  FSBL_ELF=/srv/codex-hil-data/artiq-zynqmp/build-vivado/fsbl-reproduced/app/build/zynqmp_fsbl.elf \
  ETHERNET_ELF=/srv/codex-hil-data/artiq-zynqmp/build-vivado/ethernet-reproduced/app/build/lwip_echo_server.elf
```

Resolve the current hw_server container IP; the URL above is the one tested.
The command resets only the selected board's PS, then starts PMU/FSBL and
waits for `Exit from FSBL`. It loads the echo diagnostic into initialized DDR,
reads the DHCP address from UART, verifies 20 lossless pings and the neighbor
MAC, verifies 1,080 byte-exact TCP exchanges across five connections, and reads
GEM TX/RX/error counters. Logs and JSON are saved under `O/ethernet-hardware`.
On success it leaves the diagnostic serving TCP port 7. It does not configure
PL or write flash. A PS reset changes PS clocks/reset state; RTIO probes must
restore the local-rtio configuration before their tests.

For packet-only testing of the already running diagnostic:

```sh
make test-hw-ethernet BOARD_IP=192.168.2.16 O=/srv/codex-hil-data/artiq-zynqmp/build-vivado/packets
```

The IP is a DHCP lease and can change; use the UART value. Full Ethernet
bring-up PASS is recorded in `evidence/ethernet-hardware-2026-10-07.json`.
It proves bidirectional packet I/O and GEM descriptor/DMA/cache handling for
these transfers. It does not establish RTIO DMA, ARTIQ RPC/management,
long-duration saturation reliability, or 10/100Mbps behavior.

## Warm-debug state and GIC

Processor-only JTAG reset retains interrupt-controller state. Switching from
the earlier EL1 non-secure diagnostic to the AMD secure EL3 standalone app
left interrupt groups and an outstanding interrupt in the GIC. We observed
TTC0 pending/active with running priority 0xA0 and a frozen DHCP tick counter.
Ending the known outstanding interrupt allowed ticks again, but the robust
repeatable procedure is a PS system reset before PMU/FSBL. The final firmware
has no manual GIC workaround; AMD interrupt handling runs correctly after
that reset. The reset runner guards the cable serial, avoiding other connected
FPGA boards. Do not interrupt a runtime IRQ handler and jump to another ELF
as a substitute for this flow.

Integration into ARTIQ remains the next software step. The validated vendor
GEM/lwIP path can serve as a reference and, if appropriate, an FFI backend;
this test avoids reimplementing AMD drivers in Rust before hardware validation.
