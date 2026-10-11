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
there is no connected satellite RTIO backend. After self-test the current firmware enters a persistent minimal responder:
echo is answered and destination status reports DOWN. ResetRequest is dropped
by this responder until a real RTIO reset backend exists. It ignores incoming
reply packets, preventing self-generated loopback response storms.

Use wrapper `--firmware ELF --service-test` for persistent-service acceptance.
The UART laboratory injector commands are e (echo), d (destination), c (bad
CRC), u (unknown type), r (unsupported reset). Three rounds of those commands
and final echo recovery verify18 injected requests, nine responses, nine
ignored loopback replies and three drops for each negative control. These
commands only inject laboratory AUX packets; they are not production UART
management. UART load/command/read is covered by the same board lease.

Physical persistent-service acceptance PASS; evidence:
`evidence/aux-service-hardware-2026-10-11.json`. The UART injector and responder
still share one A53 and the physical GT loopback. Remote-link acceptance,
RTIO/SED/TSC/reset and routing remain pending.

Current normal core restored192.168.2.3; physical TTL/CoreDMA/debug and
Ethernet regression PASS. Evidence: `evidence/aux-firmware-hardware-2026-10-11.json`.
Remote Kasli, routing/discovery, TSC synchronization and production satellite
RTIO/SED remain unimplemented/unqualified.
