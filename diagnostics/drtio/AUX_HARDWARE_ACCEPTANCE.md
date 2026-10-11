# Bounded AUX hardware acceptance

This checklist is the next physical acceptance scope, not evidence of PASS.
Use only verified Genesys cable210383B7F02DA and the shared board flock
`/home/codex-hil/.cache/genesys-210383B7F02DA.lock`. Hold that lease over
all UART/JTAG/DAP/network accesses, resets, diagnostic loading, tests and
normal-runtime restoration. If unavailable, perform offline work.

Prerequisites:

- `check_top_build.py` PASS for the AUX bitstream, including matching map
  SHA-256, retained synchronizer count, bus skew and timing closure.
- Complete known-good local CoreDMA/analyzer/MonInj restoration artifacts.
- Exact-board identity established before reset; both A53 cores halted for
  DAP-owned AUX tests. No concurrent firmware or host accesses to the ring.
- Keep external SFP TX disabled and use GTH internal PMA loopback2.
  Do not write Si5342, SD, boot flash, OTP or another board.

Required observations:

1. Verify monitor magic0x44525430 before writes. Configure PRBS off and
   reset/release GT; bound ready polling to10 seconds. Check CSR in_reset
   clears and rx_up asserts. Record GT/clock status.
2. Write/read TX SRAM first/last words via HPM0. Verify AUX length readback
   for4,12,68 and1024 bytes. Avoid intentionally issuing invalid DAP AXI
   transactions until PS exception/timeout recovery has a separate test.
3. Send at least10 patterned packets covering those sizes, including one
   maximum packet per GT reset. Wait for both upstream TX enqueue-busy
   and bridge_busy to clear. RX present must assert within10 seconds;
   validate every payload word at RX8192+read_pointer*1024. Pop exactly once.
   Require zero RX errors, no extra RX packet and correct pointer wrap.
4. Without popping, send8 short packets. Require RX overflow flag, seven
   preserved readable packets and no overwrite of those payloads. Drain,
   clear the flag and verify a fresh packet succeeds.
5. Reset while a maximum packet is being enqueued. Require cleared TX,
   bridge and RX state, bounded re-alignment, and exact fresh packet receive.
   Repeat at leastthree complete GT reset/test cycles. This is the first
   physical check of coordinated abort/reset; RTL's functional reset model
   alone does not qualify assertion/release timing or stopped-clock behavior.
6. Always attempt normal-runtime restoration in a finally block. Confirm
   actual DHCP address from UART, then run standard physical TTL/CoreDMA,
   analyzer/MonInj and Ethernet acceptance. Record restoration failures
   explicitly; do not leave a diagnostic loaded and claim task completion.

Save scripts, logs, maps, hashes, per-case sizes/pointers/errors and restoration
results. Raw byte AUX loopback does not establish firmware CRC/protocol,
discovery/routing, a remote Kasli link or deterministic DRTIO latency.
