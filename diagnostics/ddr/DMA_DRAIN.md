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


### Live RPU observation — 2026-10-23

`capture_rpu_state.py` defaults offline, validates vendor/plan/helper SHA-256
before and under the shared Genesys lease, then permits only fourteen fixed
DAP reads under a 45-second process-group bound. It never stops or resets cores.
Physical capture COMPLETE, both samples identical: global0x50, configs0x4/0x4,
statuses0x3f/0x38, clock0x03000302, reset0xfc0. Split bit=0; both
NCPUHALT=0/NVALRESET=1, R50/R51/AMBA reset bits=0. These observations do not
show cores held in reset or establish cache/AXI drain. Evidence is in
`evidence/rpu-hardware-2026-10-23`. No baseline change or fresh Ethernet test.
Full DDR writes remain NOT_ADMITTED. Next review other active PS DMA masters
and collect qualifying observations within the eventual diagnostic window.


### PS peripheral observation plan — 2026-10-23

`plan_peripheral_dma_snapshot.py` checks actual BSP base/offset/field definitions
for GEM0 NWCTRL, SD1 present state and QSPI DMA STS. Plan/provenance and three
passing unit groups: `evidence/peripheral-dma-plan-2026-10-23`. Hardware NOT_RUN.
Only32-bit configuration/present-state/DMA-status reads are planned; no FIFO,
interrupt acknowledgement, transfer trigger or reset access. Enable bits do not
prove descriptor drain; QSPI done count is unacknowledged completion count.
No DDR admission or other PS master ownership follows. Next implement bounded
leased capture, then account for GEM rings/buffers in the diagnostic handoff.


### Peripheral hardware snapshot — 2026-10-23

`capture_peripheral_dma_state.py` completed six read-only DAP reads under the
shared Genesys lease, with vendor/plan/helper hashes checked before and inside
the lease and45s process-group limit. Both samples: GEM0 NWCTRL0x1c,
SD1 present-state0x1f70000, QSPI DMA STS0. RX/TX remain enabled; SD transfer/inhibit
bits and QSPI busy/outstanding/FIFO are0. No device writes or baseline changes.
Four offline tests PASS; raw evidence `evidence/peripheral-dma-hardware-2026-10-23`.
Momentary fields are not ownership/drain proof. Next audit active GEM rings/buffers
and diagnostic-window policy; no destructive DDR admission follows this snapshot.


### 2026-10-23 — Qualified runtime GEM memory audit (offline)

Audited the normal CPU0 ELF, SHA29f9a64abeb88ab724ca8e6d372d5f7f0cf51080e3790efbcf1040201e8947c3.
Linked emac_bd_space is [0x800000,0xa00000), TX/RX pbuf pointer tables
[0x600000,0x600800)/[0x600800,0x601000). PBUF_POOL and lwIP heap are also
in low DDR; exact half-open symbol ranges in `evidence/gem-memory-audit-2026-10-23`.
Adjacent AMD source writes q->payload into TX descriptors, allocates RX pbufs
from PBUF_POOL and reserves64KiB per RX/TX descriptor area. Thus descriptor
exclusion alone cannot protect Ethernet payloads. XEmacPs_Stop disables
interrupts and RX/TX but contains no DMA-drain polling. Reset documentation
also warns descriptor lists survive reset. Source hashes/line anchors retained;
this is not a reproducible source-to-binary equivalence proof or live pointer dump.
Two audit test groups PASS (missing/duplicate/overlap/type/address controls).
No hardware access or changes. Destructive DDR remains NOT_ADMITTED.
Next inspect the diagnostic FSBL/PMU boot path to establish whether GEM is
started there at all, then define a boot-window ownership gate instead of
assuming that stopping a running networked CPU stops the Ethernet master.


### 2026-10-23 — Passive PL AXI read observer prototype (simulation only)

Added standalone diagnostic Migen prototype counting accepted AR versus accepted
RLAST, with saturating bounds, sticky accounting/response errors and quiet output
requiring separate external epoch qualification. Newly reset monitor never asserts
quiet without that qualification; zero local count cannot certify prior external
transactions drained. It drives no AXI signals and is NOT integrated into current
bitstream/CSR/reset tree. Three simulation groups PASS: stalls/handshakes, overflow/
unmatched completion/error stickiness and unqualified fresh-reset state.
Evidence `evidence/axi-read-observer-2026-10-23`. No hardware access or FPGA build.
Not an AXI protocol checker: no per-ID or beat-length validation, no end-to-end
PS drain proof. PMU AP0 access remains failed/unresolved; no retry performed.
Next simulate observer alongside actual DMA and independent bus accounting,
including completion/backpressure/reset cases, before any integration/build.
DDR writes remain NOT_ADMITTED; production gateware unchanged.


### 2026-10-23 — Passive observer with actual DMA simulation PASS

Extended existing real-DMA backpressure bench with passive observer and independent
AR/RLAST scoreboard comparison every cycle. All24 combinations of AXI delay0/3/17,
CRI stall0/31, responseOKAY/SLVERR and trigger0/1 PASS. No legal-run accounting
errors; completion drains to zero; SLVERR sets sticky observer response error and
prevents quiet even after drain. Negative isolated-DMA-reset test also PASS:
DMA IDLE does not clear the independently running observer's outstanding count,
which stays nonzero with quiet0 when PS responses are withheld. Production DMA
source/gateware unchanged. Evidence summary/pins:
`evidence/axi-read-observer-dma-2026-10-23/results.json`.
No hardware access or FPGA build; PMU AP0 access remains unresolved.
Next define observer CSR/reset epoch wiring and verify monitor-reset loss of
history against an independent owner model before planning a Dell build.
DDR writes remain NOT_ADMITTED; simulation quiet is not physical drain proof.


