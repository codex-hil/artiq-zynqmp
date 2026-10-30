# Image-owned mailbox allocation — offline, 2026-10-30

New pit_mailbox_audit C/H defines one aligned8-byte BSS object144bytes: sample
record48bytes atoffset0, terminal record96bytes atoffset48. C11 assertions bind
sizes/offsets. Explicit MicroBlaze/MMIO-audit opt-in and linker retention only;
no producer, publication callbacks, runtime entry hook or external RAM consumer.

Fresh12-custom-unit LTO link/no UND PASS. Symbol-derived allocationffddc520..
ffddc5b0, samplesffddc520, terminalffddc550. Addresses are descriptive artifacts,
not fixed-address probe configuration. Checker requires aligned144-byte BSS in
one writable zero-init load tail, within BSS and below stack, no sized storage
symbol collision, and any declared heap interval disjoint. Stackffddcecc..
ffddded0,6160bytes below extension table; telemetryffdd8860/32 disjoint. No heap
bound symbols exist, so dynamic heap exclusion explicitly remains unqualified.
Zero-init segment is a loader obligation, not observed successful initialization.

93 PIT tests PASS, including wrong size/alignment/storage type/BSS bounds/missing
symbols/stack/other owner/heap/incomplete heap/duplicate symbol/read-only segment
refusals. All648 project instruction pins also match unchanged code; this does
not extend the previous20-source gate to certify the new mailbox. New C/H would
require22-source closure plus mailbox helper pins. Older manifests/frozen copies
are preserved; they carry no mailbox ownership qualification.

No HW access/programming/PMU RAM read, no no-wake/recovery/DDR admission. Dynamic
allocations, callbacks and unlisted aliases are outside static symbol proof.
Next safe offline step: word-only bounded publication callbacks for this owned
allocation, with exact offset/bounds/one-shot/error/reentry controls, before
connecting anything to the audit composition. External consumer remains disabled.
