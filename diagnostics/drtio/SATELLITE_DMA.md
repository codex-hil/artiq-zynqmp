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

The initial HDL-only checkpoint deliberately blocked implementation pending
DMA CDC constraints. The following implementation-check stage replaces that
guard with exact constrained groups and routed endpoint checks. The manifest
reports383 first-stage bits/10 Gray buses for the current legacy configuration.
The qualified default DIO target and board baselines remain separate.

### DMA CDC implementation checks

The DMA variant now generates six exact source/first-stage groups from emitted
HDL, including two5-bit Gray pointers and held64/2/24/64-bit payloads. Missing
or ambiguous source/assignment/width rejects generation. Held source registers
are deliberately preserved, including constant bits of this TTL-only target,
so synthesis cannot silently shrink the checked payload contract.

The164 data synchronizer endpoints are excluded from the general first-stage
false path and receive8ns datapath-only maximum-delay and8ns bus-skew limits.
Other first-stage synchronizers retain the existing false path. The RTL launch
and completion settling intervals remain necessary; these constraints alone do
not make arbitrary changing multibit data coherent.

Build with `DRTIO_SATELLITE_DMA=1 diagnostics/drtio/build_top.sh PS PHY FRESH_OUT`.
The build checker requires all six exact post-synthesis checks and14 passing
bus-skew groups (10 Gray plus4 held payload). The wrapper automatically runs
the following routed check before accepting the build; it can also be repeated:

```
python diagnostics/drtio/check_dma_cdc.py FRESH_OUT
```

This opens only the routed checkpoint and requires a real timed path to each
of164 first-stage endpoints, with8ns requirement and nonnegative slack. Missing, nonnumeric
or false-pathed endpoints reject qualification. The final build check verifies
the hashes of the checkpoint, HDL, map, manifest and endpoint TSV, so an old
PASS cannot qualify changed artifacts. Reports/TSV and
`dma-cdc-results.json` are implementation evidence, never hardware evidence.

## Cold-release integration correction (2026-10-16)

The initial routed DMA image3ee1173c... fails AUX startup: idle no-TSC admission
fault forwarded into engine.abort also reset SED, preventing the cold-release
step preceding AUX TX/TSC. Do not reuse it. DMACSR now gates fault-driven abort
by active epoch; a fault still rejects idle launches without memory access.
Actual AuxPS/SED before/after regression and active-fault-after-AR drain/restart
passed both source revisions. Fixed bitstream rebuild/physical retest pending;
implementation timing PASS alone did not establish working firmware startup.

A prepared `examples/kasli_drtio_dma_diagnostic.py` uses synchronous host RPC to
arm the native DDR reader and reads physical JB1/JB2 timestamps via Kasli. Its
host helper requires the parent's inherited board lease, qualified artifacts,
exact diagnostic arena, full2048-byte readback and bounded completion/error
checks. The trace opens/closes input sensitivity itself and contains4 pulses
of8000mu width/80000mu period. The epoch is30s ahead of master TSC so the bounded
25s host command completes before execution. Native RecordSlicer decoding and
experiment compilation passed; wrapper integration and physical use NOT_RUN.
This tests PL DDR DMA, not standard AUX DDMA upload/playback. Native AUX DDMA
service, record validation/allocation and post-abort packet handoff are pending.

## Physical cold release and first DDR attempt (2026-10-16)

Fixed imagee0fd4389... passed cold release/TSC load, two native resets and two
physical DIO kernels (8 rises each,100000mu spacing). Normal Genesys and Kasli
baselines were restored and checked. Host-armed DMA is now an optional guarded
external-session stage (`host_dma_test`), requiring a previous successful
cold-release/DIO/restoration report bound to the exact bit and firmware hashes.
A report from a failed or different image is rejected before hardware access.

Two DDR attempts with that image failed safely before physical pulse acceptance.
Instrumented evidence proves full2048-byte DDR readback and exact address,
offset, burst-budget and watchdog CSR readback. Result65 is abort+read-budget
exhaustion, not a successful trace. The16-burst allocation was unchanged.
A model accepting70 queued requests reproduces65 with the former unlimited
AR speculation; the previous model's3-request queue hid this integration case.

DMAMemoryGuard now wraps the reused reader with4 outstanding AR credits. RLAST
handshake returns a credit; valid/ready are gated together only on admission.
All accepted responses still drain. The cumulative read-window budget remains
independent and unchanged; no fake completion or error masking. High-acceptance
short/full diagnostic trace tests and all prior abort/error/reset checks must
pass before the rebuilt image is used. Performance is not qualified.

The full-trace test counts CRI commands on RX rather than sys; otherwise a
13ns RX command was sampled twice on some10ns sys edges. The resulting native
command sequence must be input gate,8 output events and input gate close.
Physical DDR playback and post-abort packet handoff remain NOT_QUALIFIED until
rebuild/routing/CDC and new guarded physical sessions complete.


## Physical credit-limited DDR playback (2026-10-16)

Credit4 image `40dac1f7a5875d015f6df00aefcaa618204ffc86d7f95280d9f636a9d337568c`
passed routed implementation and all164 individually timed CDC endpoints
(minimum slack7.265ns against8ns). The exact image first passed guarded
cold AUX/TSC/reset/DIO qualification and full baseline restoration.

The subsequent host-armed physical playback returned error0, accepted1,
completed1, active0, pending1, no rejection, no RTIO/PHY reset and no asynchronous
or reply fault. All2048 DDR bytes were read back before arming. The cumulative
budget remained16 bursts with4 outstanding read credits.

The standard Kasli kernel captured eight physical JB1→JB2 edges: four pulses,
width8000mu and period80000mu. First edge minus programmed offset was1000120mu.
This difference is an observation for this diagnostic, not calibrated phase,
jitter or deterministic-link-latency qualification. Evidence is
`evidence/kasli03-ddr-credit4-hardware-2026-10-16`.

This proves the native PL DDR reader/decoder/RTIO path, with host RPC/DAP upload
and arming. It does **not** implement native AUX DDMA. Next stages are bounded
upload/allocation/record validation and native AUX playback/status integration;
post-abort handoff to packet ownership also requires explicit qualification.


