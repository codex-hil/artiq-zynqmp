# Sticky observation lifetime model — 2026-10-28

Offline caller-fed state model only. Wake/reset/debug/exception/transport unknown/
ownership loss invalidate the session. First reason is retained; a later sleep
sample cannot revive it. Active/failed/malformed/wrong-session observations and
unknown events also invalidate. Closing is irreversible. Every report is a copy
and always refuses continuous sleep, RAM access, authentication, recovery and
deployment. Internal Python state is not a security boundary against hostile code.

Four test methods cover all2801 event sequences of length0..4 over six invalidating
events plus a sleep sample, bad input/transport handling, mutated-report isolation,
late-sleep nonresurrection and closed-session rejection. Synthetic trace is
explicitly fake. The model assumes only delivered events: absence of a reported
event does not establish absence of a physical event or a no-wake interval.
No capture/backend/executor, hardware access or static gate change.

Next safe offline step: correlate the modeled session with supplied terminal
receipts and image/session identifiers, retaining separate authenticity, lifetime
and admission results. Such correlation cannot establish physical sleep/recovery.
