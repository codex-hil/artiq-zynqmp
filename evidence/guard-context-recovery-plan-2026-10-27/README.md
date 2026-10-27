# One changed guard-context recovery qualification — 2026-10-27

Offline preflight PASS, HW NOT_RUN. Fresh manifest explicitly aib_observation=false;
exact vector-v1 PMU and no-master PL preserved. Changed recovery helper probes
r0 before download; parent now verifies seven exact ordered stages using same
validator as normal-only qualification. No new firmware, AIB write/read stage,
remap write, private alias, force or automatic retry. Ordinary boot/master context
observations remain necessary preconditions, not DDR ownership proof.

Four actualTcl tests + three wrapper/marker tests + three image gate tests + six
parent lifecycle tests PASS (16cases). Full nested parent preflight PASS. Historical
manifests preserved. Changed sources invalidate normal-only plan's former pins;
its historical physical PASS remains valid for the recorded helper versions.

One bounded physical attempt may distinguish core-register-channel failure from
later download failure after guard. Success validates only that attempt, not
causation or all future recovery. If r0 fails, do not download or resume blindly;
retain raw error and require manual recovery if necessary. If download fails,
no reset/alias/retry fallback. Whole run needs shared Genesys lease, real storage
reserves, normal reset/boot/debug/Ethernet restoration. Current normal runtime
left untouched in this turn. DDR NOT_ADMITTED regardless of outcome.