## Bounded native-upload staging policy (offline, 2026-10-16)

`aux_protocol/ddma_store.h` is a pure-memory, single-entry staging policy for
native AUX integration, not yet linked into firmware. It uses the pinned
upstream PayloadStatus first/last bits and `(source,id)` identity. A first
fragment replaces the prior slot; continuations require the matching active
upload. Busy playback rejects every mutation. Overflow or malformed final
records invalidate the slot; incomplete slots cannot be marked complete.

The2048-byte window reserves512 bytes for terminator/speculative read padding;
at most1536 uploaded bytes are accepted (1530 for whole17-byte records).
The first supported subset is channel0 TTL output and channel1 edge gate,
destination1,17-byte records, monotonic nonnegative fine3-aligned timestamps,
and bounded address/data values. Complete validation precedes stripping the
remote destination byte. The remainder of the window is zero-filled.
This intentionally rejects wider/general RTIO records pending dedicated tests.

Run `make test-drtio-ddma-store O=/srv/codex-hil-data/artiq-zynqmp/build/ddma-store`.
Host C tests use ASan/UBSan, exercise fragmentation across records, truncation,
invalid fields/timestamps, source/ID mismatch, busy ownership, overflow,
maximum valid trace, padding and recovery. This is not a wire-codec, cache/MMIO,
playback/status or hardware test. Next extend the unchanged upstream Rust codec
C ABI with DDMA fields, test real packet vectors, then connect staging/cache
flush and bounded DMA CSR control under the existing guarded session.


## Native DDMA codec ABI (offline, 2026-10-16)

`aux_protocol/ddma_codec.rs` wraps unchanged pinned upstream packet read/write
for types0xb0–0xb6 (add/reply, remove/reply, playback/reply, status), including
native CRC/padding. C layout is declared in `ddma_codec.h`; host Rust/C assert
1056-byte size, timestamp offset32 and trace offset40. Callers must supply
valid nonoverlapping buffers and initialized, aligned structs for the stated
lengths; pointer/null/capacity checks do not validate arbitrary addresses.

The upload decoder checks status and payload length before upstream parsing,
as upstream assumes valid status/slice bounds. CRC, short frames and unsupported
kinds are rejected; decode output is published only on success. The legacy
scalar AUX decoder rejects DDMA before upstream parsing. Actual dispatch must
use the new full-field ABI so malformed DDMA cannot enter the old path.

Host reference tests cover all seven kinds, field preservation, every truncated
length, CRC corruption, invalid status/oversized length and maximum1010-byte
payload (1024-byte frame), plus ABI layout. A53 static library/firmware link is
also checked; the firmware service still does not dispatch DDMA. No physical
DDMA transfer or playback is claimed. Next connect checked packets to staging,
reply semantics and deferred playback/status with cache/MMIO guards.


## DDMA service state machine (offline, 2026-10-16)

`aux_protocol/ddma_service.h` connects full-field decoded requests to the
bounded store and native reply/status fields. Only direct destination1 is
handled. Source/ID ownership, readiness, completion and timestamp alignment/
signed-overflow checks gate playback. The hardware-start callback must validate
live readiness/future time, copy and flush all2048 padded bytes and obtain real
CSR admission; it is mocked in the present host tests, not implemented here.

A successful admission reserves the slot until engine completion and successful
status transport. Upload/remove/replay are rejected while running or while a
status awaits transport. Native status preserves requesting source, ID, error,
channel and timestamp. The transport must send the immediate reply or fail
closed; it cannot undo outputs already admitted. Link/reset abort handling and
post-error hardware requalification remain to be integrated. Completion itself
means decoder admission/drain, not elapsed event time or proven queue-empty.

`make test-drtio-ddma-service O=/srv/codex-hil-data/artiq-zynqmp/build/ddma-service`
runs native ASan/UBSan tests with mock admission. Coverage includes incomplete
trace, wrong destination/ID, unready, admission failure, timestamp overflow and
alignment, busy slot, status retention, error forwarding and policy reuse.
Mock reuse does not qualify physical abort recovery. No service is active on
hardware yet. Next implement the firmware's checked decoder dispatch, backend
cache/CSR operations and status polling under bounded failure handling.


## DDR/cache/CSR backend adapter (offline, 2026-10-16)

`ddma_backend.h` supplies the service start callback: readiness and live time
checks, idle/pending checks, exact2048-byte copy/flush, MSW-first64-bit CSRs,
configuration readback and bounded accepted-counter polling. Immutable arena
is0x22000000, bank0xa0002000, budget16, watchdog134217728. Register offsets
were compared with the qualified credit4 map. Timestamp must have at least
1000000mu lead both before copying and immediately before start. Missing live
time refuses admission. A timeout/rejection after START latches a backend fault;
no automatic reset, retry or pointer reuse is permitted by this adapter.

`ddma_a53.h` binds volatile MMIO plus DSB, DDR memcpy, AMD cache flush plus DSB
and1ms poll delay; cross-compiled with the existing A53 toolchain/BSP. It still
requires board-specific live readiness and time callbacks. Current diagnostic
CSR map has TSC-load count but **no live TSC snapshot**; add and qualify that
CSR/CDC before enabling playback through AUX. Do not substitute host/wall time.

Host ASan/UBSan tests use mocked IO for sequencing, active/pending rejection,
missing/expired time, bounds and timeout fault latch. They do not exercise
physical DDR/cache/AXI. No new service dispatch or hardware load in this stage.
Next add live snapshot to gateware, test CDC, then firmware dispatch/status.


## Coherent live TSC snapshot RTL (2026-10-16, offline)

The DMA target now appends `aux_tsc_snapshot_request`, `busy`, `valid` and
64-bit `value` CSRs. Existing register addresses are preserved. A request edge
clears valid and toggles an RX request; RX admits exactly one full64-bit TSC
into a4-entry asynchronous FIFO. PS publishes the complete value, then holds
it stable until the next accepted request. Busy requests are dropped. Shared
endpoint reset clears token/FIFO/output state; it must cover RX clock loss.
The captured value is in fine3 units from native `tsc.full_ts`, not a software
clock estimate. A read is a past sample; firmware must bound its age and
invalidate observations on reset/link/TSC-load epoch changes.

