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
