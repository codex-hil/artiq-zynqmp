# Secondary-core and transaction-history review — 2026-10-24

Offline review only, no HW access. Exact recent capture has APU reset0x300e
and RPU NCPUHALT0 observations. Execution order is: PS reset, PMU+trained FSBL,
checked OCM stop, no-master PL load, peripheral/master snapshots, PMU guard
request/capture, then mandatory normal restoration. Thus core/peripheral samples
precede the PMU guard; they are not post-guard exclusion observations.

No-master PL constants prevent new AR/AW/W requests from exported PS slave
ports after that configuration. They do not acknowledge completion of requests
accepted earlier, retain pre-reset counters, stop all PS masters or bind a global
transaction epoch. Debugger stop commands use catch in startup; reset samples
and checked CPU0 terminal narrow state, but catch-success absence is not positive
halt proof for every core. RPU is not explicitly reset/parked by these launchers.

A post-guard read could narrow ordering but still would not establish future core
release exclusion or a transaction drain. Therefore no unchanged read-only capture
is selected. Next useful offline work: inspect exact PS system-reset domains and
FSBL/PMU release sequence, identifying an architectural completion/hold mechanism
before proposing any new reset write or destructive DDR operation. PMU ROM event
policy remains separate; do not change remap or mask exceptions to bypass it.

Code regression found/fixed during review: observe-only request dispatch had
accidentally acquired guard profile arguments in d42a550. With guard=None it would
fail before transport; latest successful HW used the separate guard branch and
is unaffected. Actual request branch AST execution now PASS with guard=None and
legacy argument counts; injecting prior regression produces expected NoneType
failure. First fixture found two request branches; narrowed to actual parse branch.
No old manifests rewritten. Changed run_trained_observer hash intentionally
invalidates current deployment manifests; fresh pins required before future HW.
DDR NOT_ADMITTED. Normal baseline unchanged, not rechecked here.
