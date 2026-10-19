# KASLI03 removal checkpoint — 2026-10-19

KASLI03 v1.1, DNA `0x0048458a64b04854`, is the tested master. Genesys ZU-5EV
`210383B7F02DA` is the direct destination1 leaf. Existing SFP connection and
Genesys JB1→JB2 jumper were used. No EEM modules are qualified by these tests.

| Check | Result | Evidence |
|---|---|---|
| Native master management, counter kernels, external reset/TSC handshake, TTL loopback | PASS | `evidence/kasli-final-regression-2026-10-19/session/results.json` |
| Same-kernel DMA upload exception, exact recording cursor restoration, subsequent physical DMA | PASS, 8 edges | Same regression |
| Physical TTL stability across widths/periods | PASS, 4096 edges / 2048 pulses | `evidence/kasli-final-stability-2026-10-19/session/results.json` |
| Forced GTH link reset/reinitialization/TSC ACK, then physical TTL | PASS, two cycles | Same stability session |
| Repeated fragmented native DMA trace lifecycle | PASS, 9 plays / 522 edges | `evidence/kasli-final-long-dma-2026-10-19/results.json` |

All three completed sessions restored the Kasli SRAM diagnostic and reviewed volatile
clock profile, and restored Genesys normal local core at192.168.2.3 with local
TTL/DMA/analyzer/MonInj/Ethernet checks. The last session also finished with restoration PASS. All four shared leases
were verified available and released; KASLI03 is ready for removal. Flash and OTP are untouched.
The restored SRAM diagnostic is not persistent: a power cycle starts whatever
was already present in the board's preserved flash.

The prepared-host recovery package is under
`/srv/codex-hil-data/artiq-zynqmp/releases/kasli-handoff-2026-10-19`.
It contains pinned FPGA/runtime/firmware/restore images, exact configuration and
commands, source archive, host cursor overlay, revisions and physical logs.
It is not a standalone toolchain installer. Shared Vivado/Python/NAC3/Nix/Rust and
reference/submodule checkouts are separate dependencies; consult the main README
and PORTING_STATUS. SHA256SUMS and archive checksum are finalized after the last
session. Credentials and license files are excluded.

On the existing prepared host, use a fresh output directory:

```sh
make review-drtio-qualified O=/large-disk/fresh-review
make test-hw-drtio-qualified O=/large-disk/fresh-hardware
```

Review the generated command/profile and current network/USB identity first.
Always use the existing all-board lock/identity/restoration wrapper. Do not
program flash to reproduce a SRAM-only test. Do not substitute another Kasli
without its own identity/clock restoration qualification. The three Kasli lock
names protect ambiguous no-serial USB identification; other boards are untouched.

The newer active-DMA-underflow experiment, delay gate, telemetry firmware and
independent counter design have compile/RTL tests only. They were not loaded
for this removal checkpoint. Absolute link phase, jitter and deterministic
latency remain unmeasured. This is a qualified laboratory direct-leaf subset,
not full production DRTIO/Sinara qualification.

Without Kasli, local Genesys RTIO/DMA/debug testing and offline firmware/gateware
work can continue. External master/satellite interaction, link recovery and new
remote timing/fault experiments require Kasli or another separately qualified
master to be connected again.
