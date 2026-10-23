AXAU15 clock-only bringup — physical PASS 2026-10-23
=================================================

Exact cable Digilent JTAG-HS1 210512180081, FPGA xcau15p IDCODE04AC2093.
Shared lease: /home/codex-hil/.cache/alinx-210512180081.lock.
The earlier Xilinx Platform Cable points to XC7S15 and must not be used here.

This diagnostic uses only system clock T24/U24 and USER1 JTAG. The200MHz input
is divided by2; a registered Gray counter crosses to the JTAG domain through
two ASYNC_REG stages. Source-period max-delay and bus-skew constraints bound
that crossing. Readback signature is0x41583135. Three counter deltas passed;
host timing makes this an activity check, not precision frequency measurement.
Unused pins are configured PULLNONE. No FMC outputs, SPI, GTs or RF control.

Build top.v/build.tcl on Dell in a fresh directory under the global Vivado lock.
The final20261023c build passed routing/bitstream: WNS8.548ns,WHS0.046ns,
zero unconstrained endpoints, DRC0 checks, CDC32 safe/0 unsafe. Earlier builds
are retained remotely: a failed endpoint selector; b needed INTERNAL_TCK clock
coverage correction. Only final c was programmed. See evidence/axau15/
clock-probe-20261023 relative to the prototype root.

Run run_hardware.py BIT --sha256 VERIFIED_SHA --output NEW_ABSOLUTE_DIRECTORY
on Optiplex only after reviewing timing/DRC and matching input/artifact hashes.
It validates the cable and FPGA, holds its lease, exposes only that USB node to
a temporary server, programs volatile SRAM, checks readback and stops its server.
JTAG is6MHz, constrained for10MHz. Original sources/Trenz are not imported.
The caller must keep the probe files under /srv/codex-hil-data (container mount).

Final state: volatile clock probe running. Power cycling removes this diagnostic;
no flash/EEPROM/OTP/eFUSE writes were made. No AD9172 identity, clock-init, JESD,
RF, Ethernet or UART service is provided by this image. The scope was untouched.
Next step is separately qualified SPI-only gateware and AD9172 identity/profile;
the prior AD9173 warm-clock initialization is not AD9172 qualification.
