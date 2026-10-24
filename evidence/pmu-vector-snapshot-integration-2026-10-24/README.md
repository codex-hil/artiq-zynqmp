# Vector snapshot integration preflight — 2026-10-24

Offline only. Explicit manifest profile vector-v1 requires terminal0xffdc474c,
request0xffdd7f40 and record0xffdd7f88. Actual ELF is bound to regenerated nm/
objdump and helper hashes. Guard checker requires exactly one load in the guard,
at0xffdc4738 (lwi r4,r0,16) preceded by IMMffd4, then store to record+48 and
version1 at+44. Altered read base/offset/store/version are rejected. No GPO writes.

Tcl transport selects only the two named literal layouts (sleep or vector-v1);
unknown profiles rejected. New parser requires record version1, trailing zeros,
unchanged nonce/sequence/MSR/ACK obligations and stable GPO0 across coherent
samples. It reports bit0 as sampled ram_vector_remap, never DDR ownership.
Legacy parser rejects new version, vector parser rejects legacy fields.

Nine guard host/static/gate/transport/recovery test cases PASS, including real
Tcl mock for both address layouts, incorrect profile/version, inconsistent raw
GPO0, changed read address and first-timeout unwind. Full nested parent preflight
PASS with fresh manifests; historical captures/manifests untouched. Source pin
changes deliberately invalidate old manifests. No hardware or fresh health check.

Next bounded physical vector-v1 capture through existing parent wrapper, shared
Genesys lease, storage admission/real reserves, exact PMU bootstrap and full
normal runtime restoration. Do not force/remap/read private AP0 alias, repeat a
timeout, or reuse stale manifests. DDR remains NOT_ADMITTED regardless of bit0.
