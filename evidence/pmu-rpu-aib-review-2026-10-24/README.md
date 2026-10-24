# RPU sleep/wake and AIB acknowledgment review — 2026-10-24

No HW access. UG1085v2.5p420 describes AIB isolation stopping new traffic while
allowing posted transactions to finish, followed by acknowledgment of quiescence.
Instance1/2 isolate RPU0/1 masters toward LPD; instance3 covers LPD-to-DDR path.
This is a concrete drain mechanism, unlike an ordinary idle/reset snapshot.
It is not evidence every DDR master is covered by one isolation instance.
Primary source:
https://docs.amd.com/api/khub/documents/xzMsp_c5sG9J6A3u7NkJYQ/content?Ft-Calling-App=ft

Exact candidate pm_proc.c PmProcRpu0/1Sleep enables AIB in both directions,
asserts core reset, clears NCPUHALT, deasserts reset and disables AIB again, then
returns XST_SUCCESS. Wake invokes ROM reset handler and sets NCPUHALT on success.
Therefore NCPUHALT0/reset-released capture is consistent with the sleep sequence,
but neither proves it ran nor excludes a later wakeup.

Crucial implementation limit: XPfw_AibEnable returns void. It polls15times with
10us sleeps, prints detailed warning on no ACK, then returns normally. RPU sleep
does not receive/check an isolation status. Its success must not be accepted as
an independent transaction-drain receipt. The normal implementation is not changed.

Host test compiles the actual unchanged vendor function body with fake register,
sleep and log backends. No ACK:15reads/15sleeps/1request and normal return.
Immediate ACK:1read/0sleeps/1request and normal return. PASS verifies software
behavior only; not physical timing, register semantics or completed transactions.
Harness extraction preserves function logic; types/constants/backends are mocks.

Next offline prepare a separate diagnostic acknowledgment protocol that reports
exact requested mask, bounded ACK samples and timeout as a hard failure, keeps
isolation until restoration, and never grants DDR admission by itself. First map
master/slave paths and verify snapshot reads cannot be cut off (OCM/debug/PMU).
No AIB write/timeout-ignore/status-clear/reset change is authorized by this review.
Retain all owner/future-release/ROM gaps; DDR NOT_ADMITTED.
