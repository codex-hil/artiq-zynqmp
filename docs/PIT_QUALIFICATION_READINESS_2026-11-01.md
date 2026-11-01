# PIT/exception readiness and bounded qualification proposal —2026-11-01

SPDX-License-Identifier: LGPL-3.0-or-later

Status: OFFLINE COMPONENTS REVIEWED; NEW HARDWARE ENTRY NOT_ADMITTED.
This document is a proposal and decision record, not an execute switch. No device
access, power action, reset, firmware/vector change or PMU RAM read performed here.

## Readiness matrix

| Item | Evidence/status | What this does NOT establish |
|---|---|---|
| Fixed PIT address/order and one-shot model | Existing returning collector/adapter/capture tests | A hung load can return or be preempted |
| Sample SHA and terminal correlation | Same-invocation internal digest composition; tested failures | Trusted image delivery, live acquisition or sleep |
| Concrete digest audit root | Separate LTO/exact-body/storage/SHA gates, frozen replay | Generic CFG/full exception stack/hardware entry |
| Minimal digest+fault-slot link |19-source link fits unchanged4100 stack/fixed service table,2288 gap | Old exact-root/stack profiles apply to this new image |
| C fault formatter/slot | Word stores/fences/one-context tests and scoped linked checks | Valid incoming exception stack or nested-fault exclusion |
| Stackless assembly object/link | Exact object and synthetic non-PMU link, no stack/calls/vectors | Installed PMU vector, notification equivalence or recovery |
| Latest software suite |155 tests PASS at interleaving checkpoint; later source reviews only | Repeated or physical verification |
| Normal physical baseline | Dated2026-10-30 normal runtime/TTL/DMA/debug/network PASS | Current device availability or new-handler behavior |
| Plug ownership/load | Owner said devkit only; prior ON and status evidence | Present physical mapping, actual OFF/POR/cold recovery |
| Shared leases | Genesys flock + persistent plug token protocol defined | Lease currently free or station/device reachable |
| Active vector/ROM route | UNKNOWN; BSP0xffd00000 vs ELF0xffdc0000; WO remap | Readback or inferred state from successful runtime |
| Exceptional byte stores | Current printf path concretely contains stack sbi | Whole-path u32-only behavior |
| Reader lifetime/recovery | NOT_QUALIFIED; sampled sleep not an interval lock | Any safe external PMU RAM read after fault/hang |

Detailed sources: PIT_ONE_SHOT_TRIAL_PLAN.md, PIT_VECTOR_SELECTION_TRACE.md,
PIT_ROM_LOADER_REVIEW.md and dated evidence directories. Historical data is not
promoted to current state. Preserve original failed RAM-overlap link as evidence.

## Phase A — authorized read-only station readiness, next safe step

This phase introduces no new firmware or exception policy and no power switching.

1. Read current coordination/local instructions; identify Optiplex by hostname,
   user and local source/artifact paths. Do not assume stale LAN/tty enumerations.
2. Acquire Genesys lock `/home/codex-hil/.cache/genesys-210383B7F02DA.lock`
   nonblocking. If busy, do not access UART/JTAG/network/reset; release partial
   claims and record owner/contention. Never delete/preempt another lease.
3. Query public plug reservation. If free, reserve unique thread/purpose through
   `/home/codex-hil/.local/bin/hil-plug`; keep token private0600, use CLI only.
   If busy, no plug status/power calls and no forced reservation removal.
4. Under both claims, read plug status only and inspect owning-station/cable/UART
   identity using existing established paths. No PMU register/RAM reads, stop,
   download/reset/JTAG state change, GPO read/write, or power action. A reported
   relay state is not measured voltage/POR. No repeated sleep-status polling.
5. If exact normal runtime identity/address is established without changes, use
   bounded existing non-destructive normal status/network checks under lease.
   If identity is ambiguous, stop that dependent probe and record unknown.
6. Record present readiness/disk/artifact/lease evidence and release plug token
   and Genesys lock. No unattended power-cycle/watchdog setup or background task.

Phase A success only updates present availability; it does not admit later phases.
No need to ask the user to reconfirm already supplied devkit-only mapping unless
new evidence contradicts it, but do not switch power in this phase.

## Phase B — separately bounded recovery qualification, NOT_RUN

Required before any trial that may hang the PMU: preserve exact normal PMU/FSBL/
PL/CPU0/CPU1 artifacts and sufficient restore reserve; confirm target-only load
and control infrastructure independent. Review explicit OFF then independent ON
operations as a separate window with both leases held. No transient shell timer,
TOGGLE, implicit watchdog or assumption that broker ACK means physical switching.
Do not cut controller power. Actual cold-state/POR and normal restoration must be
observed independently and recorded, or remain unknown.

Restore through the already documented normal boot path only; do not use new
PIT/exception candidates to qualify recovery. End with bounded normal identity,
TTL/CoreDMA/debug/Ethernet validation and leases released. On timeout/uncertain
power or failed restoration, no retry cascade or firmware experiment; report exact
failure and required physical/operator step. Prior power-on is not this test.
Phase A is not authorization to silently perform Phase B.

## Phase C — policy/entry mechanism decision, NOT_ADMITTED

Before proposing an executable handler trial, establish independently how the
PMU reaches selected exception code. Do not infer WO latch state, blindly write
GPO0, relocate vectors, or repurpose ROM hooks. Explicitly review which normal
error-notification effects a separate audit image would preserve/change; the
unreferenced assembly candidate intentionally does not reproduce those effects.
This is a substantive policy decision, not a routine formatter/link fix.

A reviewable candidate trial must state exact image/slot addresses, entry method,
changed policy, permitted trigger, asynchronous/nested-fault limits, independent
recovery and safe result transport. No such executable trial is currently ready.
Do not request blanket hardware approval or claim phase B closes these gaps.

## Phase D — future isolated entry/result trial, NOT_RUN/NOT_ADMITTED

Only after B/C and normal baseline restoration can a bounded trial be considered.
No flash/OTP/SD/Si/other FPGA/DDR writes. No production error-policy removal to make
static tests pass. No APB PMU RAM read without independently established safe
sleep/no-wake lifetime; the proposed busy-loop fault receipt does not provide it.
No hung-load recovery guarantee from host timeout, IE clear, mbar or a valid hash.
If safe result transport cannot be established, the trial stays NOT_ADMITTED.

## Stop criteria and reporting

Hardware busy: no access; continue only independent already approved offline work.
Fault/missing wiring/voltage/identity or required human action: name the concrete
condition and next operator step; no automatic CONTINUE for that dependent block.
Otherwise the next safe authorized action is Phase A read-only readiness only.
No new handler or counter-image execution is authorized by this document.
