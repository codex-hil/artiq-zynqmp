> Update 2026-10-07: optional `--kernel` build integrates real TCP1381
> load/run and scalar RPC on CPU1. See boards/genesys_zu-5ev/3_kernel/README.md.
> This document describes the earlier management-only build, which remains available.

# A53 Rust management integration (management-only)

This extends Piotr's C BSP → Rust staticlib architecture. Maintained AMD
GEM/lwIP owns Ethernet, interrupts, buffers and DMA. Rust implements a bounded
ARTIQ management protocol state machine. It is **not a complete core device**:
there is no kernel loader, RPC executor, RTIO DMA, analyzer or moninj service.
The kernel port 1381 is deliberately absent. No unsupported operation reports
success. Configuration writes, flash, reboot and streaming PullLog are rejected.

Supported: current upstream `CommMgmt` handshake, GetLog, ClearLog and read-only
metadata (`ip`, `mac`, `board`, `runtime_mode`, `rtio_counter`). Logs are real
bounded runtime logs; the counter is read by A53 from actual PL CSRs.
Client revision: `486e8f897547d282d46a02c30463449c21e30cfe`.
Four concurrent TCP sessions are supported; idle-session eviction, persistent
configuration and production robustness remain pending. Rust calls must stay
in the single-core foreground lwIP loop; this ABI is not interrupt-safe.

## Build from the existing checkout

First follow `diagnostics/ethernet/README.md` and gateware/boot firmware
instructions. Generate **local-rtio**, not blinker, and generate its SDT/FSBL.
Install Rust 1.87 with `aarch64-unknown-none`. The shared host installation is
selected by `RUSTUP_HOME=/srv/codex-hil-data/artiq-zynqmp/rustup`.
Then run on the host (output directory must be new):

```sh
scripts/build_a53_services.sh \
  "$BOOT/sdt/system-top.dts" "$GATEWARE/migen-build/csr-map.json" \
  "$OUTPUT" "$ARM_GNU_PREFIX"
```

`BOOT` is the boot firmware output generated from local-rtio's XSA;
`GATEWARE` is its Vivado build directory. The orchestrator runs Rust tests and
build on the host and the generated AMD BSP/CMake build inside shared Vivado.
ELF: `$OUTPUT/amd/app/build/lwip_echo_server.elf`; SHA-256 manifest:
`$OUTPUT/artifacts.sha256`. Vendor checkouts remain unchanged.

## Physical start and validation

Use the identified Genesys cable and UART, never a broad JTAG target filter.
The PS system reset can invalidate PL configuration. The supported sequence
is PS reset → PMU/FSBL → local-rtio bitstream → generated PS/PL setup and DAP
CSR preflight → A53 application. Programming PL before the PS reset caused
AXI transaction timeouts and an unhaltable A53 during a counter read.

```sh
python scripts/test_ethernet_bringup.py \
  --server "$JTAG_SERVER" --cable "$JTAG_CABLE" --serial "$SERIAL" \
  --pmu "$BOOT/pmu-app/build/zynqmp_pmufw.elf" \
  --fsbl "$BOOT/app/build/zynqmp_fsbl.elf" \
  --elf "$OUTPUT/amd/app/build/lwip_echo_server.elf" \
  --bitstream "$GATEWARE/migen-build/top.bit" \
  --psu-init "$BOOT/sdt/psu_init.tcl" --output "$RESULTS/network"
python scripts/test_a53_services_hw.py --ip "$BOARD_IP" \
  --artiq-source "$CURRENT_ARTIQ" --sipyco-source "$SIPYCO" \
  --output "$RESULTS/services.json"
```

Use the project's data-disk Python venv, containing serial and the upstream
client dependencies, including lmdb 3.0.0 and platformdirs 4.12.3. The test
runs actual upstream CommMgmt and `artiq_coremgmt`, not a mock. The network
runner also checks DHCP, ICMP, byte-exact TCP echo and GEM error counters.
The services test checks fragmented/coalesced requests, concurrent sessions,
malformed input, unsupported writes, real logs and A53 RTIO counter access.
Its nominal 125 MHz check allows 5% network timing error; it is not precise
clock calibration. It does not test physical TTL or kernel execution.

Manual CLI with upstream ARTIQ/sipyco on PYTHONPATH:

```sh
python -m artiq.frontend.artiq_coremgmt -D "$BOARD_IP" log
python -m artiq.frontend.artiq_coremgmt -D "$BOARD_IP" config read -s rtio_counter
```

Next milestone: a genuine AArch64 kernel loader/executor using the previously
validated compiler/ABI, connected to local RTIO and RPC. Do not interpret a
successful management handshake as a working experiment executor.
