# Archived C-output session replay — 2026-10-28

Replayed eleven archived actual-C fake-transport records: success, eight read
failures, wrong-address and exhausted-budget cases. The combined output SHA
matches the archive's original SHA. No C or target program was reexecuted.

Three synthetic event orderings per case yield33 correlations: no reported event,
wake before terminal, debug after terminal. Valid content keeps the original
CAPTURE_COMPLETE/READ_FAILED status. Wake/debug invalidation persists through a
later synthetic sleep sample. All results refuse RAM/sleep/HW/deployment claims.
No reported event is not proof of a physical event-free interval.

44 negative controls mix nonce/image/sample bindings or truncate the second
snapshot. All reject and invalidate; no retry repairs the same Session. Existing
72-test suite checkpoint remains dated; this evidence adds direct archived replay
controls without implementation changes. Inputs remain fake transport records,
not hardware samples; status/event injections are explicitly synthetic.

Next safe offline step: consolidate the observer/session stage with pinned
source/archive evidence and current physical admission blockers. The validated
software chain still lacks an authentic status transport, no-wake lifetime and
independent hung-load recovery. No old RAM probe or hardware retry follows.
