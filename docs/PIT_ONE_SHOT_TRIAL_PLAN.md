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

## Explicit word-init revision — 2026-10-30

pit_capture48-byte aggregate clear replaced by12volatile32-bit writes through
aligned union representation. New LTO entry has no memset direct call;11 allowed
calls/initializerpins/fournegativecontrolsPASS;82 PIT tests PASS. Frame subtotal
now348NOTtotal. Library remains elsewhere; indirect callbacks/exception paths
are not admitted. New source/header/artifact closure required; old source hashes
must not be repinned. [Evidence](../evidence/pit-capture-word-init-offline-2026-10-30/README.md).

## New word-init bound gate — 2026-10-30

Explicit20source-header/7helper/3artifact gate and648project-word pins PASS on
actual ELF;89 PIT tests PASS with30file and19labeled+648word controls plus crossed
profiles. Deployment always refused; scoped width is not complete CFG/dataflow,
callback/library/exception coverage. Next isolated freeze/replay with new anchor.
[Evidence](../evidence/pit-mmio-word-gate-offline-2026-10-30/README.md).

## Frozen corrected audit — 2026-10-30

New20+7+3closure frozen as32files+inventory per copy. Two isolated relocated
replays identical;39negativecontrolsreject, required independent inventory anchor
checked before inputs. No HW or new physical permission; previous89-test result
dated. Next safe offline result-allocation step: image-owned mailbox symbols,
alignment and nonoverlap checks, no runtime hook or external RAM access.
[Evidence](../evidence/pit-mmio-word-frozen-offline-2026-10-30/README.md).

## Static mailbox allocation — 2026-10-30

Owned144-byte BSS allocation(48sample+96terminal) and symbol-derived layout
checks PASS;93 PIT tests PASS. No producer/consumer/hook. This closes only static
size/alignment/named-storage/stack placement for one ELF; dynamic heap exclusion
and initialization/lifetime/authenticity remain unproved. The mailbox changes
custom closure to22files; previous20-source gate does not certify its placement.
Next offline word-only bounded publisher callbacks and negative controls, no
external RAM reader. [Evidence](../evidence/pit-mailbox-allocation-offline-2026-10-30/README.md).

## Bounded mailbox publication — 2026-10-31

Word-slot callbacks enforce15/27step invalidation/fence/payload/fence/commit.
Owned target wrappers use NULLcontext andmbar1; mailbox144B union representations
preserve offsets while permitting word-array stores.96PITtests/nativeobjectsPASS;
no fullLTO/runtimebinding or physical publication/consumer qualification. Next
separate audit-only binding and complete layout/call/stack review,26custom-source/
headerclosure. [Evidence](../evidence/pit-mailbox-publication-offline-2026-10-31/README.md).

## Owned mailbox audit-root binding — 2026-10-31

Separate validated root prepares slots/binds sample and terminal writer/barriers,
then rawMMIO audit root;15customC LTO/noUND/16scopedwidth/layoutPASS.97PITtests
including21hostdoublebindingcasesPASS. Read/internalbarriersubtotals376/416NOTtotal.
External MSR/disable/hashorigin and runtime/consumer/recovery remain unqualified.
New27-sourceheaderclosure required. Next exact binding/fence/sequence mutations.
[Evidence](../evidence/pit-mailbox-binding-offline-2026-10-31/README.md).

## 2026-10-31 owned mailbox gate checkpoint

The separately pinned owned-mailbox profile passes on its actual ELF (16 bodies, 911 words, 38 inputs); 104 tests pass. See `evidence/pit-mailbox-flow-gate-offline-2026-10-31`. This adds no hardware admission. Next offline step is frozen relocated replay, retaining explicit refusal of deployment and all callback, reader lifetime and recovery gaps.

## 2026-10-31 frozen mailbox replay

Two isolated copies of the 40-file mailbox closure yield identical reports; 47 negative controls reject. See `evidence/pit-mailbox-frozen-offline-2026-10-31` for external anchor and replay recipe. No HW operations or admission. Next: offline qualification of concrete MSR/interrupt-disable callbacks, using a separate image/profile and preserving this snapshot. Request hook, digests, consumer lifetime and recovery remain unresolved.