Two asynchronous-clock simulations PASS: changing binary values/backward loads
without torn reads, stable publication, duplicate busy requests, and common
reset discarding in-flight data before a fresh request. Existing current-source
DMA transport2 tests PASS. Top HDL/CSR generation PASS. No timing, hardware
or new firmware activation claimed. `build_top.sh` explicitly refuses this new
map until snapshot FIFO CDC constraints and implementation checks are added;
the prior qualified credit4 bit remains the hardware baseline.

Next add exact Gray-pointer constraints/counts for this FIFO, update routed
qualification, then firmware MSW-first snapshot read with bounded wait and
reset/load-count/readiness checks. Only then enable AUX DDMA dispatch.


## Snapshot FIFO implementation qualification in progress (2026-10-16)

Exact generated-HDL extraction now includes both3-bit snapshot Gray pointers
in the protected timed-first-stage set:8 groups/170 endpoints total. Each gets
8ns datapath-only max delay and8ns bus skew; generic first-stage false paths
exclude these endpoints. Routed checker opens the DCP and requires a numeric
8ns requirement/nonnegative slack on every endpoint. The top checker now expects
16 total skew groups for the snapshot target. Older six-group/164-bit builds
remain checkable using their map; the current snapshot map requires8/170.

HDL extraction and missing-endpoint/wrong-width negative tests PASS. The interim
build prohibition is replaced by these constraints and mandatory implementation
checks. Build is RUNNING at `build-vivado/satellite-dma-tsc-route-2026-10-16`,
log `build/tsc-snapshot-vivado-session-2026-10-16.log`, timeout1500s. Do not edit
running build/RTL/checker helpers until completion. No routed PASS or hardware
claim yet. Next inspect route/CDC results, fix any real failures, then firmware
snapshot read/dispatch. Prior hardware baseline remains restored and unchanged.


## Snapshot routed PASS and bounded firmware reader (2026-10-16)

Build `satellite-dma-tsc-route-2026-10-16` finished PASS. Bit SHA256
860bb0e5f0048101552d43c40ccafb33655c9dc2209f6ff75d8fd9298415c900.
All170 endpoints in8 exact CDC groups have numeric8ns requirements, minimum
slack7.153ns;16 skew groups and top timing checks PASS. This supersedes the
previous RUNNING note; no physical snapshot read has yet been performed.

`aux_protocol/tsc_reader.h` provides bounded ordered MMIO snapshot reads with
nonzero/matching load epoch, pre/post readiness, stable MSW-first64-bit read,
100-poll bound and100us maximum elapsed. It returns sample+2*elapsed_ns+1000,
a conservative upper-time estimate under the explicit target rate<=2mu/ns
assumption. The1ms backend deadline margin uses that upper estimate. Output is
unchanged on error. A single firmware owner must ensure no concurrent request,
reset or epoch ABA; live dispatch integration must preserve that invariant.

`tsc_a53.h` uses CNTPCT/CNTFRQ solely to bound age; it does not synthesize RTIO
time.1us poll delay and ordered DSB MMIO use existing AMD standalone bindings.
Host ASan/UBSan tests cover age, timeout, changed epoch/readiness and signed
range; A53 compile PASS. Register constants matched the new qualified map.
Not yet linked into AUX dispatch, loaded or physically qualified. Next build
a firmware snapshot probe and repeat guarded cold AUX/DIO/snapshot validation
on this exact new bit/firmware before native DDMA service activation.


## Physical snapshot probe PASS (2026-10-16)

Guarded all-four-lease session loaded bit860bb0e5... and snapshot-enabled
A53 firmware. After actual Kasli TSC-load ACK, four coherent fine3-aligned
samples increased:14433320128,14435585360,14441487432,14447389872mu.
Conservative age allowances were10000,8066,7800,7800mu. Native reset and
both8-rise DIO kernels also passed. This qualifies this bounded snapshot
probe; it does not establish absolute offset/jitter or native AUX DDMA.

Kasli checker/volatile clock profile and Genesys normal local core restored
and validated PASS, including TTL/CoreDMA/analyzer/MonInj/Ethernet;192.168.2.3.
No flash/SD/OTP/Genesys Si writes. Evidence
`evidence/kasli03-tsc-snapshot-hardware-2026-10-16/results.json`.
Firmware build uses `--snapshot-probe` with exact map validation. External
session requires matching `snapshot_test`, helper hashes and four UART samples.
Next connect checked DDMA requests to service/backend with this live-time
callback; then test upload/reply/status offline before guarded native playback.


## Opt-in native AUX DDMA firmware wiring (2026-10-16, not loaded)

`build_firmware.py --external --tsc --reset --dio --snapshot-probe --ddma`
now compiles the checked full-field decoder into the actual AUX service loop.
Upload/remove/playback requests dispatch to the bounded store/service. Playback
uses A53 DDR copy/cache flush, live snapshot age bound and actual DMA CSR
admission. Firmware replies through the unchanged upstream codec/physical AUX
transmitter. Completion polling sends native PlaybackStatus before releasing
the slot. The immutable DMA arena/bank and snapshot CSR map are build-checked.

No physical native DDMA claim: this ELF has only built/linked. Host wire-flow
test links actual upstream Rust codec to C service and checks fragmented upload,
playback response, busy removal/replay rejection, status transport/CRC and erase;
its hardware admission callback is mocked. Four existing ASan/UBSan policy
suites PASS. A53 firmware build PASS. Current external-session wrapper rejects
native-DDMA firmware until dedicated guarded qualification is implemented;
never use the host-DAP stage to imply AUX upload success.

The service is a single-slot TTL-only laboratory subset. It fails closed on
ambiguous start/transport fault, unexpected reset while running or a2s running
bound. Hardware error latches backend fault: no post-abort/recovery promise.
No software event replay, DDR reuse on an ambiguous start, or automatic hardware
reset is introduced. Native status means DMA admission/drain completion, not
elapsed event time. Multi-slot/general RTIO/wide outputs/routing remain absent.
Next prepare a standard Kasli distributed-CoreDMA kernel and dedicated guarded
service stage, checking upload replies/status plus physical loopback edges.


## Native CoreDMA guarded attempt (2026-10-16)

