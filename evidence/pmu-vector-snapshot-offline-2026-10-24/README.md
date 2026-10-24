# Opt-in PMU-local vector-map snapshot — 2026-10-24

No HW access. New --vector-snapshot requires explicit --lab-guard and defines
ARTIQ_PMU_VECTOR_SNAPSHOT only for that build. Ordinary builds leave the new
read disabled. PMU reads maintained PMU_IOMODULE_GPO0 through Xil_In32 locally;
no host/private AP0 register alias and no GPO write. Existing64-byte guard record
uses reserved[0]=version1 and reserved[1]=rawGPO0, remaining reserved words zero.
Publication barriers, nonce/MSR checks, ACK0/unresolved7f and sleep reentry remain.

Actual linked image PASS layout/guard checker. IMMffd4 + lwi r4,r0,16 at
0xffdc4734/38 yields0xffd40010, followed by store to record+48. Terminal sleep
now0xffdc474c. Record layout addresses shifted; old image/transport pins are
intentionally invalid. Header GPO0 bit0 meaning comes from prior source review.
No current vector mapping or ROM forwarding result is claimed.

Actual C host child test PASS for ordinary and opt-in builds, both good/bad MSR:
version/raw test value preserved only in opted-in case, ACK0 and non-return held.
Host fake read does not prove hardware register behavior. No independent device
access occurs. Inspected startup/app code has no textual explicit remap write;
linked/ROM/debugger initialization effects remain unproven.

Next offline: strict linked read-address checker with mutation controls and new
version-aware host parser/transport plus fresh manifests. Reject old profiles,
keep restoration bootstrap/reserves/lease. No physical attempt until those gates
pass; no remap writes, exception masking or forced private reads. DDR NOT_ADMITTED.
