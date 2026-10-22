# RTIO DMA drain evidence and reset ownership

This is offline simulation of the tracked `zynqmp_dma.py`, not hardware
quiescence admission. Evidence: `evidence/dma-drain-model-2026-10-23`.

The normal completion cases use the actual Migen DMA, upstream record pipeline
and CRI master. Independent monitors count accepted AXI AR requests and accepted
R bursts ending with RLAST. A memory responder preserves same-ID order and legal
ready/valid behavior; CRI and read responses apply backpressure. The test requires
observed busy, final status zero, no outstanding bursts, no remaining AR/R valid,
and no new request for 30 cycles without another trigger.

24 cases cover response delays 0/3/17, CRI stalls 0/31, OKAY/SLVERR, and trigger
values 0/1. All completed with zero outstanding reads. Peak outstanding: 13;
2628 stalled R cycles and 12300 stalled AR cycles were exercised. Error responses
still permit draining; the bus-error status is separately checked. This is not
exhaustive timing, maximum-counter-depth, malformed AXI or abort qualification.

A negative test wraps the same DMA in Migen ResetInserter. After accepted AR
requests, it resets only PL logic while the modeled PS retains delayed responses.
The DMA reports IDLE with two accepted, unreturned bursts. This is a confirmed
counterexample to **IDLE alone after independent PL reset**. It does not prove
that the actual board reset sequence does this; that sequence must be audited.
Resetting the observer/core must not be treated as resetting all AXI owners.

Required before destructive DDR tests:

- Bind the active bitstream and CSR map to the audited DMA source.
- Exclude every writer of the trigger CSR; writing zero also starts playback.
- Establish completion and error status before disturbing reset/clock ownership.
- Review the actual PS/PL/HP0 reset order and what happens to accepted requests.
- Establish secondary-core, PMU and other PS-master ownership independently.

No new gateware CSR or production logic change was made. A dedicated inflight
CSR would improve visibility but would not by itself solve reset ownership.

Reproduce on the prepared host from the repository root:

```sh
export PYTHONPATH="$PWD/common/artiq:$PWD/common/migen:/srv/codex-hil-data/artiq-zynqmp/reference/misoc-current:/srv/codex-hil-data/artiq-zynqmp/reference/litex"
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -m unittest discover -s tests -p test_dma_drain.py -v
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python -m unittest discover -s tests -p test_dma_reset_ownership.py -v
```

The evidence records actual import paths, clean source revisions and RTL/test
hashes. Explicit `common/migen` selection matters: the shared venv otherwise
imports a different reference checkout. Hardware and destructive DDR remain
NOT_RUN for these tests. Next audit the real reset sequence and prepare a
read-only PS/secondary-core capture allowlist.
