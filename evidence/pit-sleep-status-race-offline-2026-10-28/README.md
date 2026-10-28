# Sleep status semantics and interval race — 2026-10-28

The exact [AMD UG1087 register entry](https://docs.amd.com/r/en-US/ug1087-zynq-ultrascale-registers/GLOBAL_CNTRL-PMU_GLOBAL-Register)
(1.11,2025-06-20) was retrieved through the PMU_GLOBAL module link after the direct
route failed. It confirms MB_Sleep bit16 is read-only and encodes active=0,
sleep=1 at0xffd80000. Dont_Sleep bit0 requests wake while asleep with interrupts
disabled. This supersedes only the earlier retrieval/field-semantic uncertainty,
not the remaining transport, no-wake lifetime or recovery qualifications.

Inference: a sampled state is not a lock covering the subsequent RAM transaction.
The abstract model enumerates eight endpoint-sleep schedules; seven contain an
interior wake. It is a counterexample to polling-only inference, not actual
hardware timing, a measured failure or proof that each schedule is reachable on
this particular board. No status polling, transport command or HW access occurred.

Pinned script review: existing RAM probe selects PSU/AP0 and reads fixed RAM
without proving sleep acquisition; it must not be reused as a qualified observer.
The restoration script selects PMU debug, stops execution, verifies suspended/r0,
downloads and resumes. It is conditional recovery that changes execution, not a
passive observation or arbitrary hung-load escape. Existing physical results and
failure evidence remain intact. No existing script was edited or executed.

Next safe offline step: specify a status-only observer contract with exact
identity/lease/route/no-write/no-RAM limits and a fail-closed admission predicate
that rejects sampled sleep as permission for RAM access. No executor or hardware
window follows; independent recovery and interval ownership stay open.
