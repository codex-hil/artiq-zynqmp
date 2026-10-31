# Owned mailbox audit composition binding — offline, 2026-10-31

Separate root pit_mailbox_composition_audit validates a fresh plan/adapter,
NULL capture/receipt contexts, nonce/digest inputs, supplied MSR/disable callbacks
and empty read/write/barrier callback fields. It prepares owned slots once,
binds only the four mailbox wrappers, then transfers to the existing raw-MMIO
audit root. The raw context remainsNULL; publication wrappers independently use
their static slot state. No PMU main/request hook, consumer or runtime deployment.
MSR/disable callbacks and image/sample digest origin remain external/unqualified.

Fresh15-custom-C-unit LTO/no UND PASS. Sixteen named function store-width checks
and mailbox layout PASS. Mailboxffddc980..ffddca10, two32-byte slot states at
ffddc938(sample)/ffddc918(terminal), disjoint BSS/named storage/stack. mbar1 remains
in fence. Current frame subtotal read28+296+52+0=376; capture barrier
28+296+32+28+32+0=416, NOT total stack/external callbacks/exception coverage.
Earlier348 subtotal belongs to previous root/build. Old instruction pins reject
new addresses/bytes; source/helper/artifact closure must be a new27-file profile.

97 PIT tests PASS. Host test uses explicit prepare/terminal/next-root/wrapper
doubles:21 cases check accepted binding, prepare failure, invalid/preselected/
consumed/context/adapter/digest/callback cases and NULL plan. Rejected plans
unchanged and never enter raw root. O2 and ASan/UBSan PASS. Initial fixture
-Wclobbered warning fixed by static loop-state across longjmp, not disabled.
Separate previous tests exercise actual publishers/slots; the full target chain
has not executed on host or hardware. No physical operation this turn.

Next safe offline step: exact new-root/slot/wrapper address binding and fence/
sequence mutation controls on this ELF, then new complete source/helper closure.
No interpretation of static PASS as physical publication/no-wake/recovery proof.
External RAM consumer, runtime hook and DDR admission remain disabled.