Standard distributed CoreDMA example compiles for Kasli rv32ima. The native
service stage requires successful exact-bit/firmware idle snapshot/DIO and
restoration proof, rejects host-DAP arming, checks helper hashes and requires
native upload/playback/status/remove messages plus8 physical edges. Negative
proof/mismatched firmware/host-mode tests PASS.

New native-service firmware passed guarded idle AUX/TSC/snapshot/reset and
both DIO kernels, then both baseline restorations PASS. Evidence
`kasli03-native-ddma-idle-hardware-2026-10-16`.

First actual CoreDMA attempt FAIL: standard client reported unexpected core
connection close. Satellite UART contains no DDMA request/reply/status lines;
physical native playback is NOT_PROVEN. No cause is established yet. Runtime
UART was previously only saved during startup, losing later buffered panic
output. Parent now drains the same already-open Kasli UART in observer finally,
while all leases remain held and before restoration; capture errors are recorded
without masking the original test error. This logging fix is not yet exercised.
Both boards restored and validated PASS after the failed attempt (normal local
Genesys192.168.2.3). No persistent/Genesys Si writes. Next bounded diagnostic
repeat with master UART capture, then fix the demonstrated software failure;
do not label this as native-DDMA success or suppress its exception.


## Master tuple ABI failure captured (2026-10-16)

Bounded repeat captured the master UART before restoration: kernel panic at
`ksupport/lib.rs:442:5`, `ptr % 64 == 0`. No satellite DDMA requests observed.
Both board baseline restorations PASS. The generated RISC-V callsite allocates
24 bytes, reads duration at8/12, address at16 and uses_ddma at20. Old upstream
ksupport returns a16-byte C struct with fields0/8/12. This reproduces the known
NAC3 ObjectHeader tuple mismatch already fixed in the A53 local-CoreDMA bridge.

`prepare_flashfree_runtime.py --nac3-dma-abi` now optionally adds the same two
header words and zero initialization, retaining alignment assertions and adding
a24-byte Rust size check. Applied only in isolated worktree
`work/kasli03-bram-runtime-dma-abi`; references and prior source trees preserved.
RISC-V C static layout assertions PASS. Full firmware build RUNNING in
`build/kasli03-dma-abi-2026-10-16`,900s timeout; build.log records toolchain
resolution/compilation. Fixed runtime has not run. Next finish build, compare
all generated hardware ABI headers with qualified BRAM bitstream, then a guarded
runtime qualification and repeat CoreDMA. No claim that tuple fix resolves all
remaining native DDMA issues. Evidence native-ddma-abi-diagnosis-2026-10-16 and
kasli03-native-ddma-capture-hardware-2026-10-16.


## Native distributed CoreDMA physical PASS (2026-10-16)

ABI-corrected Kasli RAM runtime built with matching128KiB ROM configuration;
all three generated hardware ABI headers byte-identical to the qualified bit.
Runtime SHA256 f0b53c4cc100951258422bb1bb6e617348cda8eacc0eacc10a09e71968d79d4b.
Standard `examples/kasli_drtio_native_dma.py` now passes on physical boards.
Native AUX AddTraceReply/PlaybackReply/PlaybackStatus(error0)/RemoveTraceReply
all reference ID1076235456 and succeed. Kasli captures8 physical edges,
width8000mu/period80000mu/first_delta1000120mu. No DAP DDR upload or arming.

This proves one bounded TTL trace through native master CoreDMA, AUX codec,
firmware store/cache/CSR backend, native PL DDR DMA/RTIO and physical loopback.
AUX/snapshot/reset/two DIO kernels and both baseline restorations also PASS;
Genesys normal local TTL/CoreDMA/analyzer/MonInj/Ethernet at192.168.2.3.
All four shared leases held throughout. No flash/SD/OTP/Genesys Si writes.
Evidence `kasli03-native-ddma-fixedabi-hardware-2026-10-16/results.json`.

Native service now PARTIAL, not MISSING: single-slot/17-byte TTL subset only.
Next repeat handle playback, replacement/erase/reupload and fragmentation near
bounds under guarded physical capture. Do not claim post-abort recovery,
general wide-output DMA, production routing, absolute offset/jitter or link
latency qualification. The new satellite UART finally drain preserves logs on
future client failures as well as successful completion.


## Native lifecycle physical PASS (2026-10-16)

`kasli_drtio_native_dma_lifecycle.py` runs three versions of the named trace,
three plays each (first by name, next two via one retained CoreDMA handle).
Phase1 replaces the existing name; phase2 uploads after explicit erase. Pulse
width/period pairs are8000/80000,16000/120000,24000/160000mu, with4 pulses
per play. All9 plays/72 physical edges PASS, first_delta1000120mu throughout.
Each capture checks count, width, spacing and absence of a ninth edge.

The guarded `native_ddma_lifecycle` stage requires exact native AUX operation
order: upload, three playback/status pairs and erase for each phase, including
all9 statuses error0. All3 allocations reused ID1076235456; distinct waveform
measurements plus ordered erase/replacement prove new content despite ID reuse.
Parser negative tests reject wrong width, error status and missing erase.
Standard rv32ima compilation PASS; hardware uses unchanged qualified firmware/
bit and ABI-corrected Kasli runtime. No host-DAP upload/arming.

AUX/snapshot/reset/two DIO kernels and both baseline restorations PASS; normal
Genesys local TTL/CoreDMA/analyzer/MonInj/Ethernet restored192.168.2.3. All four
shared leases covered programming/UART/network/experiments/restoration. No
persistent/Genesys Si writes. Evidence
`kasli03-native-ddma-lifecycle-hardware-2026-10-16/results.json`.
Next offline qualify long trace versus read-window/prefetch budget, then native
multi-packet upload/physical fragmentation. No long-trace/abort/absolute-phase
qualification inferred from these short-trace lifecycle tests.


## Long-trace prefetch boundary (2026-10-16, offline)

Before physical fragmentation tests, new fast-AXI simulation exposed error65
for1020-byte/60-record trace with the previously qualified4-outstanding guard.
Outstanding responses plus already-buffered raw FIFO data let cumulative AR
reach the reserved drain threshold before the terminator was decoded. Existing
short-trace physical PASS does not qualify this longer trace.

