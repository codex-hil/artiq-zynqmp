# Forwarded callback observation -> target status builder integration — offline

48 PIT tests PASS. New returning composition model forwards actual calls to
caller callbacks and logs called/value/return for each of three MSR observations.
Read/publish return failures determine sample operation outcome independently of
caller record fields. Real C metadata builder constructs record status/MSR fields;
it must agree with lifecycle status or metadata is rejected. Receipt publication
is attempted only after metadata success and remains a separate outcome. Plan,
capture/publication state and record must be initially unconsumed/uncommitted.
Duplicate whole-plan use rejected before callbacks.

New optimized+ASan/UBSan fixture runs six observation-failure/control cases using
real forwarding/builder/publisher. Emitted event/sample/receipt bytes match the
independent Python replay/producer, including failed-read output validity tests.
Test callbacks remain fake; no target execution or authenticated trace proof.
Receipt hashes remain EXTERNAL caller inputs, not calculated by target code.

Fresh full PMU LTO link/layout/no undefined symbols PASS. Entry and all five
forwarding functions pass scoped no-subword-store checker. Entry frame288,
observe44, disable28, read/write/barrier32. Largest internal entry+forwarder332
EXCLUDES underlying callback/caller/exception frames and is NOT a total bound.
Aligned stack assumptions and no-subword-opcode check do not prove every address
or platform visibility. New terminal still separate barrier/sleep/backbranch.

Audit entry now calls the returning composition model then nonreturning terminal;
retained only with -u, no vendor main/request hook, hardware callback or bound
mailbox. Constructor consumes observed MSR rather than prefilled record fields,
but malicious/lying/hung callbacks and mutated caller-owned inputs are outside
contract. Hash provenance, current IRQ after receipt write, boot/session lifetime,
AP0 visibility and independent hung-read recovery remain OPEN. Existing v3 gate
cannot admit this new layout; no new deployment manifest or bypass introduced.

No HW/JTAG/UART/network/reset/register access. MUST NOT DEPLOY; DDR NOT_ADMITTED.
Next safe offline work: fault-inject composition metadata/publication failures
and rejected/reentrant plan states, verify no receipt writes on metadata failure
and preserve separate lifecycle/build/publication outcomes before new flow gating.
