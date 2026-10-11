# Upstream AUX codec and A53 laboratory firmware

This reuses unchanged ARTIQ `drtioaux_proto.rs`, `libio` and its CRC library.
It does not reimplement the packet enum or serialization in C. `lib.rs`
provides a small C ABI and the established padding/CRC envelope; `firmware.c`
handles volatile PS/PL MMIO, UART and a bounded laboratory scenario.

Both original Piotr ARTIQ1461cf9 and current upstream486e8f8 produce identical
seven basic wire vectors. Host tests check roundtrips, corrupted CRC,
truncated data and unknown types. This proves those vectors, not compatibility
of all newer AUX protocol variants.

Build in the existing workspace (outputs must live on the data disk):

```sh
python3 diagnostics/drtio/aux_protocol/build_vectors.py \
  --artiq-source /path/to/artiq \
  --output /srv/codex-hil-data/artiq-zynqmp/build/aux-reference
python3 diagnostics/drtio/aux_protocol/build_firmware.py \
  --artiq-source /path/to/artiq \
  --csr-map /path/to/passing-aux-build/csr-map.json \
  --output /srv/codex-hil-data/artiq-zynqmp/build/aux-firmware
```

Dependencies are locked. The existing Rust1.87 target aarch64-unknown-none
builds the no_std static library; existing GNU AArch64 tools and AMD BSP
link the ELF. Paths to the shared BSP/tools are explicit in the builder.
The original libio still requires never_type; RUSTC_BOOTSTRAP is scoped to
these subprocesses, with no upstream source edits. Host uses cargo+stable.
A missing `extern crate core` needed by the old failure derive was fixed in
our host harness. No firmware dependency migration is claimed.

Run hardware only through `scripts/test_drtio_aux_bringup.py`, using its
normal diagnostic/known-good restoration arguments plus:

```sh
--firmware /path/to/aux-firmware/aux-firmware.elf
```

It validates bitstream/map hashes, acquires the shared Genesys lock, loads
PS/PL, runs PHY and SRAM loopback tests, then loads CPU0 firmware and captures
UART. Finally it restores normal PL/CPU0/CPU1 and validates local TTL/DMA,
analyzer/MonInj and Ethernet before releasing the lease. The firmware helper
requires that inherited lease and verifies ELF/map hashes before CPU access.

Physical acceptance2026-10-11 PASS:31 request/reply exchanges through real
GTH PMA loopback, bad CRC, unknown type and final echo recovery. Both roles
run on one A53. ResetAck only acknowledges this laboratory handler; it does
not reset production satellite RTIO. Destination status replies DOWN because
there is no connected satellite RTIO backend. After success this firmware
idles; it is not a persistent autonomous remote-facing AUX service.

Current normal core restored192.168.2.3; physical TTL/CoreDMA/debug and
Ethernet regression PASS. Evidence: `evidence/aux-firmware-hardware-2026-10-11.json`.
Remote Kasli, routing/discovery, TSC synchronization and production satellite
RTIO/SED remain unimplemented/unqualified.
