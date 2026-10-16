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

## Asynchronous native decoder/CRI engine (offline)

`AsyncSatelliteDMA` now composes the running sys-clock memory guard, raw FIFO,
upstream RecordSlicer, TimeOffset and CRIMaster. Decoder/CRI run on rtio_rx and
share the queue's extended read_reset. The raw FIFO carries a separate EOP bit.
After the native zero-length trace marker, a synchronized finish stops memory
streaming; AXI drains, then a terminal FIFO token lets the native decoder flush
and the CRI master finish. Completion/error payload is held stable until reset;
the sys side waits two extra edges after synchronized completion before capture.

Byte address and time offset are latched at accepted start; the offset settles
through synchronization before queue readiness permits memory reads. Busy
starts are rejected. Invalid128-byte alignment is rejected before any AXI AR.
The caller must supply the qualified64-bit memory interface and keep sys alive.
Status error bits are internal flags, not a direct native AUX status encoding:

| Bit | Meaning |
|---:|---|
|0|Aborted trace|
|1|AXI read-response error|
|2|Native CRI underflow|
|3|Native destination-unreachable|
|4|Unaligned start|

A PS abort resets the FIFO/decoder while memory independently drains. The RX
`rtio_reset_request` output **must** be connected to the actual SED queue reset
alongside its other reset sources. This cancels already-enqueued future events;
it preserves output PHY state, so it cannot undo a level transition which has
already fired. New start releases that hold only through the fresh reset epoch.
The clock-pause test first queues actual future CRI writes, pauses RX, drains
on abort, resumes, verifies no cancelled TTL edges, then plays a fresh trace.

Six engine tests (four full-path and two admission cases) pass on each ARTIQ source variant: both clock-rate orders,
precise fine3 TTL/time offset, native underflow snapshot/recovery, AXI error/
recovery, pause-after-enqueue abort/recovery, bad alignment and busy admission.
Existing memory CDC and packet/SED/reset regressions also pass.
`generate_dma_memory.py --engine --output DIR` emits standalone AXI/control/CRI
RTL with Xilinx reset primitives. The physical Genesys target and firmware
remain unchanged; no Vivado/hardware/DDMA protocol claim is made.

Before live use: map CSRs and the PS memory port; add and check Gray/bundled-data
constraints; implement native AUX trace admission/storage/lifecycle and CRI
ownership; validate trace records, bounds/arena/prefetch padding and watchdogs.
This engine has no trace-length limit and invalid/missing terminators can keep
reading until explicit abort. Consumer completion means events admitted, not
that every scheduled pin transition has fired. No arbitrary concurrent packet
commands or active firmware ownership changes are qualified here.

Clock loss needs an external sys-domain fault/abort request. This engine does not
infer loss of a clock merely from backpressure; without abort it may wait for RX.

## PS AXI/CSR control and bounded reads (offline)

`DMACSR` places the asynchronous engine behind MiSoC registers, tested through
the actual AuxPS32-bit AXI bridge and CSR bank4 (base0xa0002000). Configuration
is shadowed; accepted start latches byte address, offset, read budget and sys
watchdog. Real Genesys PS port/GT/SED wiring is not added by this peripheral.

Default trace arena is0x22000000–0x22200000,128-byte aligned. Start requires an
aligned address, a positive budget of at least four128-byte bursts, the entire
read window inside the arena, positive watchdog, no external fault, idle engine
and no unacknowledged result. Fault defaults asserted until explicitly wired.
This reuses the normal core's documented arena only in a separate exclusive
image/session; it does not coexist with the normal core's trace allocator.

The memory guard reserves three outstanding request opportunities when stopping
on budget so **all** issued128-byte bursts fit the requested window, including
the terminating drain request. Fourteen fast/blocked-memory subcases test limits
1,2,3,4,5,16,32 with short invalid limits rejected before any AR. Zero remains
an unlimited low-level laboratory mode, but DMACSR rejects it. Guard budget
failure aborts the decoder and drains memory; it cannot be cleared into a new
active read until the old AXI epoch has finished. Idle launch clears that fault.

Watchdog expiry requests abort and then waits for AXI drain. It never resets
an unresponsive memory interface to manufacture completion. A missing AXI
response remains a fault requiring system-level recovery. Trace record/length
validation and valid padding are still firmware duties; hardware budget bounds
reads even if native decoding cannot reach a terminator.

Register protocol:

1. Configure address, time_offset, max_bursts, watchdog using MSW-first32-bit
   words for multiword fields. Positive watchdog is in sys clocks.
2. Write start=1; check accepted/active or sticky reject reason.
3. Poll pending, then read stable result_error/channel/timestamp and completed.
4. Write clear=1 while idle before another start. It cannot erase an active run.

Result error bits0–4 keep engine meanings; bit5 is watchdog expiry and bit6 is
read-budget exhaustion. Reject bits0–6 are busy, alignment, arena window, burst
budget, zero watchdog, fault, unacknowledged result. Counters are32-bit wrapping.

Five PS AXI tests cover high/low-word underflow timestamp snapshot, pending-result
protection, invalid inputs with no memory access, watchdog/drain/restart and
missing-terminator budget/drain/restart. The test target supplies CRI status;
actual SED/TTL playback is covered by the separate full-engine tests. The fifth
case holds CRI busy and confirms PS start/clear/shadow writes cannot mutate the
active epoch; four cases are repeated against both ARTIQ source variants.
`generate_dma_csr.py --output DIR` emits standalone PS AXI+memory AXI+CRI HDL and
its exact csr-map.json. No physical CDC constraints, actual PS pin connection,
AUX trace allocation or Vivado/hardware acceptance are implied.

```sh
make test-drtio-dma-csr test-drtio-dma-read-budget \
  PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python \
  MISOC_SOURCE=/srv/codex-hil-data/artiq-zynqmp/reference/misoc-current
```

## Optional Genesys target wiring (2026-10-16)

`diag_gateware.py --satellite-dma` implies satellite/AUX mode and generates
PS HP0 64-bit memory AXI wiring with every PS signal width checked. Bank4 at
0xa0002000 exposes the bounded DMACSR, with its immutable DDR arena recorded
in csr-map.json. The memory guard stays on PS sys during GT reset/loss; only
the RX decoder/SED side follows recovered-clock reset. A synchronized active
level selects the native CRISwitch before the FIFO warmup finishes. Firmware
must keep packet traffic quiescent throughout DMA ownership, including return.

DMA abort resets actual SED queues while preserving PHY/TSC. Fault holds DMA
when the link is reset/down, no TSC load has been observed, explicit RTIO/PHY
reset is requested, or reply/RTIO errors are latched. This is target wiring,
not an AUX DDMA upload/playback service or a hardware-qualified image.

The generated implementation script deliberately stops with an error until
DMA Gray and bundled-data CDC constraints are implemented and checked. The
manifest reports383 first-stage bits/10 Gray buses for the current legacy
source configuration; it explicitly marks DMA physical constraints pending.
Do not remove that guard merely to obtain a bitstream. The qualified default
DIO target and board baselines remain separate.
