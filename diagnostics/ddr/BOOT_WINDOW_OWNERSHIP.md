# DDR diagnostic boot-window ownership

The intended DDR test window is **after the SPD-trained FSBL JTAG terminal and
before CPU0 network runtime or CPU1 kernel worker starts**. The observer and its
exception vectors execute in OCM. This window is not yet admitted for DDR writes.

Offline source/image audit: `evidence/fsbl-network-window-2026-10-23`.
Reproduce with `scripts/audit_fsbl_network_window.py --build BUILD --output FRESH`.
The audited FSBL/PMU hashes match the diagnostic images in the trained-observer
manifest. Neither ELF has named XEmacPs/lwIP/netif entry points. That is negative
symbol evidence, not proof of absence of generic MMIO or ROM-mediated actions.
The adjacent source tree has not been independently rebuilt to prove equivalence.

In `xfsbl_initialization.c`, JTAG returns `XFSBL_STATUS_JTAG` before device-driver
initialization. `xfsbl_main.c` takes this status to stage4/handoff and marks both
RPU cores usable in its usage-status register. That usage marker is not a reset
or halted-core certificate. The generated `psu_init.c` enables GEM clocks and
releases GEM0 reset. PMU contains a GEM reset definition using a ROM callback;
its continued reset/clock authority must not be mistaken for an absent master.
No new stop/reset policy is authorized by this document alone.

## Required integration before any DDR writer

1. Keep the existing shared Genesys lease from system reset through normal-runtime
   restoration and physical validation. Preserve storage gates and artifact pins.
2. Establish actual JTAG/diagnostic boot mode and checked FSBL terminal/CPU0 state;
   UART text alone is insufficient. Do not start normal runtime or CPU1 worker.
3. Collect existing fixed GEM/SD/QSPI, CSU, ZDMA and RPU register observations
   **within this same window**, after training. Associate every capture with the
   same manifest and boot session; prior runtime snapshots do not qualify.
4. Require GEM RX/TX disabled at this point. If enabled, reject and restore;
   do not silently call XEmacPs_Stop, clear flags or guess a drain delay. Disabled
   bits are necessary observations, not standalone proof of outstanding drain.
5. Resolve secondary A53/R5, PMU, PL HP0, PCAP and remaining PS master ownership.
   Prove reset ordering/drain separately. The actual DMA reset counterexample
   shows why IDLE after resetting PL alone is insufficient.
6. Only after explicit admission run a bounded OCM DDR writer with exception
   capture. Preserve the two separate DDR address windows and exclude OCM/MMIO.
7. On any failure restore the qualified normal runtime using the existing parent
   lifecycle; validate TTL/CoreDMA/analyzer/MonInj/Ethernet before lease release.

No physical boot-window peripheral capture or full DDR writer ran in this audit.
The next implementation step is to add read-only observation frames to the
existing trained-observer child, with parent-pinned scripts and offline negative
controls, while keeping the DDR write gate closed.


## Integrated peripheral capture (offline checked)

Use `evidence/boot-peripheral-integration-2026-10-23/inputs.json` as the trained
observer manifest with the existing runtime restoration manifest. It requests
normal exception-observer execution followed by a fixed read-only peripheral
frame. The parent pins nested input manifest, vendor headers and all execution
helpers before and under its lease. Failure rejects the candidate and restores
normal runtime; a quiet result remains observation-only, never DDR admission.
Physical execution remains NOT_RUN at this checkpoint.


## Physical peripheral window PASS — 2026-10-23

Same-boot capture after trained exception-observer execution passed: GEM RX/TX
both disabled, SD transfer/inhibit fields0, QSPI DMA STS0, stable two samples.
Full cycle93.081s included normal-runtime restoration and physical debug/DMA/
Ethernet requalification at192.168.2.3. Lease released. Raw evidence is in
`evidence/boot-peripheral-hardware-2026-10-23`. This establishes necessary
peripheral observations in this boot only; remaining owner/drain conditions
above are unresolved, and no DDR writer ran. Next extend same-window coverage.


## Combined master observation (offline checked)

`evidence/boot-master-integration-2026-10-23/inputs.json` extends the observer
with source-pinned ZDMA, CSU/core metadata and RPU captures in the same boot.
Reads are sequential, not atomic. Nonquiet DMA fields reject; RPU/core metadata
remain unknown ownership. Parent lifecycle still restores and qualifies normal
runtime. Physical execution NOT_RUN at this checkpoint; DDR writer remains closed.


### 2026-10-23 — Combined same-boot master hardware observations PASS

104.687s full reset/trained-FSBL/EL3-OCM/peripheral/master/restoration cycle PASS
under shared Genesys lease. Sequential same-boot observations: all16 ZDMA
channels STS/CTRL2=0 twice; both CSU STS=0 twice; GEM RX/TXdisabled,
SD transfer/inhibit fields0, QSPI DMA STS0. RPU global0x50, configs0x4/0x4,
statuses0x3f/0x38, clock0x03000302, reset0xfc0, stable. Metadata CPU0suspended1,
CPU1Reset/suspended0, CPU2/3PowerOnReset/suspended0, R50Halted/suspended0,
R51LockStepMode/suspended0. Metadata labels do not establish held-reset/cache
ownership. Positive core/reset and PMU/PL/PCAP/drain requirements still unresolved;
DDR writer NOT_RUN and NOT_ADMITTED. Normal runtime restored192.168.2.3;
physical TTL/CoreDMA/analyzer ring-wrap/MonInj and Ethernet PASS. Lease released.
No Si/SD/flash/OTP/Kasli writes. Raw logs/hashes and physical restoration evidence:
`evidence/boot-master-hardware-2026-10-23`. Next offline audit PMU/core reset
control and PL HP0 reset/ownership, then prepare necessary register observations;
do not repeat unchanged combined capture without new coverage.


