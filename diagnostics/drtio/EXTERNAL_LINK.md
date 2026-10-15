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
