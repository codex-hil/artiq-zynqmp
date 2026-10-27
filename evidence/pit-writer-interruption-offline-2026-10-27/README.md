# PIT publication writer interruption model — offline

17 PIT unittest cases PASS. New writer tests cover exact 15-callback sequence,
60 interruption controls (15 positions, failure before/after effect, fresh or
previous-session slot), invalid source, duplicate/reentrant entry, and buffered
payload visibility with a deliberately omitted second barrier negative control.
Sequence: invalidate commit; barrier; eleven payload words; barrier; commit=1.
Only byte offsets are passed to injected callbacks: no physical addresses/MMIO.

All failed callback attempts consume the writer and return VISIBILITY_UNKNOWN.
No clear/retry/rollback occurs. In particular, a commit write that takes effect
then reports failure leaves a valid receipt even though the writer reports an
error. Error is not proof of cancellation. Never repeat that attempt blindly.
Successful callbacks also do not prove hardware visibility: the intentionally
broken barrier callback returns success but leaves a stale nonce, which the
receipt decoder rejects in the buffered model.

These are sequential fake-memory tests, not a processor memory-model proof.
Barrier effects, atomic word stores, fresh never-reused nonce/session, ownership,
reset lifetime, consumer acquire ordering and coherent/DAP visibility remain
external unqualified obligations. The Python one-shot flag is neither a lock
nor persistent uniqueness. A new object cannot establish a new physical epoch.
No barrier opcode, firmware hook, transport or physical adapter was added.
No HW/reset/network/register access; DDR remains NOT_ADMITTED.

Next safe offline work: implement the same publisher contract in C with fake
write/barrier callbacks and target linked-order review; separately qualify the
PMU/DAP memory attributes and recovery before proposing any hardware capture.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
