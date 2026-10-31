# Bounded mailbox publication callbacks — offline, 2026-10-31

Generic pit_word_slot accepts only12/24-word caller-owned aligned zeroed slots.
It enforces invalidate0 -> fence -> every payload word in increasing offset order
-> fence -> commit1. Step is consumed before store/fence; offset/sequence/value
errors and failed fence latch failure. Reentry during fence rejects without
changing outer operation. State/buffer/context must be exclusive and disjoint;
no reset/reuse or hostile pointer/state mutation is protected. Completion remains
stored after an extra rejected call; rejection does not roll back prior writes.

Target-only wrappers select actual image-owned sample_words/terminal_words with
NULL callback context, static single-use states and mbar1 memory-clobber fence.
Mailbox fields are union views of typed records and12/24uint32 words: same144B
ABI/offsets; word-array stores avoid aliasing across a uint64 member. Preparation
has no rollback: if terminal setup fails after sample arming, the sample remains
armed and a fresh retry is forbidden. No clear/recovery/write-to-device API.

96 PIT tests PASS. Actual sample/terminal C publishers produce byte-exact records
through slots under O2 and ASan/UBSan.42 wrong-offset injections at every stage,
four fence errors, early commit, omitted fence, bad count/alignment/nonzero slot,
invalid order, overrun, reentry and one-shot controls PASS. Guards around fake
buffers remain unchanged. Target wrappers/raw slot/allocation compile on MB;
native fat objects have no subword-store instructions, mbar1 wordb8220004 present.

These wrappers are not connected to the audit entry or PMU main. Standalone
objects are not full LTO/effective-address or physical visibility proof. No
hardware operations this turn; mapped plug/JTAG/UART/Ethernet remain available.
No external RAM access/consumer/no-wake/recovery/DDR admission. Prior mailbox
header pin is intentionally stale after union-view change; do not repin historical
snapshots. New custom closure would have26source/header files.

Next safe offline step: bind these exact mailbox callbacks and preparation into
a separate audit-only composition, resolve NULL raw context versus publication
contexts explicitly, then link/review all new slots, calls, layout and stack.
No runtime hook or physical trial until consumer lifetime and recovery qualify.
