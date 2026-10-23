# Sleep guard candidate integration — 2026-10-23

Fresh manifest copies bind the specifically changed sleep image, actual symbols,
disassembly and current helper hashes. Historical manifests were not modified.
The gate requires exact sleep terminal 0xffdc4738 and sleep-reentry mode, plus
unchanged fixed request/record addresses. Historical guard manifest is rejected.

Full normal-runtime and nested trained-observer preflight PASS offline. Five
guard gate/transport/recovery tests and three guard C/static-flow tests PASS.
Real Tcl mock injects first post-publication guard-record read timeout and proves
exactly one failed access followed by unwind: no retry or alias. Ordinary four
sample budget and exact nonce/state/MSR/ACK rejection controls remain in place.

No hardware access or new runtime health check. A physical trial must use the
existing parent wrapper, shared Genesys lease, real storage reservations and
explicit PMU debugger bootstrap followed by full baseline restoration. This is
a changed candidate, not an unchanged retry. Wake inputs may defeat sleep
residency: failure to read a coherent record is FAIL, never quiescence proof.
On the first timeout unwind to restoration; no forced/alternate RAM access.
ACK=0 and all unresolved obligations remain; destructive DDR NOT_ADMITTED.

Next: bounded parent-owned physical capture/restoration when device lease and
storage admit it. No Si/SD/flash/OTP/Kasli changes are part of this candidate.
