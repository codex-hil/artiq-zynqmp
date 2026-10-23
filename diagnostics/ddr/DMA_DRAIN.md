# RTIO DMA drain evidence and reset ownership

This is offline simulation of the tracked `zynqmp_dma.py`, not hardware
quiescence admission. Evidence: `evidence/dma-drain-model-2026-10-23`.

The normal completion cases use the actual Migen DMA, upstream record pipeline
and CRI master. Independent monitors count accepted AXI AR requests and accepted
R bursts ending with RLAST. A memory responder preserves same-ID order and legal
ready/valid behavior; CRI and read responses apply backpressure. The test requires
observed busy, final status zero, no outstanding bursts, no remaining AR/R valid,
and no new request for 30 cycles without another trigger.

24 cases cover response delays 0/3/17, CRI stalls 0/31, OKAY/SLVERR, and trigger
values 0/1. All completed with zero outstanding reads. Peak outstanding: 13;
2628 stalled R cycles and 12300 stalled AR cycles were exercised. Error responses
still permit draining; the bus-error status is separately checked. This is not
exhaustive timing, maximum-counter-depth, malformed AXI or abort qualification.

A negative test wraps the same DMA in Migen ResetInserter. After accepted AR
requests, it resets only PL logic while the modeled PS retains delayed responses.
The DMA reports IDLE with two accepted, unreturned bursts. This is a confirmed
counterexample to **IDLE alone after independent PL reset**. It does not prove
that the actual board reset sequence does this; that sequence must be audited.
Resetting the observer/core must not be treated as resetting all AXI owners.

Required before destructive DDR tests:

- Bind the active bitstream and CSR map to the audited DMA source.
- Exclude every writer of the trigger CSR; writing zero also starts playback.
- Establish completion and error status before disturbing reset/clock ownership.
- Review the actual PS/PL/HP0 reset order and what happens to accepted requests.
- Establish secondary-core, PMU and other PS-master ownership independently.

No new gateware CSR or production logic change was made. A dedicated inflight
CSR would improve visibility but would not by itself solve reset ownership.

Reproduce on the prepared host from the repository root:

```sh
export PYTHONPATH="$PWD/common/artiq:$PWD/common/migen:/srv/codex-hil-data/artiq-zynqmp/reference/misoc-current:/srv/codex-hil-data/artiq-zynqmp/reference/litex"
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -m unittest discover -s tests -p test_dma_drain.py -v
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -m unittest discover -s tests -p test_dma_reset_ownership.py -v
```

The evidence records actual import paths, clean source revisions and RTL/test
hashes. Explicit `common/migen` selection matters: the shared venv otherwise
imports a different reference checkout. Hardware and destructive DDR remain
NOT_RUN for these tests. Next audit the real reset sequence and prepare a
read-only PS/secondary-core capture allowlist.

## Reset source audit and32-register ZDMA read plan —2026-10-23

Offline audit pins actual reset/boot/prepare/gateware/generated-FSBL sources.
Bootstrap does PS system reset before PMU/FSBL; FSBL can call generated PL
isolation/removal/reset operations when PL DONE; normal preparation calls PL
reset configuration again after bitstream load. Sys-domain reset derives from
negated PS pl_resetn0. Generated reset helper mentions GPIO Bank5/EMIO; the
complete exported wiring and HP0 transaction-owner reset timing are not yet
proven. Do not equate logical reset/status0 with drained AXI ownership. Existing
bootstrap catch-stop loops are not positive admission of all secondary cores.

`plan_zdma_snapshot.py` verifies all16canonical channel bases and vendor header
offsets/masks; emits32CH_STS/CH_CTRL2 reads only. No ISR/descriptor/interrupt
registers or writes. Decoder requires two exact complete32-bit observations;
busy/paused/error/enabled/reset-like control or changing state is not quiet.
Even all quiet fields stay NOT_OWNERSHIP/destructive_test_allowed=false.
Four source-drift/allowlist/decoder controls PASS, actual BSP plan generated.
Evidence: `evidence/zdma-reset-audit-2026-10-23`.

