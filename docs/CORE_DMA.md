# CoreDMA on Genesys ZU

Physical local CoreDMA API PASS, 2026-10-08. Normal current ARTIQ/NAC3
`artiq_run` records DDR traces and FPGA HP0/RTIO DMA replays them. No CPU
pulse replay, custom host DMA protocol or changes to the upstream CoreDMA
Python class. Supports prepare_record/recorder, get_handle/playback_handle,
playback(name), erase, overwrite, empty trace and empty name.

## Run and reproduce

Current board: 192.168.2.16; DMA gateware/runtime loaded through JTAG.
Keep the verified JB1→JB2 jumper fitted for the input tests.

```sh
artiq_run --device-db examples/device_db_genesys.py \
  --dataset-db /srv/codex-hil-data/artiq-zynqmp/build/core-dma-user-datasets.mdb \
  examples/genesys_dma.py
make test-hw-core-dma BOARD_IP=192.168.2.16 \
  O=/srv/codex-hil-data/artiq-zynqmp/build/core-dma-user-tests
```

Use the existing shared host ARTIQ environment described in ARTIQ_HOST.md.
For new firmware, first build matching local-rtio-dma PS/PL as documented
in diagnostics/DMA_BRINGUP.md; then:

```sh
export RUSTUP_HOME=/srv/codex-hil-data/artiq-zynqmp/rustup
bash scripts/build_kernel_worker.sh ABI_TOOLS OUTPUT DMA_CSR_MAP
```

Final current worker:
`/srv/codex-hil-data/artiq-zynqmp/build/kernel-worker-dma-final/worker32.elf`
and sibling start64.elf. Existing CPU0 is the validated
`build-vivado/eh-kernel-services/amd/app/build/lwip_echo_server.elf`.
Boot flow remains PS reset→PMU/FSBL→DMA PL→matching psu_init AXI/reset
setup→CPU1→CPU0. Never use mismatched PS/PL/CSR firmware artifacts.

## Existing M-Labs work and ZynqMP adapters

Original kernel/dma.rs and runtime/rtio_dma.rs are preserved, unmodified,
with revision, hashes and license in boards/genesys_zu-5ev/3_kernel/upstream-dma.
Gateware remains the already validated M-Labs AXI reader and upstream ARTIQ
RecordSlicer/TimeOffset/CRIMaster. Record encoding is unchanged: scalar record
length17, channel3, timestamp8, address1, data4; fields little-endian, end
marker0,128-byte AXI alignment/padding. CPU1 writes bytes to uncached DDR
and issues DSB before starting the engine.

Zynq7000 page-table remapping and CPU0 mutex/messages are replaced here by
single-owner CPU1 output redirection and fixed persistent DDR slots. During
recording rtio_output writes the same records to DDR; normal output resumes
at record stop. No new general-purpose RTIO/DMA library was written.

Pinned NAC3 322b7bd returns tuples with an8-byte ObjectHeader. Its scalar
DMA tuple ABI is24 bytes: duration at8, address at16, bool at20. The firmware
adapter includes this non-refcounted prefix; compile-time layout assertions
protect the ABI. These three returned fields have no refcounted children.
Standard CoreDMA immediately unpacks them and constructs its own handle.
Handles in a kernel list were also tested. This is not a generic composite
RPC/tuple marshalling implementation.

## Storage and lifecycle

CPU1 reserves DDR **0x22000000–0x22200000**:32 slots of64KiB. Names may have
up to64 bytes. Each slot holds up to3847 scalar records, with128 bytes
reserved for the end marker/padding. Metadata sits outside both resettable
kernel/runtime heaps. Empty names/traces work. Exhaustion, overlong names,
missing/erased/invalid pointers and nested recording raise native DMAError.

Completed traces survive kernel ELF replacement and exception recovery.
Transient recording is discarded on normal kernel exit, new load or recovery.
Starting a replacement removes the old trace as in the upstream lifecycle;
an exception during replacement does not restore that old trace. Erase frees
its slot. Traces do not survive cold boot or CPU1 image reload/reset.

CoreDMA's epoch checks reject stale handles after record/erase; firmware also
checks pointer bounds/alignment and whether a slot is still committed. The
standard API's handle lifetime rule applies; this is not a capability system
for untrusted kernels.

The old direct DAP DMA test overwrites slot0. Use it only on a fresh runtime
with no committed traces. The standard test-hw-core-dma needs no DAP writes
and is the normal regression target.

## Physical evidence

Final3-cycle suite:21 artiq_run invocations, **216 validated pulses/432
physical loopback edges**. Includes named and handle playback, handle lists,
100us pulses and24-pulse sequences with64ns high/64ns low (8 RTIO ticks).
Every edge matches expected timestamps; input latency remains15 ticks=120ns.
This measures relative timing on the RTIO clock, not precision calibration.

Overwrite duration, restore/advance timeline, erase, full32-slot store,
64KiB trace overflow,65-byte name, empty name/trace, nested recording,
DDMA rejection and invalid pointer tests PASS. Actual DMA underflow is
caught, acknowledged and followed by another successful playback. Missing
trace also propagates a real host DMAError/device traceback; next kernel
records and plays successfully. A completed trace survives an uncaught
ValueError during another recording, with identical TCP connection retained.

Regression: ordinary TTL loopback10/10, native exception suite10 invocations,
management9 and Ethernet DHCP/20ICMP/1080TCP echo exchanges PASS.
Evidence/core-dma-{hardware,build,ttl,exceptions,management,ethernet}-2026-10-08.json.

Limits: local scalar TTL channels only; wide outputs and distributed DMA
remain unsupported. Hardware stalls beyond25s fail closed and require full
runtime reboot; this is not general watchdog/trap/cancellation recovery.
Production MMU/cache/full-DDR qualification remains pending.

## New SD image

Prepared complete image with DMA PS/PL and final worker:
`/srv/codex-hil-data/artiq-zynqmp/build/sd-core-dma-2026-10-08/BOOT.BIN`.
Hashes/partition headers are alongside it. Packaging PASS; this new image's
cold SD boot is **NOT_RUN**. The card currently contains the earlier validated
non-DMA image. Follow SD_BOOT.md to back up/replace BOOT.BIN through the USB
reader, then capture a cold boot and rerun test-hw-core-dma. Do not infer new
SD boot success from the JTAG/API tests above.