Guard now permits2 outstanding requests, preserving the reused reader,16-burst
budget and2048-byte padded window. Firmware payload admission is reduced from
1536 to1024 bytes (maximum whole17-byte trace1020 bytes); larger uploads are
invalidated rather than launched. The retained1530-byte RTL negative proves
budget error/drain/restart. A1020-byte trace succeeds with70-request AXI model,
exact60 native CRI commands, bounded addresses and matched AR/RLAST counts.
No error masking or larger speculative window. Performance unqualified.

Current-source CSR10 tests +engine/CDC17 tests PASS. New first CSR run had a
Python local-variable error in the recovery test; fixed and full suite rerun
PASS. Store/service/backend ASan/UBSan PASS. Real upstream codec->C store splits
1020 bytes into1010/10 payloads across a record boundary; reconstructed60 records,
normalization and padding PASS. Optional upload UART metadata records status/
length per packet for future physical evidence. New A53 firmware build PASS.

Vivado RUNNING `build-vivado/satellite-dma-credit2-route-2026-10-16`,1500s bound,
log `build/dma-credit2-vivado-session-2026-10-16.log`. Piotr decoder two boundary
cases also running. Do not edit running RTL/build/checker/test helpers.
No hardware accessed in this stage; restored lifecycle-tested baseline remains.
Next qualify route/CDC, obtain new exact-bit/firmware idle/DIO proof, then native
29-pulse/58-edge1020-byte physical upload in two packets. Do not use previous
firmware proof after payload-policy/helper hashes changed.


## Native fragmented upload physical PASS (2026-10-16)

Credit2 route PASS, bit SHA256
0c8fcc5c6b6e1721267dd453e2a1f4a97c89b426a0d22f6e795f996afccf5de9.
All170 endpoints/8 CDC groups have8ns requirement, minimum slack7.228ns;
16 skew groups/top timing PASS. Exact new bit/firmware first passed guarded
idle AUX/snapshot/reset/two DIO kernels and both baseline restorations.

Standard `kasli_drtio_native_dma_fragmented.py` then uploaded1020 bytes through
native AUX as First1010 +Last10, splitting a17-byte record across packets.
Both AddTraceReplies, PlaybackReply, PlaybackStatus(error0) and RemoveTraceReply
succeeded for ID1076235456. Kasli physically captured29 pulses/58 edges,
width8000mu,period16000mu,first_delta1000120mu and no extra edge. No host DAP
upload or arming. This tests the largest whole17-byte trace under current1024B
payload policy, while preserving the16-burst/2048-byte padded read window.

Parser negatives reject wrong fragment length/status, DMA error and missing
erase;3 host preflight/parser tests PASS. Both actual hardware sessions restored
Kasli checker/clock profile and normal Genesys local TTL/CoreDMA/analyzer/
MonInj/Ethernet PASS at192.168.2.3. All4 leases held throughout; no flash/SD/OTP/
Genesys Si writes. Evidence `kasli03-credit2-idle-hardware-2026-10-16` and
`kasli03-native-ddma-fragment-hardware-2026-10-16`.

Next repeat long-trace handles/replacement and test bounded upload rejection/
recovery offline before further physical negatives. Fragmentation PASS does not
qualify reset/abort recovery, arbitrary RTIO records, general routing or phase/
jitter/deterministic link latency.


## Long native trace lifecycle physical PASS (2026-10-16)

`kasli_drtio_native_dma_long_lifecycle.py` records three1020-byte versions,
each uploaded as First1010/Last10, and plays each three times (six via handle).
All9 plays/522 physical edges (261 pulses) PASS. Width/period pairs4000/16000,
6000/20000,8000/24000mu, first_delta1000120mu throughout; no extra edges.
Replacement and erase/reupload PASS. Checker requires six exact fragments,
ordered18 successful replies plus9 error0 statuses with consistent per-phase ID.
Four host preflight/parser tests PASS, including wrong length/width/status and
missing erase negatives. Firmware/bit/master runtime unchanged.

New `make test-drtio-ddma-reject` exercises source mismatch, orphan last,
truncated/invalid final record, wrong destination, oversized accumulated payload
and wire-array length, invalid status and busy ownership. ASan/UBSan PASS;
zero mock start calls across all malformed uploads, then valid recovery/two
admissions. This is host policy validation, not physical malformed-packet proof.

Actual hardware session restored both board baselines PASS, including Kasli
checker/clock profile and Genesys local TTL/CoreDMA/analyzer/MonInj/Ethernet
at192.168.2.3. All4 leases held; no persistent/Genesys Si writes. Evidence
`kasli03-native-ddma-long-lifecycle-hardware-2026-10-16` and
`ddma-reject-offline-2026-10-16`. Next audit and RTL-test abort-to-packet handoff;
current production service fails closed on abort and does not claim recovery.


## Abort-to-packet handoff RTL recovery (2026-10-16)

A new actual AXI/native DMA -> CRISwitch/SED -> serialized native packet test
reproduced sticky abort telemetry holding SED reset after memory drain. Simply
gating reset by engine active fixed running-clock handoff but FAILED a real
simulator RX-clock pause: both canceled DMA events fired on resume. This
negative is preserved; a short reset pulse across a stopped clock is invalid.

Abort request now remains latched until RX observes eight actual reset edges
and acknowledges them to sys. Sys releases only after engine drain/IDLE, then
waits for acknowledgement return-to-zero before admitting another epoch.
`recovering` extends CSR active/busy, rejects new starts and prevents result
clear while the handshake is incomplete. Target ownership therefore remains
DMA through recovery. Sticky error diagnostics remain latched; recovery does
not clear the reported error. Software must wait active0 before result clear.

Both running-RX and paused-RX tests verify no canceled events, conserved AXI
AR/RLAST, preserved PHY/TSC, rejected early start without new reads and a native
packet pulse after handoff without a successful new DMA epoch. Final target-
ownership/TSC assertions PASS twice each current/Piotr. Current full24-test
engine/CDC/CSR/cold-release regression PASS. No physical abort recovery claim.

