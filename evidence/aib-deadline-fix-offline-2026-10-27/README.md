# Backend recheck deadline regression and fix — 2026-10-27

Offline only. Before change, actual adapter/session/protocol fixture delayed the
ninth read (backend REQ recheck) by100ticks against10tick budget. Transport write
was still invoked once and later protocol reported timeout. Reproduced behavior,
prior source hashes and local binary hash retained; not physical timing evidence.

Changed callback ABI passes original start/timeout into write_request. Backend
checks elapsed time at entry and again after REQ/TYPE rechecks, before transport
write. Pre-dispatch expiry returns distinct EXPIRED code; backwards clock returns
CLOCK; generic transport errors are mapped to IO_UNCERTAIN and cannot masquerade
as cancellation. Protocol preserves status and one-shot consumption, no retry.

Actual optimized+ASan/UBSan tests PASS for delayed recheck=>zero transport writes,
normal success, backwards clock, clock-read failure, negative transport error
code after write, and already submitted write completing late=>one retained write/
timeout/no rollback. Existing adapter/session/strict fixtures also PASS (four test
suites, each optimized+sanitized). No real MMIO/backend/firmware integration.

Boundary remains explicit: time checked immediately before dispatch cannot cancel
an in-flight bus transaction or preempt a blocked callback. Acceptance may occur
later in a real transport; callback-level transaction deadlines and completion/
uncertain-effect policy still need implementation/qualification. AIB request must
not be blindly cleared after failure. Current code supplies no physical transport.

ABI and code changed: previous MicroBlaze callback/stack/table audit is historical,
not applicable to new build. Next rebuild exact target/audit link, check caller/
callee argument passing and stack, then bounded real-transport contract before
any deployment. Current normal runtime untouched; DDR NOT_ADMITTED.