No HW/JTAG/UART/network/reset operations. Next implement a bounded shared-lease
read-only snapshot wrapper with exact address allowlist and raw provenance, then
review actual PL reset wiring/HP0 semantics and expand CSU/peripheral/core
ownership independently. No complete DDR write-test admission from this plan.
Normal baseline remains last validated192.168.2.3.

## Read-only live ZDMA64-read capture complete —2026-10-23

New wrapper defaults offline, pins register plan/vendor inputs/execution helpers,
rechecks under shared Genesys lease and enforces45s process-group bound. Fixed
Tcl reads only CH_STS/CH_CTRL2 for16channels twice via exact-cable PSU/AP0.
No stop/reset/UART/network/register writes, ISR clears or force-access mode.
Parser requires exact64ordered unique address/name/channel/sample rows within
one complete frame. Timeout retains partial raw log and releases lease.
Five Tcl/parser/stale-pin/timeout controls PASS; actual preflight PASS.
Evidence/pins: `evidence/zdma-capture-plan-2026-10-23`.

Physical capture COMPLETE under shared lease: all16channels CH_STS=0 and
CTRL2=0 in both samples. No hardware configuration change or baseline reset;
lease released. No fresh Ethernet/runtime test was performed or claimed.
Raw64reads and provenance: `evidence/zdma-status-hardware-2026-10-23`.
Enclosing capture marks hardware=true; pure decoder hardware=false intentionally.
Quiet fields do not establish transaction-owner exclusivity, PL HP0 drain,
secondary-core/PMU/CSU/GEM/SD ownership or destructive DDR admission.

Next offline extend reviewed status inventory to CSU DMA and relevant PS
peripheral masters, plus positive secondary/R5 state capture. Bind future
observations to the diagnostic window rather than assuming this running-runtime
snapshot applies after a later reset. No Si/SD/flash/OTP/Kasli changes.

## CSU status and core metadata live capture complete —2026-10-23

Vendor BSP-checked source/destination STS addresses0xffc80008/0xffc80808,
fields busy/outstanding/FIFO/unacknowledged-done, no SIZE/trigger/interrupt
acknowledgement writes. Fixed Tcl performs4STS reads plus six exact-cable
core metadata queries. Leased wrapper defaults offline, pins plan/vendor/helper
sources before and under lease,45s bounded process group, partial timeout log.
Parser requires complete ordered4-row frame and exact six-core metadata rows.
Four decoder/Tcl/strict-parser controls and actual preflight PASS.
Evidence/pins: `evidence/csu-core-plan-2026-10-23`.

Physical read-only capture COMPLETE: source/destination STS0 in both samples,
busy/outstanding/FIFO/done all0. A53#0/#1 metadata Running; A53#2/#3 Power On
Reset. R5#0 label Halted and R5#1 Lock Step Mode, but suspended0; these labels
are NOT positive halted/reset/cache ownership. All core ownership stays unknown.
Raw provenance: `evidence/csu-core-hardware-2026-10-23`. No stop/reset/force
access/UART/network/register writes or error clears. Lease released, baseline
configuration unchanged; no fresh runtime/network requalification claimed.

Next offline RPU lockstep/reset/clock register allowlist and PS peripheral
DMA activity review, then positive observations inside the actual diagnostic
window. Momentary CSU/ZDMA status and debugger labels cannot authorize DDR
destructive writes or establish PL HP0 drain. No Si/SD/flash/OTP/Kasli changes.


### RPU observation plan — 2026-10-23

`scripts/plan_rpu_snapshot.py` validates seven register addresses and relevant
masks against the AMD `rpu.h` and `crl_apb.h` used by the existing PMU build.
Evidence: `evidence/rpu-plan-2026-10-23`. Three unit tests and three mutated-header
rejection controls PASS. This is offline only; no board fields were read.
NCPUHALT, NVALRESET, reset controls and clock enables are reported separately;
none establishes completed AXI drain, R5 cache ownership or destructive DDR
admission. Next implement leased, bounded DAP capture without writes or core stops.
