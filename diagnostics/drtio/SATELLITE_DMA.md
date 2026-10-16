# Satellite DMA integration

## Qualified offline path

`SatelliteBackend(..., dma_membus=bus)` optionally instantiates the existing
M-Labs AXI DMA adaptation in `boards/genesys_zu-5ev/1_gateware/zynqmp_dma.py`
and native upstream `cri.CRISwitch`. Owner0 is the serialized RT packet engine;
owner1 is DMA. Both drive the same actual SyncRTIO/SED/TTL backend. The default
backend still connects packets directly, so the qualified DIO hardware target
has not acquired a DMA instance or a new memory interface.

The simulation drives real AXI ready/valid memory responses with outstanding
same-ID bursts and backpressure. It proves packet→DMA→packet→DMA ownership at
idle boundaries, precise TTL edges, fine3 timestamps and a nonzero DMA time
offset. A stale trace produces the native underflow error; explicit error
clear and another aligned trace recover without phantom TTL events. AXI must
fully drain before handing ownership back. Observed drain waits are519–520
simulation clocks; the initial400-cycle test budget was insufficient, and the
final test retains a bounded1500-cycle deadline.

Run:

```sh
make test-drtio-satellite-dma \
  PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python \
  MISOC_SOURCE=/srv/codex-hil-data/artiq-zynqmp/reference/misoc-current
```

The same test can set `ARTIQ_SOURCE` to the preserved contemporary ARTIQ
checkout. `generate_satellite_backend.py --dma --fine-ts-width 3 --output DIR`
emits standalone same-clock RTL with AXI AR/R and explicit control/status ports.
Those ports are not a PS CSR map or a routed Genesys bitstream.

## Required before hardware or distributed DMA claims

- PS/PL memory and clock integration. The same-clock laboratory input is not a
  PS AXI CDC bridge. The recovered RX clock can stop or reset; an AXI memory
  transaction must not be abandoned when that happens. Keep memory-side state
  on a running clock or implement/prove safe isolation and draining first.
- Native switch ownership is firmware-managed, just like upstream satman. Only
  idle, transaction-free handoffs are tested. Pending input reads, concurrent
  packet commands, ownership changes during DMA and active queue/link reset
  need explicit rejection/quiescence policy and negative tests.
- DMA engine state intentionally is not driven by RTIO queue reset. Resetting
  it while AXI reads are outstanding could abandon PS transactions. This is a
  requirement to resolve, not a qualified active-reset implementation.
- This64-bit AXI reader uses16-beat bursts: trace bases must be128-byte aligned.
  Upstream satman/dma.rs uses ALIGNMENT64, which cannot be reused unchanged for
  this interface. All simulated traces use valid0/512-byte bases.
- Reuse native AUX DmaAddTrace/RemoveTrace/Playback and PlaybackStatus packets,
  bounded allocation/fragment validation, cache coherency and native status
  semantics. No success replies may precede actual trace admission/playback.
- Validate memory reader/CDC/ownership first, then run a normal Kasli CoreDMA
  distributed recording and timestamped playback against physical TTL loopback.

No Vivado build, programming, PS/DDR access, AUX DMA trace transfer or remote
DMA experiment was performed for this optional path. The last qualified board
state remains the restored local runtime described in PORTING_STATUS.md.


## Running-clock memory drain and raw-word CDC (offline)

`DMAMemoryGuard` reuses the existing DMAReader. The AXI side remains on sys.
Start/finish/abort are sys-domain pulses/levels; abort suppresses consumer data,
turns off further streaming and accepts/discards remaining read beats until the
native terminal EOP. Done requires all accepted bursts to finish. It does not
reset AXI state. Starting while active is rejected/latched; starting with abort
asserted is rejected. sys must remain clocked and out of reset until done.

`DMARawCDC` provides a separate AsyncFIFOBuffered raw64-bit queue to rtio_rx.
Both FIFO domains share coordinated reset, independently of the AXI reader.
Reset must span a sys edge. Assertion holds until seven RX edges acknowledge
reset settling; writing waits for fresh read readiness and old reset ACK to
clear. Merely observing read-ready zero after one RX edge was insufficient:
the short-reset negative control exposed16 phantom zero words. The corrected
control passes that test. Downstream decoder/CRI must use `read_reset`, whose
assertion remains held even when the external reset request has ended.

Always pair an interrupted queue epoch with guard.abort; queue reset alone is
not a cancellation of outstanding reads. A normal raw end marker will require
the decoder to request finish, drain memory, and coordinate the next queue epoch.
Those decoder/CRI control connections are the next step, not implemented here.

```sh
make test-drtio-dma-memory   PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python   MISOC_SOURCE=/srv/codex-hil-data/artiq-zynqmp/reference/misoc-current
```

Nine tests pass on each preserved ARTIQ source variant. The clock-loss test
postpones actual RX clock-driver transitions inside Migen's simulator while sys
continues; it confirms no RX progress during the pause, AXI drain, and fresh-only
data after resume. This remains simulation with the existing functional reset
model. It does not qualify physical clocks or reset-release timing.
`generate_dma_memory.py --output DIR` emits standalone Xilinx-reset RTL; neither
Gray-bus physical constraints nor a PS/board target have been added. No hardware
access occurred. Evidence: `evidence/dma-memory-offline-2026-10-16`.
