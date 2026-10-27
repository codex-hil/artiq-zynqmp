# Strict RPU-master AIB callback protocol in C — 2026-10-27

Offline only. New C function accepts explicit read/write-request/ticks callbacks;
no MMIO addresses or hardware backend supplied, no firmware/build integration.
Only nonzero subset of RPUM0/1mask30000 allowed. Poll budget1..1024 and finite
monotonic elapsed tick deadline. Initial selected REQ/ACK clear required; bracketed
snapshot preserves raw TYPE and unrelated request bits. One request write at most.
Full selected ACK, exact held request and unchanged TYPE required before reporting
DRAIN_OBSERVED. No resume/clear/release action; destructive_test_allowed always0.

Actual C optimized GCC and ASan/UBSan execution PASS. Fixtures cover full ACK,
partial/missing ACK timeout, write-error ambiguity, read failure after write,
lost USB baseline bits, changed TYPE, stale selected ACK, backwards clock,
request-bracket race, deadline before write and during ACK, invalid backend/mask/
budget. Mocks assert at most one write and no automatic clear. Five Python model
tests also PASS; C adds monotonic time and callback-error distinctions.

Failure does not imply physical held isolation: write errors may mean request
accepted or rejected, other writers can change registers, and callbacks can block.
Bounded callbacks and exclusion of competing software/ROM writers are caller
obligations. Req bracketing cannot detect ABA. Timestamp errors after request do
not undo it. Snapshot/ACK is not a boot/session receipt; a future integration must
bind exact image/boot/request sequence and positive source-core state separately.
No global DDR ownership, ROM/reset containment or full-master coverage proved.

Next offline cross-compile this standalone component with the actual MicroBlaze
recipe, audit object call/stack footprint, and add transport/session binding before
choosing any real register backend. No AIB writes/HW validation admitted yet.
Normal runtime remains untouched. Full DDR NOT_RUN/NOT_ADMITTED.
