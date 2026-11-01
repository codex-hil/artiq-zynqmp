# PMU admission after practical power recovery — 2026-11-01

SPDX-License-Identifier: LGPL-3.0-or-later

Practical OFF/ON and normal restoration PASS. New PIT/exception execution remains
NOT_ADMITTED. No hardware accessed for this reconciliation.

| Requirement | Current evidence | Remaining limit |
|---|---|---|
| Target-only power control | One explicit OFF and separate ON; network disappears and returns, exact JTAG cable returns | No electrical/POR waveform or PMU-fault scenario measured |
| Normal restoration | Pinned normal volatile JTAG load, physical TTL/9 CoreDMA runs/analyzer/MonInj and Ethernet PASS | Boot source still older image; no persistent image update |
| Ownership/storage | Shared board and plug claims through restoration, released; real reserve allocated/released | Reacquire and recheck each future window |
| PMU exception routing | Source/ELF/BSP trace | Active ROM/RAM route remains unknown |
| Error notification | Concrete vendor versus audit source comparison | Audit candidate does not preserve vendor notification |
| Result transport | RAM format/store/host parsing evidence | Busy loop is not safe sleep; no continuous no-wake interval or alternate transport qualified |
| Fault recovery | Practical healthy-board switching/restoration | Hung-PMU/fault-trigger case not tested; host timeout does not preempt MMIO |

The practical test supersedes the earlier demand for physical voltage observation
as a prerequisite for this limited switching test. Such observation is still
needed for electrical/POR claims. Do not require another identical power cycle
just to reconfirm this result. It does not admit a new handler or RAM reader.

Vendor software exception source saves ESR/EAR at0xffd80050/54, writes the literal
0x10000000 to0xffd6033c and loops. Vendor hardware exception source prints special
registers first, then uses RMW for persistent storage5/HW_EXCEPTION_RECEIVED0x2,
then FWERR1 mask0x20000000 set and clear, then loops. These are source effects;
register side effects, successful notification and live reachability are separate.

The unreferenced audit assembly instead publishes its64-byte RAM slot, omits EDR,
and loops. It performs none of those persistent/error-register writes. Therefore
removing printf alone or binding this entry to a vector would change observable
policy; source-level word stores and no-stack properties cannot prove equivalence.

Next bounded offline work: resolve the exact vendor RMW helper, addresses/access
semantics and ordering dependencies, then state requirements for preserving the
notification effects. Do not implement or install a replacement as part of that
review. Keep active vector route and safe result transport as independent gates.

Evidence: `../evidence/pit-post-recovery-review-2026-11-01/review.json` pins the
successful recovery records and relevant vendor/candidate sources. Assertions
against practical result/claims/tests PASS. Prior155 PIT tests were not rerun;
no implementation changed and no new build was needed.
