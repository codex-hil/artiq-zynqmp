# Composition metadata/publication/reentry fault qualification — offline

2026-10-28:49PITtestsPASS. Actual C forwarding/capture/lifecycle/builder/publisher
composition tested at-O2 and ASan/UBSan with fake callbacks.54receipt interruptions
(27callback positions x before/after effect) plus2success controls preserve
lifecycle COMPLETE/metadata success while publication reports UNKNOWN on error.
Commit may be visible after a reported final-write error; no retry or rollback.

Three metadata errors (zero image digest, missing sample digest, zero sample digest)
leave successful sample capture intact but produce metadata failure and ZERO
receipt writes/barriers, publication REJECTED, publication attempt unconsumed.
No path promotes these outcomes to a combined success. Seven invalid/reused plan
states cause zero callbacks and preserve the entire plan byte-for-byte; null
entry rejected. Nested composition attempted from every callback is rejected
before another callback, and repeated entry after finish is rejected as well.

The fixture reuses the existing fake callback source rather than rewriting the
implementation under test. Source pins include both fixtures and seven actual
C components. Synthetic hash words are not authenticated image/sample evidence.
Assertions qualify returning single-context callbacks only: no concurrency,
exception/hang recovery, actual sleep, physical visibility or persistent nonce
uniqueness proof. A plan can still be tampered with by hostile code; it is not a
security boundary. No target production source or audit image changed this turn.

No JTAG/UART/network/reset/register/HW access. MUST NOT DEPLOY; DDR NOT_ADMITTED.
Next safe offline work: machine-check new target-composition callback/branch
bindings with consistent ELF/disassembly mutations before constructing any new
source-bound audit gate; keep independent MMIO recovery/AP0visibility unresolved.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