### 2026-10-23 — APU reset plan and PMU core-control source audit (offline)

Reviewed PMU pm_proc.c: RPU0 sleep enables AIB isolation, asserts reset,
clears NCPUHALT, deasserts reset, disables isolation. Wake calls ROM R50 reset
handler then sets NCPUHALT. APU wake delegates to ROM. This source sequence is
consistent with observed RPU reset0/NCPUHALT0, but does not prove execution or
exclude future PMU wake. Do not require held-reset as the only possible RPU
idle model, or silently invoke sleep/wake callbacks during observation.
Added source-checked CRF APU reset-control plan at0xfd1a0104: four soft-reset,
four POR bits and L2 reset decoded separately, unknown bits retained. Two decoder
tests and two changed-header controls PASS; actual vendor header validation PASS.
Evidence `evidence/apu-reset-plan-2026-10-23` pins header and PMU source/anchors.
No hardware access. Next integrate two fixed APU reset-control reads into the
same-boot observation, then review PMU request/event paths and PL HP0 drain.
DDR writes remain NOT_ADMITTED; no policy to stop PMU or mutate core resets added.


### 2026-10-23 — APU reset-control same-boot integration (offline)

Added fixed read-only Tcl for two32-bit CRF RST_FPD_APU reads0xfd1a0104,
plus strict ordered-frame parser and vendor-header/plan/helper preflight. Extended
the existing same-boot collector with APU controls after ZDMA/CSU/RPU. Exact
cable/PSU selection, parent shared lease and mandatory restoration remain intact.
Soft/POR/L2 reset controls and unknown bits are observations, not automatic DDR
admission or PMU-release exclusion proof. Fresh complete nested pins in
`evidence/boot-apu-integration-2026-10-23`. Nine offline tests PASS including
real Tcl read-address/count controls, malformed frames, stale pins and restoration.
Hardware NOT_RUN. Next bounded combined hardware capture/restore/qualification,
then PMU request/event authority and PL HP0 reset/drain audit. No DDR writer.


### 2026-10-23 — Same-boot APU reset controls physical PASS

110.194s diagnostic/restore/validation cycle under shared Genesys lease PASS.
CRF RST_FPD_APU0xfd1a0104 read twice0x300e: CPU1/2/3 soft-reset controls1,
CPU2/3 POR controls1, CPU0soft/POR0, CPU1POR0, L2reset0, unknown bits0.
These are stable sampled controls, not proof that PMU cannot later release reset.
Existing same-boot ZDMA/CSU/peripheral necessary fields also PASS; DDR test
NOT_RUN/NOT_ADMITTED. Normal runtime restored192.168.2.3, physical TTL/CoreDMA/
analyzer ring-wrap/MonInj/Ethernet PASS; lease released. No Si/SD/flash/OTP/Kasli
writes. Raw logs/hashes and qualification: `evidence/boot-apu-hardware-2026-10-23`.
Next offline PMU event/request and PL HP0 reset/drain audit; do not repeat this
unchanged hardware cycle. Remaining PMU/PL/PCAP ownership unresolved.


### 2026-10-23 — PMU wake authority routes audited (offline)

Pinned current PMU ELF9f5c58c5 contains PmIpiHandler/PmProcFsm/PmProcWake/
PmMasterWake. Adjacent source routes: PM IPI handler -> PM_REQUEST_WAKEUP ->
permission checks -> PmMasterWakeProc -> PM_PROC_EVENT_WAKE -> processor wake
callback; hardware GPI wake handler is registered for A53/R5 wake events; slave
wake can call PmMasterWake. APU callback delegates to ROM; RPU callback sets
NCPUHALT after ROM reset handler. SLEEP_WHEN_IDLE does not disable PM service.
This is capability evidence, not proof an event occurred or is currently enabled.
Source hashes/line anchors and linked symbol checks reproduced by
`scripts/audit_pmu_wake_routes.py`; evidence `evidence/pmu-wake-audit-2026-10-23`.
Positive anchor/hash and missing-anchor rejection controls PASS. No hardware access.
Cannot close future-wake exclusion from two sampled reset values. Do not stop
PMU or change event masks without a separately reviewed, restorable policy.
Next offline identify non-destructive wake mask/status register observations and
inspect PL HP0 reset/drain coverage. DDR write admission remains closed.


The PMU exclusion condition remains unresolved. A diagnostic-window policy must
account for IPI requests, direct processor wake events and slave wake sources;
review effective permissions/masks/pending state plus non-wake callbacks accessing
DDR. Static source capability alone must not cause hardware writes or blanket
PMU shutdown. Candidate approaches require further review: a maintained AMD PMU
configuration for a bounded diagnostic image, or a documented reversible event
policy with readback and restoration. Neither was implemented or run here.


### 2026-10-23 — PMU event observation allowlist (offline)

Source-checked six-register plan: IOMODULE GPI1/GPI2/IRQ_PENDING/IRQ_ENABLE
0xffd40024/28/34/38; LOCAL GPI1_ENABLE/GPI2_ENABLE0xffd60224/228. Two samples,
32-bit reads only. Processor wake signal/enable bits decoded separately; masked
signal is only a current observation. Excludes IRQ_ACK, IPI acknowledgements,
enable/disable writes and event clearing. Actual DAP accessibility NOT_RUN;
no force-access fallback permitted. Vendor headers, source read/ack line anchors
and decoder controls: `evidence/pmu-event-plan-2026-10-23`. Two tests and changed
address rejection PASS. No hardware access. Next integrate fixed leased capture
with existing same-boot lifecycle and test strict frame/timeout behavior offline;
PMU future-wake and DDR ownership remain unresolved. No DDR write admission.
