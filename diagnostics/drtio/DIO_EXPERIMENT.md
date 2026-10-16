# Kasli master → Genesys DRTIO digital I/O experiment

The target is a **single direct-link leaf**, rank1/destination1 on the first
Kasli downstream port. It is not a repeater or a general Sinara satellite.
The physical endpoint uses the existing reviewed JB1 (AE13) output and JB2
(AG14) input. Connect JB1 to JB2 with the existing jumper; do not use power pins.
The simple TTL PHY has8ns resolution; the protocol timestamps use1ns units.
Absolute inter-board phase, jitter and deterministic link latency are not proved
by this test.

`examples/kasli_drtio_dio.py` is a normal ARTIQ/NAC3 kernel executed on Kasli.
It resets RTIO, leaves10ms scheduling margin, schedules eight10us pulses with
100us spacing, gates the remote input, and reads eight timestamps over DRTIO.
It requires exactly eight rising edges, all seven spacings100000mu, and an
empty ninth read. The input PHY is permanently an input; no output-enable
command is needed. Global channels are0x10000 (output) and0x10001 (input).

The firmware build option `--external --tsc --reset --dio` uses the unchanged
upstream AUX packet codec with additional RoutingSetPath/Rank/Ack and
DestinationOk support. It stores the local-hop predicate for each route, accepts
rank1, and advertises only destination1 when its direct path, TSC load, queue/
PHY release and fault-free backend are all present. Other destinations remain
DOWN. No downstream forwarding is implemented. Fatal faults never produce UP.

Use the combined `scripts/test_kasli03_netboot_hw.py` session with the reviewed
Genesys configuration's `reset_test: true` and `dio_test: true`. It verifies
firmware/CSR/bitstream/source/policy hashes, holds the Genesys and all three
Kasli board locks, boots the pinned Kasli master into SRAM, enables the Genesys
endpoint, verifies TSC and two native reset transactions, requires the native
master's `[DEST#1] destination is up`, and runs the DIO kernel twice. It restores
Kasli diagnostic/clock and Genesys local core and validates both before release.
Never run a second direct UART/JTAG/network client outside that session's lease.

The first physical attempt reached native destination-UP and completed resets,
but NAC3 rejected legacy timing syntax before the kernel ran. The corrected
experiment uses core.delay, float pulse durations, and an explicitly declared
parallel-block timestamp; static `artiq_compile` with localhost-only device data
passes. Raw failed-session evidence is retained separately from subsequent runs.


With both qualified volatile images already active and the shared leases held,
the standard command is:

```sh
artiq_run --device-db examples/device_db_kasli_genesys.py examples/kasli_drtio_dio.py
```

Do not run this command against the restored diagnostic baseline. The combined
session loads the matching images and owns the lease for its standard clients.
Its evidence directory contains the exact session configuration, generated
runtime device database, raw master logs and experiment results.


Physical acceptance2026-10-15: **PASS** in two independent kernel executions.
Both returned `DRTIO_DIO_PASS 8 100000`; native destination1 UP, no new master
reset/RTIO/buffer/TSC errors, and both board restorations passed. Genesys local
TTL/DMA/analyzer/MonInj and Ethernet regression checks passed afterward. See
`evidence/kasli03-external-dio-final-2026-10-15/acceptance.json` and raw logs.

## Bounded stability test

`examples/kasli_drtio_stability.py` measures both edges of1024 pulses per
kernel, in128 batches of eight pulses. The input FIFO is drained after each
16-edge batch and a seventeenth read must be empty. Four width/period pairs
(in1ns machine units) repeat evenly:

| Width | Period |
|---:|---:|
|800|16000|
|8000|40000|
|10000|100000|
|30000|250000|

Every high time and rising-to-rising interval must match exactly. Native
core.reset is invoked at batches0,32,64,96. Two kernel executions measure4096
physical edges,256 empty reads and eight native resets. This tests integrity
and varied scheduling; it is not maximum sustained throughput or FIFO capacity.

The guarded session enables this with `stability_test: true` in its reviewed
external DIO configuration. It requires standard DIO acceptance first, captures
both standard artiq_run results, rejects new master/firmware errors, and restores
the same baseline. Static artiq_compile can use a localhost-only device database;
it performs no physical board access.

## Forced GTH link recovery

Configuration `recovery_test: true` requires qualified DIO/reset configuration.
After baseline DIO acceptance, the parent retains every shared lease while an
exact-cable XSDB script asserts only Genesys monitor_reset for1000ms. It neither
reprograms PL nor resets the PS or Kasli. Two cycles each require one **new**
master LINK#0 DOWN, initialization-completed and destination1 UP occurrence,
one fresh actual-load TSCAck in that reset epoch, and two physical DIO kernels.
New TSC/reset/RTIO/buffer errors reject acceptance. Raw UART/master logs are
preserved per cycle, including baseline experiment logs. Normal restoration
runs even if reset or retraining fails. This tests forced transceiver reset,
not physical cable removal or deterministic recovered phase.

## Next: distributed DMA

Current upstream implements DmaAddTraceRequest/Reply, DmaRemoveTraceRequest/
Reply, DmaPlaybackRequest/Reply and asynchronous DmaPlaybackStatus. Reuse those
packet definitions and satman trace lifecycle. The default CoreDMA context
records with enable_ddma=False; distributed recording must explicitly enable it.

The current laboratory satellite routes only the RT packet engine to SyncRTIO.
It has no DMA memory reader or CRI arbitration. Upstream Kasli satellite target
connects drtiosat.cri, rtio_dma.cri and local rtio.cri through
CRIInterconnectShared; satman/dma.rs drives the native engine and reports status.
Genesys normal local-core DMA is a different already-qualified image. Its PASS
does not imply remote DMA support in this satellite image. The next integration
must provide a memory-backed upstream DMA engine, safe CRI ownership/reset and
trace lifecycle/status handling, with RTL tests before hardware acceptance.
