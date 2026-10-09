# Local RTIO analyzer and MonInj bring-up

The optional analyzer build reuses upstream ARTIQ `MessageEncoder`, attached
to the core CRI after the kernel/DMA switch. It captures real FPGA output,
input and exception records, including DMA replay, in a 256-record BRAM ring.
The ring overwrites its oldest records when full; the standard dump header
reports both delivered and total byte counts. This is 8 KiB of record storage,
not the full upstream DDR-backed analyzer DMA implementation.

CPU0 exposes the standard analyzer service on TCP1382 and MonInj on TCP1383,
using the existing foreground AMD/lwIP network stack. Standard ARTIQ clients
are used without protocol extensions. One client per debug service is
supported. Analyzer retrieval briefly disables capture, appends the upstream
stop record, copies the frozen ring, clears it and resumes capture. RTIO
execution is not stopped; events during this brief capture pause are excluded.

MonInj exposes level probe0 for output channel0 and the registered physical
input channel1. Output channel0 supports overrides0 (enable) and1 (level).
There is no bidirectional output-enable override for these simple TTL PHYs.
Unsupported probes/overrides/channels terminate the connection. Disconnect
releases output override enable. Probe changes are sampled every500ms;
MonInj is not a pulse-width measurement instrument.

## Build

Use the existing verified PS export with HP0 enabled for CoreDMA. Original
source checkouts and previous build outputs stay unchanged.

```sh
export RUSTUP_HOME=/path/to/port-rustup
export PYTHONPATH="$PWD/common/artiq:$PWD/common/migen:/path/to/misoc"
PYTHON=/path/to/venv/bin/python bash scripts/build_rtio_debug.sh \
  /path/to/genesys-rtio-dma /fresh/rtio-debug
bash scripts/build_debug_services.sh \
  /path/to/dma-ps/sdt/system-top.dts /fresh/rtio-debug/csr-map.json \
  /fresh/debug-services /path/to/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-elf
```

The PL script requires passing timing and checks all generated first-stage
CDC registers. It preserves the existing CSR banks; analyzer registers use
bank5. CPU1 can use the existing verified CoreDMA worker because its RTIO/DMA
register addresses and ABI are unchanged.

## Load over JTAG

Use the explicitly identified Genesys cable/UART and current hw_server URL:

```sh
python scripts/load_rtio_runtime.py \
  --server tcp:SERVER:3121 --cable YOUR_GENESYS_SERIAL \
  --port /dev/serial/by-id/YOUR_GENESYS_UART \
  --ps-export /path/to/dma-ps --bitstream /fresh/rtio-debug/top.bit \
  --worker /path/to/kernel-worker-dma-final \
  --cpu0 /fresh/debug-services/amd/app/build/lwip_echo_server.elf \
  --output /path/to/runtime-load-evidence
```

This performs PS reset → PMU/FSBL → PL → AXI preflight → CPU1 → CPU0.
It captures UART and the actual DHCP address. It does not write card/flash.
Configure your device database with that address and the pinned host compiler.

## Tests

```sh
PYTHONPATH="boards/genesys_zu-5ev/1_gateware:$PYTHONPATH" \
  python -m unittest discover -s tests -p test_analyzer_bram.py -v
/path/to/artiq-host/bin/python scripts/test_rtio_debug_hw.py \
  --ip ACTUAL_DHCP_ADDRESS --device-db /path/to/device_db.py \
  --artiq-run /path/to/artiq_run --output /path/to/debug-evidence
```

Hardware testing requires the verified JB1→JB2 jumper. It rejects an invalid
MonInj handshake, checks output override/readback and physical input tracking,
then checks override release on disconnect/reconnect. It executes normal
CoreDMA experiments and decodes real FPGA records with the standard analyzer
client. Eight additional experiments fill the ring beyond256 records and
exercise the complete multi-segment TCP dump. Capture reset/restart and the
final upstream stop marker are checked. Builds/simulation alone are not
hardware acceptance.

## Physical result (2026-10-09)

PASS using standard ARTIQ clients:37 decoded records from one DMA experiment
(16 TTL outputs,16 physical inputs,4 input-control outputs and one stop),
full256-record ring dump after eight more experiments, capture reset/restart,
MonInj physical input/output states, override readback and disconnect cleanup.
Native DMA error handling mask255 and analyzer underflow reporting also PASS.
Evidence: `evidence/rtio-debug-hardware-2026-10-09.json`.

The standard client closes asynchronously. Allow the peer to process FIN
before reconnecting to this single-client service. The test runner does so.