Vivado RUNNING `build-vivado/satellite-dma-abort-handoff-route-2026-10-16`,
1500s bound/log `build/dma-abort-handoff-vivado-session-2026-10-16.log`.
Do not edit running RTL/build/checker helpers. Firmware native service still
fails closed on abort; no recovery policy was relaxed and no HW was touched.
Next qualify implementation/CDC, then prepare a bounded guarded handoff test.
Native AUX fault-code mapping/recovery semantics need separate review before
claiming production recovery. Prior long-DDMA hardware baseline is unchanged.


### Routed abort fix and AUX error ABI audit (2026-10-16)

The above Vivado run completed PASS: eight groups/170 CDC endpoints meet
8ns, minimum slack7.206ns. Bitstream SHA256
`21c187cbeaf98543153b126bda5fd32ee079f1b4345a8aa9ec057863b5af24a8`.
This is implementation qualification only, not a physical abort test.

Lab CSR error bits differ from the upstream AUX playback status ABI. Native
CRI underflow/unreachable are CSR bits2/3, whereas master ksupport tests AUX
bits0/1. `ddma_aux_error` now translates only these native errors, preserving
channel/timestamp. All other errors (abort, AXI, alignment, watchdog, read
budget, unknown bits) fail closed with raw UART telemetry and no playback
status. The existing upstream master ignores unknown AUX error bits, so
forwarding the raw byte could falsely indicate success or the wrong exception.
Internal failure intentionally requires session restoration and can surface
as a master timeout; this is not automatic recovery. No upstream edit needed.

ASan/UBSan service tests exhaust all256 raw-byte combinations and reject a
future unknownbit256. A53/Rust firmware compilation PASS; evidence in
`evidence/ddma-status-map-offline-2026-10-16`. Both new image qualification on
hardware and error-injection semantics remain NOT_RUN. The next session must
qualify fresh bit/firmware idle before native playback regression.


Abort-handoff image2026-10-16 physical regression PASS: fresh bit21c187cb...
and mapped-status firmware668ca20c... first passed guarded idle qualification
(native reset2, physical DIO2x8pulses, TSCsnapshot4), then native long DDMA
3fragmented1020B uploads/9plays/6handles/522edges PASS. All9first_delta1000120mu;
width/period4000/16000,6000/20000,8000/24000mu. No new AUXsend/RX/masterreset
errors. Both sessions restored Kasli diagnostic/clock and Genesys normallocal
TTL/DMA/analyzer/MonInj/Ethernet PASS192.168.2.3. All4sharedlocks held through
restoration. No flash/SD/OTP/GenesysSi writes. Evidence kasli03-abort-handoff-
{idle,long}-hardware-2026-10-16. Physical abort/fault status injection NOT_RUN;
production error recovery remains fail-closed. Next prepare bounded host-armed
abort-to-native-packet diagnostic with canceled-output and postabort-DIO checks.


### Preparation for physical abort cancellation test (2026-10-16)

The existing host-armed ten-record trace may finish admission before a DAP
abort. An abort after completion would not validate queue cancellation. New
`abort_trace_bytes()` is an offline-only fixture:1100 alternating TTL writes
(channel0, address0), strictly increasing fine3 timestamps1000000+16000*i,
terminator plus zero padding to32768bytes. This exceeds the target's nominal
8x128 SED slots. Native RecordSlicer decodes all1100 records and terminator
correctly in both current and Piotr trees. This does not yet prove actual
backpressure in the complete engine. Tests also retain short-trace coverage.

The future guarded host-only diagnostic may reserve256 bursts in the existing
exclusive DDR arena. Native AUX remains limited to1024 payload bytes/16 bursts;
the fixture is not enabled by any live wrapper. The old host probe qualification
now accepts only known6/164 and8/170 CDC shapes, with8ns requirement and
nonnegative slack, while retaining per-artifact hash verification.

Required next steps before hardware use:

1. Prove long-fixture backpressure and abort drain with the complete native SED
   model. Confirm actual outstanding-read conservation at the256-burst bound.
2. Integrate an opt-in host probe under the existing parent/all4 leases. Use
   bounded block DDR write/readback, not thousands of individual DAP accesses.
   Validate a live TSC snapshot and ample future offset after loading.
3. Require accepted counter+1 and active1/pending0 after a settling interval.
   If DMA already completed, fail the test; do not claim cancellation. Abort,
   then require result bit0, no extra faults, completed+1 and active0 (which
   includes recovery handshake), with unchanged TSC epoch and live link.
4. Abort resets input control. Rearm the physical input through normal RT
   packets after recovery and before the canceled events; capture beyond the
   last canceled timestamp. Assert no edges. Then exercise ordinary DIO
   without a new DMA start or core.reset masking the handoff.
5. Record failure evidence and restore both baselines in all cases. No flash,
   SD, OTP, Genesys Si writes. Paused recovered-clock hardware fault injection
   is a separate test; running-clock cancellation alone cannot qualify it.

Evidence `evidence/dma-abort-fixture-offline-2026-10-16`; no HW accessed.


### Long fixture backpressure qualified in complete RTL (2026-10-16)

The exact32768-byte/1100-record host-only fixture now runs through actual
AXI reader, two-credit guard, raw CDC, native decoder/CRI switch and native
SyncRTIO/SED with8 lanes/depth128. It stalls after129 write commands (lane
distribution need not fill all1024 nominal slots). At abort,20 AR have been
accepted and18 RLAST returned: two reads are outstanding. The256-burst budget
is not exhausted, no pre-abort errors/edges occur, and DMA is active.

Abort drains all accepted reads, yields exact rawerror1 with no budget fault
and zero outstanding reads, completes recovery and restores packet ownership.
A normal native RT packet pulse then passes without a new DMA start, without
clearing sticky abort telemetry, and without PHY reset or TSC discontinuity.
Current and Piotr variants PASS. The long-fixture case intentionally does not
simulate to its distant canceled timestamps; absence of late physical edges
is still NOT_RUN. Earlier short-fixture cases cover that property in RTL.

No hardware access. The fixture is still disconnected from live wrappers.
Next integrate guarded block DDR loading, live-TSC/active checks, explicit
abort and rearmed physical input observation into the existing host-only
parent session. Native AUX payload/burst limits and fail-closed policy stay
unchanged. Evidence `evidence/dma-saturated-abort-offline-2026-10-16`.


