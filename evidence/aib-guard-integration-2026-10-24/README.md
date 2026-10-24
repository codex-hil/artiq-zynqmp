# Parent-owned post-guard AIB observation — 2026-10-24

Offline integration only, no HW access. New explicit boolean aib_observation
requires the existing guarded no-master trained window. Parent requires exact
probe/decoder pins, passes --aib-observation to its inherited-lease child. Child
rejects AIB without guard. Order is checked boot/OCM/no-master/master captures,
guard request/record, then eight fixed AIB reads. No AIB request/type/reset writes.
Current guard firmware reused exactly; no extra PMU read or build introduced.

Full nested preflight PASS with fresh manifest copies and current source hashes;
historical manifests/evidence untouched. Two integration tests PASS: full preflight,
nonboolean/missing-pin rejection, actual child AIB branch timeout executes exactly
one helper call and propagates failure. Two actual Tcl/decoder tests, one request
legacy dispatch test and six parent lifecycle tests PASS (11cases total).
Any failure still reaches parent's mandatory baseline restoration and preserves
child raw output; no local retry/alias exists.

Read-only observation may show preexisting isolation requests/ACK/type but does
not reserve ownership or establish RPU/core/ROM/drain exclusion. selected inactive
is an observation, never permission for an AIB write or destructive DDR.

Next one bounded changed-observation physical run via parent wrapper, shared
Genesys lease, real block reserves and explicit PMU debugger bootstrap/full
normal restoration. If hardware busy or space insufficient, do offline work.
No Si/SD/flash/OTP/Kasli/AIB writes. DDR NOT_ADMITTED regardless of captured bits.
