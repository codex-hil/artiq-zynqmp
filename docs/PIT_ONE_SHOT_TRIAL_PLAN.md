# One-shot PIT counter diagnostic plan — DRAFT / NOT ADMITTED

Scope: one nonce/image-bound record containing PIT0..3_COUNTER read twice in
fixed order. No preload/control/prescaler/watchdog/AIB/Si/flash/OTP/DDR writes.
New raw pit_mmio_read callback accesses exactly ffd40044/54/64/74; adapter enforces
eight returning loads and no retry. Return0 is not bus recovery. The callback is
MicroBlaze audit-opt-in only and not installed in normal runtime.

| Stage | Concrete action | Admission/evidence required |
|---|---|---|
| Offline image | Link exact callback + sequence adapter into new audit image | New source/header closure, actual LTO paths, load/store/ranges and complete stack/callback review; old18-source gate must refuse this new shape |
| Result allocation | Dedicated symbol-owned48-byte sample and96-byte terminal record |32-bit alignment/disjoint stack/heap/owners, init/lifetime and helper pins; no borrowed old fixed addresses |
| Recovery qualification | Owner-mapped plug supplies only devkit; control station separate | Separately bounded OFF then ON and cold normal runtime restoration with host/board identity; ON command alone is not a power-cycle/POR guarantee. No unvalidated countdown or unattended transient-session cycle |
| Ownership | Genesys lease plus unique plug reservation through entire test/restore | Re-identify owning station/cable/runtime, sufficient disk/reserve, no other board owner or infrastructure load |
| PMU entry | One explicit reviewed handoff, capture with actual IE transition observations | Runtime hook and exception/reset/fault-policy review; current standalone audit entry does not provide it |
| Consume result | External RAM access only during proven sleep lifetime | MB_SLEEP sample is not an interval lock. Exclude wake/reset/debug/exception or select separately reviewed non-RAM transport; sampled sleep alone never authorizes AP0 RAM |
| Recovery | On any uncertain outcome, no retry/fallback/private alias | Independent recovery effect must be qualified; host timeout cannot preempt stuck load and current debug restore is conditional |
| Restore | Normal PMU/FSBL/PL/CPU images and physical TTL/CoreDMA/debug/Ethernet | Exact input hashes, result logs and leases held through restoration; successful diagnostic without restore is failure |

Only the offline raw backend and plan are complete at this checkpoint. Physical
trial is NOT_RUN/NOT_ADMITTED. Do not run the disabled counter image, guess a
mailbox address, override fault policy or use DDR as an output channel. Counters
show changed/unchanged values only; no elapsed time/frequency/ownership inference.

Next authorized safe step: fresh audit-only LTO integration and negative static
controls for the concrete raw callback. Physical preparation then still requires
closing the recovery, entry, result ownership and consumer-lifetime rows above.

## Offline link checkpoint — 2026-10-30

Separate pit_mmio_composition_audit binds actual raw callback and links with11
custom C units. Layout/noUND/scoped word stores PASS;78 PIT tests PASS. Frames
292+52+0=344bytes internal subtotal only. Both old flow profiles reject this entry;
new full binding/flow mutation gate remains required. No HW/admission change.
[Evidence](../evidence/pit-mmio-linked-offline-2026-10-30/README.md).

## Instruction pins / library width gap — 2026-10-30

Nine exact bodies/712words pinned;16specific and712individual-word mutations
reject.82 PIT tests PASS. This is not full CFG/dataflow qualification. Library
memset retains byte-store paths; entry48-byte/SP+28 arguments require unresolved
alignment/path proof, so whole-path width remains unqualified. Next safe offline
fix uses explicit volatile32-bit initialization in pit_capture and a fresh link
with no entry-to-memset call. No admission/physical change. See
[evidence](../evidence/pit-mmio-flow-controls-offline-2026-10-30/README.md).
