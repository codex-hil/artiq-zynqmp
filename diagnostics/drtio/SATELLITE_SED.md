# Satellite packet to real SED simulation

The test connects the retained upstream `RTPacketMaster` to the port's
`CheckedRTPacketSatellite` over ideal 16-bit packet wires. The satellite drives
actual upstream `SyncRTIO`, its eight-lane/128-entry SED and `ttl_simple.Output`.
No synthetic CRI response backend is used. Original checkouts remain untouched.

Run from the repository root:

```sh
make test-drtio-satellite-sed \
  PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python \
  MISOC_SOURCE=/srv/codex-hil-data/artiq-zynqmp/reference/misoc-current
```

Four writes at timestamps 240, 272, 304 and 336 produce precisely four PHY
strobes at 249, 281, 313 and 345 and TTL edges at 251, 283, 315 and 347.
The test locks down the **uncompensated** SED pipeline latency of nine clocks
plus the TTL PHY's two clocks. Inter-edge spacing is preserved. Timestamp
alignment still needs deliberate latency compensation and validation; this is
not a claim of zero-latency or externally synchronized operation.

The disconnected-packet negative control executes identical master requests
with the satellite frame input forced low and requires no PHY strobes or TTL
edges. Both runs require no SED asynchronous errors.

Two output channels are instantiated (only channel zero is selected) because
the retained upstream ROMs cannot elaborate a one-entry address space with
this Migen. The normal eight-lane configuration avoids the same zero-width
counter issue seen with a reduced two-lane configuration.

All domains are deliberately mapped to one simulation clock. This validates
packet decoding, CRI dispatch, SED scheduling and TTL behavior only. GTH,
clock-domain crossings, recovered-clock synchronization, TSC loading, input
reads, reset handling and a remote Kasli remain separate acceptance steps.

## Time and underflow controls (2026-10-11)

The suite now has five passing tests:

- Original scheduling and disconnected-frame negative control.
- Sender-side timestamp advance of 11 clocks produces edges at exactly the
  requested 240/272/304/336 counter values. This is a diagnostic parameter,
  not a modification to production master semantics or remote synchronization.
- An actual serialized `set_time` packet loads 1000 exactly once; subsequent
  events use timestamps 1240/1272/1304/1336 and retain the measured latency.
- A stale timestamp-10 write is sent before the valid sequence. Real SED CRI
  underflow status asserts, the stale event produces no edge, and the four
  subsequent valid events execute normally without extra strobes or edges.

No compensation is applied to the upstream SED, PHY or standard master.
A final platform integration must choose a consistent time reference and
validate physical latency before changing timestamp conventions. These tests
establish local counter behavior, not master/satellite counter alignment.

## Real queue capacity and input reads

Seven tests now pass. The buffer-space test sends three serialized requests
around four queued writes and requires replies **128 → 124 → 128**. The values
come from the actual upstream SED FIFO occupancy logic, not a constant responder.
It also checks packet parsing and buffer-space timeout errors remain absent.

The input test replaces the spare output PHY with upstream `ttl_simple.Input`
connected to the simulated output pad. A serialized channel-1 write enables
rising-edge sensitivity, then channel-0 writes generate a pulse. The collector
captures exactly one rising event with data1 at timestamp253. A serialized read
returns that exact data and timestamp; a second read from the empty FIFO returns
native timeout (`no_event=1`, `is_overflow=0`). For an event response, the upstream
protocol explicitly leaves `is_overflow` unspecified, so it is not asserted.
The test requires no unknown/truncated packet errors.

The input synchronizer latency is included in timestamp253; no physical pin,
loopback jumper, recovered-clock or input-delay calibration is qualified here.

## Reusable backend (2026-10-13)

`SatelliteBackend(packet_link, output_pad, input_pad)` now owns the checked
packet parser, TSC, real SyncRTIO and TTL PHYs. All seven tests instantiate
this module directly. Channel0 is output; channel1 is input when supplied,
otherwise a spare output used by the negative controls. All internal domains
map to `sys`. An outer `ClockDomainsRenamer` can move the entire backend to a
recovered-clock domain; packet frame/data must be synchronous to that domain.
This is a laboratory backend, not a complete upstream DRTIOSatellite target.

Generate standalone Verilog with `make hdl-drtio-satellite-backend` using the
same Python/MiSoC arguments above and an `O` directory on the data volume.
Ports expose packet words, TTL pins, coarse counter and asynchronous errors.
Generation passed, but synthesis/routing and physical integration are pending.
The generator writes a scope manifest alongside the HDL.

Next integration must provide explicit common-reset handling and verified
transport CDC, preserve diagnostic error counters and use the shared bounded
Genesys load/test/restoration wrapper. AUX ResetRequest stays unsupported until
that reset path is implemented and physically validated.

## Receive-clock transport block — 2026-10-15

`SatelliteTransport` connects the existing decoded AuxEndpoint RT wires to
SatelliteBackend. RT packet parsing, TSC, SED and TTL PHYs run directly on
rtio_rx. This avoids using a free-running PS elastic buffer for request words.
The existing tested AuxTxCDC is reused at16-bit width/128-byte capacity to
cross whole RT reply packets from RX to gth_tx; link-layer TX retains native
RT priority over AUX. All three domains must share reset assertion.

RTPacketSatellite offers no TX backpressure. RTReplyCDC therefore admits a
packet only when idle, drops a busy arrival as a whole, and latches fault on
busy rejection or overflow/oversize. Fault is fatal for acceptance until a
common reset; it is in RX domain and needs synchronization before PS reads.
This is a bounded lab reply path, not a general lossless pipelined transport.

A Gray counter increments on actual packet.tsc_load at the same RX edge that
loads TSC. Its PS-side count can later gate genuine TSCAck; no ACK firmware or
new CSR has been added yet. AuxEndpoint now exposes its existing RX-domain
settled-ready signal without changing its logic.

Three offline tests PASS: one real time-load and scheduled TTL edge at1461
for timestamp1450 (existing11-cycle uncompensated SED/PHY latency); real buffer
replies128→127 across8ns RX/11ns TX and13ns PS clocks; busy reply rejection
without a partial second packet; and no TSC load/TTL/replies when RX is unready.
The notification is counted once per assertion, since its valid flag can span
several source-clock cycles. Distinct master source/RX clock names avoid old
Migen sequential clock-renaming aliases in the testbench.

Use `make test-drtio-satellite-transport` and
`make hdl-drtio-satellite-transport` with the same source/Python overrides as
above. Generated standalone HDL includes all three clock/reset interfaces and
a scope manifest. No board top integration, route/timing or hardware validation
is claimed. Next: integrate inside the AuxPS common-reset domains, expose/load
counter and fatal faults through CSR, then implement real TSC ACK and reset
semantics before accepting production AUX reset or destination-UP.
