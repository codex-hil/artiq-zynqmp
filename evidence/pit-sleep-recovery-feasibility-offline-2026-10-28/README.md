# Sleep observation / recovery feasibility — 2026-10-28

Offline review only, no register read or policy change. Pinned local sources and
line/page references are in review.json. UG1085 v2.5 p113 requires sleep before
external APB PMU RAM access and warns about starvation/hang while the CPU runs.
The IPI0 loading protocol (pp141-142) is cooperative: its interrupt handler must
execute to reach sleep. It cannot be assumed to rescue an arbitrary stuck local
load. A host process deadline only ends host waiting. Existing halt/r0 restore
has historical successes but is not qualified against every stuck transaction.
POR and SRST have different retention effects; do not substitute or trigger them
without a concrete qualified recovery/ownership/restoration plan.

New candidate: vendor pmu_global.h defines PMU_GLOBAL.GLOBAL_CNTRL at0xffd80000,
MB_SLEEP bit16/mask0x10000. This is encoding evidence only. Exact UG1087 semantics
(read type, effects, synchronisation and permitted access paths) remain unverified.
Official page retrieval failed; search results for Versal PMC are another device
and were excluded. The header must not silently become a qualified sleep test.
Even a valid sampled sleep bit would leave a race: wake/exception can occur
before or during subsequent RAM access. Pre-sleep receipts and repeated polls
cannot substitute for a justified no-wake lifetime and independent recovery.

No absent-mechanism claim: a candidate exists, but qualification is incomplete.
Next safe offline work obtains the exact register definition and reviews existing
observer transport code, then models the status/read race. No hardware poll,
IPI/reset/watchdog/AIB/interrupt-policy change, RAM shortcut or executor is added.
PIT image remains NOT DEPLOYABLE and destructive DDR NOT_ADMITTED.