### 2026-10-23 — Observer reset-history test and status CSR prototype PASS

Added two read-only CSRStatus objects: outstanding and flags(accounting_error,
response_error,quiet,epoch_qualified). Qualification deliberately tied0; no host
arm/clear CSR, no allocated addresses, no production wiring/FPGA build.
Independent PS-side scoreboard retains accepted bursts while ResetInserter resets
the monitor: localcount0 does not certify drain, quiet/epoch remain0. Late RLAST
sets accounting error. Two simulation/CSR/RTL inspection test groups PASS.
Initial testbench manual count expected one request while ARVALID stayed high
for two cycles; replaced it with an independent per-handshake scoreboard.
Evidence `evidence/axi-observer-reset-csr-2026-10-23`. No hardware access.
Next integrate status-only observer into optional diagnostic gateware, preserving
normal CSR ABI; review reset/clock scope and generate HDL offline before a Dell
build. No epoch qualification mechanism or DDR write admission implemented.


### 2026-10-23 — Optional diagnostic DMA observer integration, HDL PASS

Added --dma-observer only for local-rtio-dma. Default Top/LocalRTIO constructors
retain prior behavior. Optional read-only bank6 exports outstanding0xa0003000
and flags0xa0003004; existing register map including analyzer unchanged by test.
Epoch qualification tied0, no arm/clear write CSR. Monitor shares sys clock/reset
with local RTIO: reset history loss remains explicit, not PS drain proof.
Two optional integration/map/invalid-mode tests PASS; existing physical-interface
AXI->CSR->RTIO/TTL simulation regression PASS. Standalone LocalRTIO Verilog
elaboration PASS; no full PS top or Vivado run/hardware programming.
Evidence/map/artifact hashes: `evidence/local-dma-observer-2026-10-23`.
Next inspect full generated PS-top HDL and explicit source bundle, then build
optional diagnostic on Dell under shared build lease. Do not replace normal
runtime or infer DDR admission from this instrumentation. PMU AP0 unresolved.


### 2026-10-23 — Dell observer build running; offline probe prepared

Existing job artiq-dma-observer-20261023 now RUNNING, no duplicate submission.
Prepared fixed four-read AP0 diagnostic CSR Tcl plus strict ordered-frame/map
validator. Exact address/order/count Tcl mock PASS; incomplete/duplicate/wrong
address/unexpected quiet or epoch assertions reject. Zero local count is decoded
only, never PS drain admission. Script intended only for verified observer image
under parent Genesys lease through mandatory normal restoration. No board access;
current normal runtime has no observer CSR bank and must not be probed with it.
Evidence `evidence/dma-observer-probe-offline-2026-10-23`. Next collect SAME Dell
job and verify reports/IP hashes, then integrate bounded candidate probe lifecycle.
DDR writes remain closed; full observer build/hardware still NOT_QUALIFIED.


### 2026-10-23 — Dell observer service interrupted; stale status corrected

Same job artiq-dma-observer-20261023 has no exit.json. Systemd journal records
Stopping/Stopped at09:41:18 and container SIGTERM; service inactive. Cause/actor
unknown, no automatic restart or duplicate job. Previous state.txt RUNNING was
stale, not build progress. Added status query combining service activity with
exit receipt; test rejects inactive RUNNING/WAITING, preserves terminal returncode.
Live query now INCOMPLETE_SERVICE_INACTIVE. Raw partial console/journal in
`evidence/dma-observer-build-interrupted-2026-10-23`; no build/timing/bitstream PASS.
Separately added full AXI->CSR simulation showing writes0xffffffff to both
observer status addresses cannot change counter/epoch/quiet; PASS0.742s.
No hardware access; baseline unchanged. Next inspect interruption coordination
before any resubmission; safe offline candidate-probe lifecycle work remains.


### 2026-10-23 — Dell observer implementation PASS; hardware NOT_RUN

Same session-held job finished exit0; retrieved files match remote SHA-256.
Strict input/IP/timing/DRC/route checker PASS. Setup1.728ns, hold0.003ns,
pulse2.5ns; internal no_clock/unconstrained endpoints0. Existing external I/O
coverage limitations no_input_delay1/no_output_delay5 remain; DRC only reviewed
RTSTAT-10 warning. BitSHA9649c982dc8353fc6f9b83f5397707143ff1dc4526fc104292aa1512cc2cafca.
Evidence/reports: `evidence/dma-observer-build-pass-2026-10-23`.
Staged candidate inventory combines this optional diagnostic PL/map with known
normal baseline firmware. Inventory is NOT executable yet: current parent hardcodes
prior release build-input binding. Next add explicit hash-bound build receipt and
read-only observer before/after runtime qualification, negative preflight tests,
then bounded physical candidate/restore cycle. Do not bypass current gate by
replacing the prior-release evidence manifest. No board access; normal runtime
unchanged. No DDR write admission, epoch qualification tied0.
