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
