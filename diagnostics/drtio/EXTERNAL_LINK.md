# External Kasli–Genesys link observation

The KASLI03 local kernel/RPC milestone is physically validated. External
DRTIO synchronization is still NOT_RUN. The existing ProtocolProbe validates
its own fixed payload and must not be used as a payload-error detector for
real Kasli traffic.

`link_observer.py` is a separate receive-only building block. It uses the
existing raw20 codec, comma aligner and upstream LinkLayerRX, then counts
RT/AUX words and rising frame boundaries with Gray counters crossing to PS.
Enable it only after receiver/alignment/descrambler settling; discard initial
acquisition counts. Counters wrap modulo2^32. Disable and drain CDC before
comparing totals. Enable does not reset counters. A frame crossing the enable
boundary may contribute words without a new frame count.

It has no connected transmitter or AUX responder. The codec's encoder is
unused. It does not validate packet contents, CRC, invalid 8b10b symbols or
running disparity; upstream software decoder exposes no validity output.
Comma acquisition and traffic counters alone must never be labelled link-up,
remote discovery, synchronization or deterministic latency.

## Integration gates before physical use

1. Add a separate observer diagnostic top mode, CSR map and exact generated
   synchronizer/Gray-bus constraints. Default external TX disabled; PRBS off.
   Reset the RX domain/aligner on transceiver reset or lost readiness; current
   aligner latches its first offset and cannot reacquire without reset.
2. Generate/routinely qualify a fresh bitstream with timing, CDC and hashes.
   Use the existing156.25MHz Si5342 output for initial observation; do not
   change clock-cleaner profiles in this stage.
3. Extend one bounded parent wrapper to acquire Genesys and all three Kasli
   locks in sorted nonblocking order before any UART/JTAG/network/reset.
   Validate exact DNA/cable/UART topology. Existing child loaders rely on the
   parent's lease; they must not acquire a second conflicting flock.
4. Parent loads the Genesys observer with A53s halted and enables external RX
   (loopback0), leaving Genesys optical TX disabled. Then perform reviewed
   KASLI03 BRAM boot/two-upload runtime startup. Capture master UART, both
   downstream port status and Genesys LOS/presence/clock/alignment snapshots.
   Do not guess which Kasli downstream port is cabled from old USB topology.
5. Require bounded settled observations and counter deltas. A silent RT stream
   can be normal without remote traffic; this stage proves only what is
   observed. No replies means AUX timeout is expected, not satellite success.
6. Finally restore Kasli full-checker and reviewed23-register Si5324 profile,
   then normal Genesys PL/CPU1/CPU0 and normal TTL/DMA/debug/network suite.
   Hold every lease until restoration completes, preserving failure evidence.
   No flash/SD/OTP writes. If any device is busy, release partial claims and
   continue offline; never replace it with another attached FPGA.

After reception is established, wire the real satellite RTIO/SED and persistent
AUX service before accepting ResetRequest or reporting destination UP. TSC,
routing and remote physical TTL require separate tests.

## Observer top integration — 2026-10-15

`DRTIO_OBSERVER=1 diagnostics/drtio/build_top.sh PS_EXPORT PHY_EXPORT FRESH_OUTPUT`
selects the independent observer mode. Use the existing Genesys RTIO/DMA PS
export and raw20 final156 PHY. It is mutually exclusive with protocol/packet/
AUX modes. CSR bank3 exposes observer enable/alignment/four counters. TX_DISABLE
is hardwired high, regardless of monitor_tx_enable. TX data is zero; CSR reset
defaults select external RX and PRBS off. Use monitor_reset around mode changes.

A separate observer_rx clock domain shares GTH RX clock and asynchronously
asserts reset on PS reset, monitor reset, or lost RX PMA/resetdone/user-clock
active. This clears alignment and counters; each readiness reset starts a new
measurement epoch. Optical LOS alone is not in that reset condition: the host
must reject LOS samples and assert monitor_reset before reacquisition.
Observer enable is in PS/sys domain and survives an RX-only reset; disable it
while reacquiring and settling the decoder before taking deltas.

Generated HDL preflight PASS:252 first-stage CDC bits and seven32-bit Gray
buses, each with exact-count synthesis guards/bus-skew constraints. A separate
RX reset simulation PASS verifies counts clear and alignment reacquires.
Full route/timing validation is still pending; this top has not been loaded.
First route attempt was stopped after HDL checks caught ineffective reset
assignments to CSRStorage.storage. Corrected code sets storage_full.reset;
the abandoned build must not be used for hardware.

## Bounded external session

The existing `scripts/test_kasli03_netboot_hw.py` accepts
`--genesys-observer CONFIG.json` together with its reviewed runtime/clock inputs.
The configuration supplies server, port (exact Genesys UART serial), ps_export,
bitstream, csr_map, restore_bitstream, worker, cpu0, device_db, artiq_python and
artiq_run paths, plus explicit network_interface. Preflight requires timing-qualified observer artifacts/hashes
and all restoration files before acquiring hardware. `external_session.py` is
not a standalone hardware tool: the Kasli parent holds all four board leases.

After both identities are selected, Genesys observer loads first; Kasli then
starts its reviewed RAM runtime. The observer resets/reacquires external RX,
settles, records four500ms-spaced samples, disables counting and retains optical
TX hard-disabled. Acceptance requires present module, no LOS, PHY readiness,
comma alignment and RX clock approximately matching independent PS125MHz clock.
It is reported as RX_CLOCK_AND_COMMA only. Idle/no RT/AUX frames can be normal
without a returning optical signal; no packet/CRC/discovery success is inferred.

Finally the parent restores Kasli diagnostic/clock and Genesys normal dual-CPU
runtime. Genesys restoration validates normal physical TTL/DMA/analyzer/MonInj
and Ethernet under the same leases. Any failed observation remains failed after
successful restoration. Four offline controls cover counter wrap/idle traffic,
LOS, absent module, wrong clock and recording restoration failures.
