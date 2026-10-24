# AIB observation PASS / mandatory restoration FAIL — 2026-10-24

Candidate trained observer PASS; overall FAIL/restoration FAIL preserved.
Eight fixed post-guard reads: REQbefore/after0x00c00000, ACK0x00c00000,
TYPE0x19cf000f in both samples. Selected RPUM0/1 bits0x30000 were clear.
Other asserted request/ACK bits retained; do not interpret full register as zero.
No AIB request/type writes, forced/private alias reads or retries.

Mandatory restore selected exact PMU and stop/suspended check completed, then
baseline ELF download failed at0xffdc0000: MicroBlaze data register read error.
No bootstrap marker, normal reset/load/debug/Ethernet stages did not run. Thus
normal runtime is NOT_RESTORED/UNKNOWN; PMU may be halted/partially modified.
No unchanged download retry, alternate memory access or reset bypass attempted.
AIB observation does not establish cause of debugger failure. Prior restoration
PASS remains historical, not current health evidence.

Shared lease covered candidate/attempted restoration and wrapper then released
it. Storage reserves were allocated and released before restoration; no storage
failure in this physical attempt. Initial separate invocation was rejected before
hardware due insufficient reserve headroom. Own completed historical result was
verified/copied to root disk and old path kept as symlink; see ../aib-storage-
admission-2026-10-24. Thresholds unchanged, no other thread/tool data removed.

Recovery requires physical board power cycle before a fresh leased normal-runtime
bootstrap/test. Do not reuse Genesys as healthy or run another diagnostic until
that recovery succeeds. Do not change Si/SD/flash/OTP/Kasli or AIB policy.
Full DDR NOT_ADMITTED. Failure evidence/raw bytes preserved without reinterpretation.