### Guarded host abort integration (2026-10-16, offline)

`host_dma_abort_test=true` now selects a separate host-only diagnostic through
`host_dma_session`/`abort_dma_session`. It requires non-native firmware, snapshot
test, explicit `abort_acknowledgement="host-only-32768-byte-window"` and exact
prior bit/firmware idle+DIO/restoration proof in `dma_idle_qualification`. A
native DDMA session cannot enable it. Normal host/native playback paths retain
their existing limits. No live abort session has been run.

`make_abort_tcl` uses documented XSDB binary block write/read to transfer and
compare32768 bytes. It validates identity/readiness, live snapshot age/future
lead (conservative2mu/ns bound), active/pending and epoch counters before an
explicit abort. It then requires exacterror1, completed+1, active0 (including
recovery), unchanged link/TSC epoch, no RTIO/PHY reset or async error and time
remaining for observation. It logs before/after counters; does not clear the
result, reset RTIO or restart DMA. The inherited Genesys lease and existing
all-board parent remain mandatory.

`examples/kasli_drtio_dma_abort.py` compiles with actual ARTIQ/NAC3. It allows
30s future offset for RPC load/abort, rearms input after recovery, observes
start-1ms through start+20ms (last canceled timestamp start+18.584ms), requires
zero edges, then demands one ordinary packet pulse/two edges/8000mu width
without another core.reset or DMA start. RPC child25s, experiment75s bounds.
Parent restores both boards on failure. A positive result would qualify only
running-clock host-armed abort; paused-clock and native AUX recovery remain
separate.

Seven offline tests PASS, including actual Tcl execution with mocked MMIO/DDR:
success plus early completion, unexpected fault, corrupt readback and late
offset rejection. Wrapper rejects native mode/missing snapshot/acknowledgement/
wrong proof. Fresh non-native snapshot A53/Rust firmware build PASS at
`build/host-abort-firmware-2026-10-16`; it needs its own physical idle proof.
Evidence `evidence/dma-abort-host-integration-offline-2026-10-16`. Next guarded
idle qualification, followed by exact-proof abort session; physical NOT_RUN.


### Physical host-only abort cancellation PASS (2026-10-16)

Fresh non-native snapshot firmware SHA256
`4569379d08b9a58921d8379a9ba5fa0d4458cd8bc376d19f7a9eff238da33ed9`
and routed bit`21c187cb...` first passed guarded idle qualification:2 native
reset handshakes,2x8 physical DIO pulses,4 TSC snapshots and full restoration.
An independent guarded session then passed the opt-in host-only abort test.

The complete32768-byte DDR window was block-loaded and read back exactly
(hashes recorded in binary-manifest.json; large generated binaries archived).
Before abort: active1, accepted1, completed0, epoch1, sampled49376986304mu,
offset76029910816mu. After abort: active0, pending1, exacterror1, accepted1,
completed1, epoch1; readiness/error checks clean. Input was rearmed after
recovery and observed across every timestamp of the1100-record canceled
trace: zero edges. A subsequent native RT packet pulse yielded2 physical
edges with8000mu width without a new DMA epoch, result clear or core.reset.

Both sessions restored Kasli diagnostic and reviewed volatile Si5324 baseline
and Genesys normal local ARTIQ at192.168.2.3. Local TTL/CoreDMA/analyzer/MonInj
and Ethernet restoration checks PASS. All4 shared locks held through
restoration; no flash/SD/OTP/Genesys Si writes. AUX send/RX/master reset error
counts unchanged. Evidence `kasli03-host-abort-{idle,physical}-hardware-2026-10-16`.

Scope: one running-clock host-DAP-started/aborted epoch with physical TTL
observation. No claim of paused-RX hardware recovery, native AUX fault recovery,
absolute phase/jitter or cancellation of events that already fired. Next repeat
the bounded abort session independently, then qualify native AUX fault status
propagation before relaxing its fail-closed policy.


Independent physical abort repeat2026-10-16 PASS: images reloaded under all4
shared leases, reset/DIO/TSC prerequisites repeated. Preabort active1/accepted1/
completed0, sampled50195627976mu, offset76882906768mu, epoch1. Postabort
active0/pending1/error1/accepted1/completed1, epoch1 unchanged. All canceled
1100trace timestamps covered by rearmed input:0edges; subsequent packet pulse
2edges/8000mu without DMA restart/core.reset PASS. Both board restorations and
normal Genesys localTTL/DMA/analyzer/MonInj/Ethernet PASS192.168.2.3. No flash/
SD/OTP/GenesysSi writes. Evidence kasli03-host-abort-repeat-hardware-2026-10-16.
Two independent physical runningclock hostabort sessions now PASS. NativeAUX
fault-status propagation/recovery and pausedRX hardware tests remain NOT_RUN;
next nativeDDMA rejection/error handling, preserving existing failclosed policy.


### Native oversized-upload rejection preparation (2026-10-17)

The upstream master calls remote upload during DmaRecordStop. A failed
DmaAddTraceReply propagates a runtime/session error before any playback call;
this must be tested as an expected failing host invocation, not a successful
kernel or a guessed catchable kernel exception. Reference paths:
`runtime/session.rs` DmaRecordStop, `runtime/rtio_mgt.rs` ddma_upload_trace.
The latter currently constructs DmaAddTraceFail using reply destination (master
0), so the diagnostic can label satellite#0 despite actual remote destination1.
Do not infer physical routing from that error label. Upstream is untouched.

New `examples/kasli_drtio_native_dma_oversize.py` records30 pulses plus input
gate open/close:62x17B=1054, fragments1010/44, over the unchanged1024B bound.
It never calls playback. If recorder exit unexpectedly succeeds it prints
`NATIVE_DDMA_OVERSIZE_UNEXPECTED_ACCEPT`, which the future guarded parser must
reject. Actual ARTIQ/NAC3 compilation PASS. Existing C policy ASan/UBSan now
tests the same1054-byte boundary with valid records, accepts the first1010B,
rejects the final44B, blocks playback (zero mock starts) and subsequently
accepts valid recovery with two mock starts. No firmware policy changed.