## 2026-10-31 IRQ callback candidates

Standalone real MicroBlaze candidates and maintained interrupt-only helper compile PASS; 105 Python tests PASS. See `evidence/pit-irq-callback-offline-2026-10-31`. Candidates reject non-NULL context, observer rejects invalid alignment, compiler memory barriers bracket operations. No linked binding or physical claim. Next offline step is a separate root and fresh C/LTO link with linked helper inspection; retain old frozen profiles. No runtime hook or external PMU RAM consumer admission.

## 2026-10-31 linked IRQ root checkpoint

Fresh audit-only IRQ root binds actual callbacks and delegates to mailbox/MMIO roots; 106 tests PASS. Linked BSP C disable helper has two configuration-selected paths, unlike standalone .S evidence. See `evidence/pit-irq-binding-offline-2026-10-31`. No physical or deployment admission. Next: separate exact gate/mutation checks covering both helper paths/config read, bindings and relocated storage; preserve frozen prior closure.

## 2026-10-31 distinct IRQ gate

Actual IRQ image passes exact 20-body/1008-word profile with 41 pinned inputs; 113 tests PASS. Evidence `evidence/pit-irq-gate-offline-2026-10-31`. Both helper paths/config-read address pinned, live flag and exception behavior unobserved. No deployment. Next safe step is frozen relocated replay with external inventory anchor, keeping all old profiles intact.

## 2026-10-31 frozen IRQ checkpoint

43-file closure copied/relocated; identical isolated reports, 50 negative controls rejected. External anchor/recipe in `evidence/pit-irq-frozen-offline-2026-10-31`. No HW or deployment admission. Next safe offline dependency review: configuration flag feeding linked IRQ-helper branch, ELF initial bytes and BSP writes; live contents remain unobserved. Preserve frozen profiles and unresolved hook/digest/exception/lifetime/recovery requirements.

## 2026-10-31 initial IRQ configuration dependency

BSP and target compiler layout checks trace linked ffdd8b94 to initial UseMsrInstr=1 in ELF. 115 tests PASS; see `evidence/pit-irq-config-offline-2026-10-31`. No live or no-writer proof. Frozen profiles unchanged. Next offline requirement: canonical digest inputs/ordering and producer contract for actual image/sample bytes, replacing no existing profile until a separate implementation is reviewed. Physical admission remains closed.

## 2026-10-31 digest producer contract

Canonical bytes and ordering specified in `PIT_DIGEST_PRODUCER_CONTRACT.md`; host reference/vectors pass within 117 tests. Current caller-supplied hashes are not correlated by the target; no target producer or delivery protocol added. Next offline step: separate SHA-256 implementation candidate, vectors and word-store/stack review, then revised private snapshot pipeline. Existing frozen profiles and physical admission unchanged.

## 2026-10-31 fixed sample SHA candidate

Separate fixed-record C SHA-256 candidate passes 258 hashlib comparisons, rejection/sanitizer checks; 119 tests PASS. Standalone target object frame300, no undefined/subword-store findings. See `evidence/pit-sample-sha-offline-2026-10-31`. Not integrated/LTO-qualified. Next offline step: private snapshot capture/hash/publication API with failure controls, then linked review. Existing frozen profiles and physical admission unchanged.

## 2026-10-31 private digest pipeline candidate

Separate local-snapshot capture/hash/publication API and failure/reentry tests added; evidence `evidence/pit-capture-digest-offline-2026-10-31`. Not connected to existing lifecycle or terminal metadata. Target standalone frame156, expected three dependencies; next offline step is distinct C/LTO link and store/call/stack inspection. No physical admission or frozen-profile change.

## 2026-10-31 linked digest dependencies

Separate digest API/SHA retained in fresh19-unit LTO image; scoped calls/stores/constants/layout PASS. SHA path frame subtotal456 is not whole-stack proof. Evidence `evidence/pit-capture-digest-link-offline-2026-10-31`. Existing121 tests unchanged, no HW. Next safe offline step: separate lifecycle/composition consumes internally generated digest, final MSR after hash and explicit failure/substitution controls; existing root/frozen profiles remain unchanged.

