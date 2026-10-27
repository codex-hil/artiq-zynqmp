# Normal-only PMU restore qualification plan — 2026-10-27

Offline preflight PASS, hardware NOT_RUN. qualify_pmu_restore_hw.py defaults to
no hardware; --execute requires explicit pinned manifest/server/port/interface.
Scope forbids guard,AIB writes and retries. Exact normal artifacts and15 helper/
database pins checked before and after shared Genesys lease acquisition. Real
storage reserve held through bootstrap, released before normal load. Source
changes invalidate plan; old failure/candidate manifests remain historical.

One new r0-gated PMU bootstrap, then normal PS/FSBL/PL/CPU load, TTL/CoreDMA/
analyzer/MonInj and Ethernet. Seven exact ordered markers required before load.
Any bootstrap/register/download failure prevents later steps and preserves logs;
no repeated download, force, alternative mode or implicit reset fallback. A load/
test failure is FAIL with normal_runtime_verified=false; operator recovery may
be required. No loop attempts to manufacture PASS after a failure.

Three wrapper tests and four actual-Tcl recovery tests PASS. Mocked execution
proves failed bootstrap invokes only one child and never normal load. Mock result
hardware_executed=true belongs to fake execution inside unittest, not physical
qualification. Offline CLI creates PREFLIGHT_PASS_NO_HARDWARE result. First plan
superseded by v2 after explicit success-health field addition; no HW occurred.

Next one bounded normal-only physical qualification under lease/reserves. This
will halt/download baseline PMU and restore normal runtime, not enter diagnostic
guard or isolation. It tests new register-channel gate on normal firmware only;
PASS cannot qualify recovery from guard/sleep/AIB state. DDR NOT_ADMITTED.
Current normal baseline remains as recovered previously, untouched this turn.
