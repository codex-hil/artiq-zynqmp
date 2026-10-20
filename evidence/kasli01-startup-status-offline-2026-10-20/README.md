# AUX startup failure status instrumentation (offline)

Added bounded read-only DAP telemetry in the existing external AUX exception
path, before restoration and while the parent still holds both board leases.
The generated script requires the exact Genesys cable and unique PSU target.
It reads seven selected single-word CSRs without reset, snapshot-trigger or
link-enable writes. Samples are sequential and post-failure: they do not prove
the exact earlier failing poll or qualify the link.

The original exception is re-raised even if telemetry fails; restoration
remains in the existing outer finally. External status is now explicitly FAIL
on that path instead of the previous NOT_RUN initialization.

Two offline tests PASS: selected read-only operations/identity order, and
rejection of missing/duplicate/out-of-range samples. Generated against the
actual qualified satellite map; existing external KASLI01 preflight PASS.
Physical telemetry capture NOT_RUN. Next repeat the bounded external-idle
trial once, then use status evidence to decide whether physical SFP inspection
is required. No hardware was accessed for this instrumentation checkpoint.