No HW access this turn. Next integrate opt-in bounded expected-failure process
under the existing all-board leases: require concrete AUX first-fragmentACK/
last-fragmentNACK, no playback/status, matching IDs and master error, then run
a valid native playback in a fresh host connection before restoration. Guard
against treating timeout, link loss, panic or arbitrary nonzero exit as PASS.
Evidence `evidence/ddma-oversize-offline-2026-10-17`; physical NOT_RUN.


### Native oversized-upload rejection/recovery physical PASS (2026-10-17)

Opt-in `native_ddma_rejection=true` requires standalone native playback mode
and exact prior idle/DIO/snapshot/restoration proof. The inherited all-board
lease covers a bounded30s expected-failure subprocess and the subsequent
normal60s playback. Parser requires nonzero positive exit, exact upload
1010/44 with matching IDs, firstACK/finalNACK, no playback/status before
recovery, and concrete master upload error. Timeout, kill, generic link loss,
panic, altered fragments or unexpected upload success cannot count as PASS.
Six wrapper/parser regression tests (including11 negative evidence cases) PASS.

Physical result:1054-byte trace ID1076235456 first1010 ACK/final44 NACK; master
logs `error adding DMA trace on satellite #0` (upstream reply-destination label).
No playback/status for rejected trace. New host session, same trace name and
reusedID, valid upload/playback/error0status/erase PASS; physical4pulses/8edges,
8000mu width,80000mu period,first_delta1000120mu. No FPGA reload, firmware
restart or DRTIO link reset between rejection and valid playback. The valid
experiment performs its normal core.reset; no claim of reset-free recovery.

Two observed limitations are retained explicitly. Upstream closes the kernel
session on uploadNACK, so Python receives ConnectionResetError rather than a
structured DMAError. The next same-name record attempts to erase the already
invalidated slot; Genesys NACKs this, upstream logs cleanup failure and proceeds
to successful new upload. This is demonstrated recovery with diagnostic noise,
not polished production error handling. No underlying policy was relaxed.

Both boards restored: Kasli diagnostic/reviewed volatile clock profile and
Genesys normal192.168.2.3 localTTL/CoreDMA/analyzer/MonInj/Ethernet PASS. All4
shared locks through restoration; no flash/SD/OTP/GenesysSi writes. Evidence
`kasli03-native-ddma-rejection-hardware-2026-10-17`, limitations.json and raw
logs; offline `ddma-rejection-wrapper-offline-2026-10-17`. Next examine
structured master upload error and idempotent rejected-trace cleanup without
masking source/id ownership or changing successful playback. Runtime fault
status injection and pausedRX hardware recovery remain NOT_RUN.


### Identity-bound rejected-trace cleanup (2026-10-17, offline)

On payload overflow or final record-validation failure, the staging slot now
zeros every payload byte and retains only a rejected source/ID marker. Matching
DmaRemoveTraceRequest succeeds repeatedly while that marker remains. Wrong
source (including >255), wrongID or busy ownership still fails. No complete/
uploading flag, length or playback eligibility survives invalidation. A new
First fragment replaces the marker; stale cleanup cannot erase a newer
upload or valid trace, even when source/ID differs. Successful trace removal
semantics and the1024-byte/16-burst playback policy remain unchanged.

Four ASan/UBSan store/service/rejection/backend suites PASS: zero payload,
matching repeated cleanup, wrong source/ID, pending-status busy, no rejected
playback, new First replacement and valid recovery. Fresh A53/Rust firmware
compilation PASS at`build/native-ddma-rejected-cleanup-firmware-2026-10-17`.
No HW access. Exact fresh-image idle qualification is required before repeating
the rejection/recovery experiment; old qualification hashes deliberately fail.
Evidence `evidence/ddma-rejected-cleanup-offline-2026-10-17`.

Structured master error audit: DmaRecordStop currently uses synchronous mailbox
`send`/ack with no result reply; runtime propagates upload failure out of the
session and closes the socket. A correct kernel DMAError requires a coordinated
reply in libproto_artiq, runtime and ksupport, followed by normal exception
raising/unwinding, not merely acknowledging a failed upload. Keep original
upstream and qualified master artifacts untouched; implement any such change
as an optional isolated overlay with success/failure validation. Not implemented
in this cleanup change. Next qualify fresh firmware idle then rejected upload
cleanup/recovery with no extra eraseNACK; structured master exception later.


### Identity-bound cleanup physically qualified (2026-10-17)

Firmware18a99107897c68393a68306d7b4f026784422ed6aeb866a5480cfc475836391b
first passed fresh guarded idle/reset/DIO/TSC/restoration qualification on the
existing routed bit21c187cb... . Independent native rejection/recovery then
PASS:1054B1010ACK+44NACK, rejectedID1076235456; cleanup179ACK for exactly that
ID, new170B upload177ACK, playback181ACK, statuserror0, final179ACK. Same
name/reusedID recovery physical8edges,8000mu width,80000mu period,firstdelta
1000120mu. No master cleanup erase error remains. No payload/playback policy
relaxation; native1024B/16burst limits preserved.

`native_ddma_rejected_cleanup=true` requires the existing rejection/recovery
mode and validates exact five-event sequence/IDs, successful ACKs/error0, and
absence of master erase errors. Unknown/missing/extra/NACK/mixed IDs fail.
Eight parser/preflight regression tests PASS, including distinct/reusedID
positive cases and negative evidence controls. Both hardware sessions used
all4 shared leases through restoration. Kasli diagnostic/volatile clock and
Genesys192.168.2.3 localTTL/CoreDMA/analyzer/MonInj/Ethernet restored PASS.
No flash/SD/OTP/GenesysSi writes. Evidence kasli03-rejected-cleanup-{idle,recovery}
-hardware-2026-10-17; offline rejected-cleanup-evidence-offline-2026-10-17.

Remaining: upstream upload failure still closes the kernel session, yielding
Python ConnectionResetError and next-session unclean-kernel warning. Only
cleanup was fixed here. Next isolated optional master mailbox/runtime/ksupport
result reply so upload failure raises structured DMAError without successful
ACK semantics. Runtime fault-status injection/pausedRX hardware remain NOT_RUN.
