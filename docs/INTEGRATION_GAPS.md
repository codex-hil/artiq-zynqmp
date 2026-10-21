# Integration checkpoint — 2026-10-22

The physical port runs uploaded ARTIQ kernels, scalar RPC, local TTL input/output,
CoreDMA, analyzer and MonInj. KASLI04 also drives Genesys as a direct DRTIO leaf.
These are bounded laboratory results. Full upstream platform integration and the
complete original Definition of Done remain open.

| Area | Demonstrated | Remaining work |
|---|---|---|
| Boot and CPUs | AMD PMU/FSBL; CPU0 AArch64 networking and CPU1 AArch32 kernel worker; earlier SD cold boot | Cold boot the latest packaged runtime; empty-host provisioning and consolidated upstream platform build entry point |
| DDR | Initial scratch tests and actual kernel/DMA workloads | Full-range destructive test in a dedicated diagnostic image, then sustained memory stress |
| Local ARTIQ | Network upload/run, scalar RPC, physical TTL loopback, CoreDMA, standard analyzer/MonInj clients | Broader protocol/exception coverage and consolidation with maintained upstream runtime; current runtime is a custom integration |
| DRTIO | KASLI04 SFP1 to Genesys GTH, AUX, TSC load/snapshots, resets, physical DIO, forced-link recovery | Full production satellite lifecycle, routing coverage, multihop and subkernels are not qualified |
| Distributed DMA | Native upload/play/status/erase, replacement, fragmented lifecycle, caught malformed/expired requests and same-kernel recovery | Broader fault coverage and production lifecycle integration |
| Active DMA fault | One controlled 2 ms AXI hold caused native underflow; exact kernel exception and blocked post-fault state; both boards restored | This does not qualify arbitrary fault recovery or reuse of a faulted DMA engine; reuse remains forbidden before outer restoration |
| Clocking | Local GTH recovered-clock to Si5342 laboratory lock/loss/relock | Qualify production remote clock selection, synchronization, phase repeatability, jitter and deterministic latency with measurements |
| Future RF target | Architecture investigation only | FMC-HPC target, AD9172 hardware, JESD/DAC drivers and measured RF output |

The local execution path is AMD/lwIP on CPU0 (AArch64), then the M-Labs loader
and kernel worker on CPU1 (AArch32). It is not a complete native AArch64 upstream
ARTIQ runtime. No result above establishes RF performance or absolute timing
accuracy.

## Evidence and reproduction

- Local baseline: [RTIO debug services](RTIO_DEBUG.md) and [CoreDMA](CORE_DMA.md).
- Remote DIO/DMA and restoration: [KASLI04 procedure](../diagnostics/drtio/KASLI04.md).
- Normal profile entry point: `evidence/kasli04-profile-hardware-2026-10-21`.
- Long fragmented lifecycle: `evidence/kasli04-ddma-long-lifecycle-2026-10-21`.
- Rejected requests: `evidence/kasli04-ddma-expired-2026-10-21` and
  `evidence/kasli04-ddma-catch-2026-10-21`.
- Host cursor preservation: `evidence/kasli04-ddma-cursor-2026-10-21`.
- Controlled active fault: `evidence/kasli04-active-underflow-2026-10-21`.

The [source replay](SOURCE_REPLAY.md) now connects verified PS reconstruction,
SDT equivalence and FPGA generation/build to qualified artifact packaging and
release verification. Remaining work includes full-range DDR validation, latest
cold boot, runtime protocol integration and remote clock measurements.
Hardware revalidation must retain shared board leases through restoration.
KASLI01/03 belong to the separate secure-link project. Current qualified remote
identity is KASLI04 DNA `0x006c440674704854`; its removed EEM mux must never be
accessed. Flash, OTP and SD writes are outside these test profiles.

A [clean-checkout CPU1 build checkpoint](CLEAN_BUILD.md) now records successful
compilation and the remaining byte-reproducibility failure.

A fresh candidate assembled from rebuilt PMU/FSBL, the Dell PL rebuild and clean
CPU0/CPU1 builds passed one bounded JTAG physical session; baseline restoration
also passed. See [candidate qualification](CANDIDATE_JTAG.md). Its cold SD boot
remains untested; this result does not close the broader DDR/DRTIO/clock gaps.

The same candidate additionally passed three cycles each of full local CoreDMA
and exception recovery:216physicalpulses/432edges,21DMA and30exception-suite
artiq_run invocations. Post-error debug/network and old-baseline restoration
passed. See `evidence/candidate-extended-hardware-2026-10-21`; this closes the
candidate's extended local-regression checkpoint, not the excluded boot/DDR/
remote-link qualifications. The source build/release recipe is now documented; see SOURCE_REPLAY.md.

The [runtime protocol audit](RUNTIME_PROTOCOL.md) records the scalar-only RPC
return path, unsupported subkernels and the next host-testable framing step.
The corrected startup-log source has not been deployed.
