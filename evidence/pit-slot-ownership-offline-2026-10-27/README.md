# PMU RAM slot ownership and consumer-path review — offline

21 PIT tests PASS. Fresh layout-only 48-byte BSS probe retained in a new PMU
LTO audit link. Symbol checker PASS; eight malformed/overlap controls rejected.
Slot ffddbe58..ffddbe88, BSS ends ffddbeb0, stack ffddc7cc..ffddd7d0; extension
table ffddf6e0..ffddfae0. Sized request ffdd8160/32, guard ffdd81a8/64 do not
overlap. ELF segments show the slot within zero-file-tail BSS. This is link
ownership only, not proof that startup ran/zeroed it or no ROM/debug agent writes.
Probe has no runtime reader/writer and is not a selected physical mailbox.

Previous C-capture audit has request ffdd8160, guard ffdd81a8, stack
ffddc79c..ffddd7a0. Existing probe_pmu_lab_guard.tcl hardcodes older sleep
request ffdd7f20/guard ffdd7f68 and older vector addresses. Those offsets are
NOT valid for this link. No old pins/manifests or helpers were changed/reused.
Fresh image-specific symbol binding and before-lease/under-lease artifact
verification are required for any future deployment; layout changes invalidate
old address assumptions. Never pick an apparent free gap by inspection.

## Access and lifetime

Existing host consumer uses PSU target selected by exact cable and
mrd -address-space AP0. Historical guard procedure reads RAM while PMU sleeps;
prior running/non-sleep PMU accesses timed out. Therefore sampling PIT locally
must finish BEFORE the PMU enters the documented sleep state used for external
RAM access. Reading timers from host or reading the slot while PMU runs is not
an approved shortcut. External record access needs a new image-bound helper;
none is implemented or run here. DATA_SYNC compilation alone does not prove
visibility across PMU/sleep/AP0 or visibility of the final commit.

Fresh nonce and one-shot state must be tied to one boot/image/session. Loading
or resetting firmware can erase local state and permit accidental reuse; a new
Python object is not a new physical epoch. Initial BSS zero checks only support
freshness in a qualified lifecycle, not persistent uniqueness. Concurrent ROM,
exception/reset flows and independent stalled-read recovery remain unqualified.

Audit ELF reuses historical prohibited vector-v1 guard objects: MUST NOT DEPLOY.
No hardware/network/JTAG/UART/reset/register access. DDR NOT_ADMITTED. Next safe
offline work: design a new counter/sleep guard profile without GPO0 reads, with
source-bound symbol extraction and local capture-before-sleep ordering tests.
Its physical backend/admission must remain disabled until fault/recovery and
consumer visibility obligations are resolved.
