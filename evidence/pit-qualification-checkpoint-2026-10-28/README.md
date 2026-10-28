# PIT/PMU qualification checkpoint — 2026-10-28

Consolidated matrix only; no new hardware action or test run. matrix.json pins
all referenced evidence documents/reports and distinguishes OFFLINE_PASS,
STATIC_PASS, HISTORICAL_HW_PASS/FAIL, UNKNOWN, UNQUALIFIED and NOT_RUN.
No per-row PASS promotes the whole image or destructive DDR test to admitted.

Current full audit image SHA256:
fe560003b29596d1d708b1008ebdcf5edb7a93338e08b4af2c0b48411f946fec.
Frozen inventory SHA256:
c6e12adb82352d744a2aee886b915b8e52d81534db9dc147cb19f8815b1a3a90.

Counter profile deployment false; destructive DDR admission false. Physical
backend/main hook/mailbox, target hash provenance, sleep/AP0 visibility and
independent hung-read recovery remain unresolved. Historical normal runtime
restore PASS belongs to Oct27, not a live health check today. No unchanged HW
retry is selected. See docs/PIT_QUALIFICATION_CHECKPOINT.md for the handoff.