## 2026-10-31 digest lifecycle candidate

Separate lifecycle uses internal capture digest and final MSR after hash/publication/copy.123 tests PASS, target standalone frame128; evidence `evidence/pit-digest-sleep-offline-2026-10-31`. Hash failure status5 is not terminal-v1 compatible. Next offline step: distinct composition with fail-closed/versioned hash-failure handling and correlation tests, then new root link. No HW or frozen-profile change; physical admission closed.

## 2026-10-31 digest terminal adapter

Separate adapter validates lifecycle/digest/observation consistency before output writes; explicit hashfailure5 rejected for v1.124 tests PASS, target frame140; evidence `evidence/pit-digest-terminal-offline-2026-10-31`. State has no nonce so same-session provenance remains caller premise. Next offline composition must own lifecycle state and record observations from one invocation, test correlation/order/failure before separate root link. No physical admission.

## 2026-10-31 same-invocation digest composition

Private composition generates digest and records MSR outcomes in one call; no sample-hash input, hash failure blocks terminal even after final IRQ override.125-suite tests plus strengthened focused tests PASS; evidence `evidence/pit-digest-compose-offline-2026-10-31`. Next safe offline step: separate concrete callback/ordered read/mailbox/nonreturn audit root and fresh LTO review. No HW/runtime/frozen changes or physical admission.

## 2026-10-31 concrete digest root

New concrete opt-in audit root and fresh24-unit LTO artifact PASS,126 tests,29 scoped stores/layout checks. Root frame336 and scoped SHA path792 are not full-stack proof. Evidence `evidence/pit-digest-root-offline-2026-10-31`. No HW/main hook/frozen changes. Next: distinct exact instruction/storage/constants/source gate plus mutants; retain physical admission gaps.

## 2026-10-31 exact digest-root gate

Actual ELF exact profile pins29 bodies/1737 words,64 SHA constants/owned storage and52 files; independent mutation/refusal controls. Evidence `evidence/pit-digest-root-gate-offline-2026-10-31`. Compile-count correction: preceding build used23 custom C units (not24), unchanged artifact. Next safe offline freeze/relocation replay with external anchor; no HW or deployment admission.

## 2026-10-31 frozen concrete digest-root replay

54-file closure copied/relocated, identical isolated reports,61 negative controls rejected. External anchor/recipe in `evidence/pit-digest-root-frozen-offline-2026-10-31`. Existing133 tests unchanged; no HW. Next safe offline step: concrete normal-path callback/call-stack analysis, keeping entry and exception/interrupt/debug/error/hang obligations separate. No deployment or PMU RAM reader admission.

## 2026-10-31 conditional normal-path stack

28-function graph with reviewed callback bindings yields conditional792-byte peak. Extra exact fence pin closes a scope omission in prior29-body gate without changing its frozen inventory; see `evidence/pit-digest-stack-offline-2026-10-31`. Not total-stack/exception admission. Next safe offline step: inventory exception/NMI/debug/error vector/handler dependencies and unbounded paths; no physical fault injection or deployment.

## 2026-10-31 static exception dependencies

Exact ELF vector/IRQ-table inventory finds concrete unqualified exception path through xil_printf byte stores (expected checker rejection). See `evidence/pit-exception-inventory-offline-2026-10-31`. No live fault/recovery or vector-policy change. Next offline step: separate word-oriented audit-only fail-stop receipt design, no printf/UART and no exception-disable shortcut. Normal-path792-byte result is not total-stack admission.

## 2026-10-31 exception receipt proposal

Distinct16-u32/64-byte fault schema and host supplied-word codec,140 tests PASS. No session/image/sleep/physical proof or handler binding. Contract `PIT_EXCEPTION_RECEIPT_CONTRACT.md`; evidence `evidence/pit-exception-contract-offline-2026-10-31`. Next offline step: portable word-oriented formatter/writer, fault/torn controls and target object checks, without changing vectors/exception policy. Linked printf gap still blocks exceptional-path qualification.
