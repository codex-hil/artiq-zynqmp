# A53 CPU1 ARTIQ kernel worker

Initial real network kernel execution, continuing Piotr's C BSP → Rust
staticlib design. CPU0 runs the maintained AMD/lwIP network stack plus Rust
management; CPU1 enters EL1/AArch32 through the previously validated AArch64
stub and loads ARM32 ET_DYN modules with the preserved M-Labs loader.
RPC value serialization is copied unmodified from M-Labs (see ORIGIN.md).
It is **not full ARTIQ support yet**: TTL output/input exports, RTIO DMA,
analyzer, moninj, exception unwinding and complex RPC returns are pending.

## Verified behavior

The real upstream `artiq_run` compiles a fresh kernel, sends it on TCP1381,
loads/relocates it on CPU1, executes it and serves actual RPC. The probe sends
an i64 token, a real hardware RTIO counter and a float to the host; the host
returns 3.75, which the kernel sends back in another RPC for validation.
Empty automatic asynchronous writeback is served using the upstream wire ABI.
`examples/genesys_network_probe.py` never calls TTL output functions.

Enabled exports: RPC send/receive, malloc/free, Core.reset/RTIO counter and
software timeline functions. No fake output function is supplied: loading
`examples/genesys_ttl.py` fails explicitly on unresolved `rtio_output`.
Scalar RPC returns n/b/i/I/u/U/f are accepted. Argument serialization is
upstream, but only scalar arguments and empty writeback are hardware-validated.

Negative tests: malformed/out-of-bounds ELF and upload larger than 1 MiB are
rejected; an unsupported TTL kernel cannot report LoadCompleted. Fragmented
upload, exclusive kernel ownership and management while CPU1 waits for RPC
are checked. Multiple uploads/runs reclaim library memory and reset the
separate kernel heap, rather than consuming a single test bump allocator.

## Build

Prerequisites: pinned host environment from docs/ARTIQ_HOST.md, Rust 1.87
ARMv7 target and ABI tools from prototypes/kernel-abi/README.md, shared
Vivado/AMD2025.2, local-rtio bitstream plus its SDT/PMU/FSBL.
From the repository root:

```sh
export RUSTUP_HOME=/srv/codex-hil-data/artiq-zynqmp/rustup
scripts/build_kernel_worker.sh "$ABI_TOOLS" "$WORKER" "$CSR_MAP"
scripts/build_a53_services.sh "$BOOT/sdt/system-top.dts" "$CSR_MAP" \
  "$CPU0" "$ARM_GNU_PREFIX" --kernel
```

Use a fresh CPU0 output directory. `WORKER/worker32.elf` is the AArch32
staticlib+C/startup linked image; `WORKER/start64.elf` is its EL3 bridge.
CPU0 image is `$CPU0/amd/app/build/lwip_echo_server.elf`. The historical file
name reflects the maintained AMD transport template, not the runtime scope.
Both builders emit SHA-256 manifests. Original checkouts remain preserved.

## Boot and test

PS reset → PMU/FSBL → FPGA local-rtio → PS/PL preflight → CPU1 worker → CPU0.
The CPU0 runner deliberately preserves CPU1; the old diagnostic runner halts
all cores and must not be used for this two-core runtime.

```sh
python scripts/test_ethernet_bringup.py \
  --server "$JTAG_SERVER" --cable "$JTAG_CABLE" --serial "$SERIAL" \
  --pmu "$BOOT/pmu-app/build/zynqmp_pmufw.elf" \
  --fsbl "$BOOT/app/build/zynqmp_fsbl.elf" \
  --elf "$CPU0/amd/app/build/lwip_echo_server.elf" \
  --bitstream "$GATEWARE/migen-build/top.bit" --psu-init "$BOOT/sdt/psu_init.tcl" \
  --worker32 "$WORKER/worker32.elf" --worker64 "$WORKER/start64.elf" \
  --output "$RESULTS/boot-network"
artiq-host python scripts/test_network_kernel_hw.py \
  --ip "$BOARD_IP" --output "$RESULTS/kernel"
artiq-host python scripts/test_a53_services_hw.py \
  --ip "$BOARD_IP" --artiq-source "$CURRENT_ARTIQ" --sipyco-source "$SIPYCO" \
  --kernel --output "$RESULTS/management.json"
```

The first Python command uses the original project venv (serial installed).
The other two use `artiq-host`. Update examples/device_db_genesys.py to the
actual DHCP IP, then the no-output probe also runs directly:

```sh
artiq_run --device-db examples/device_db_genesys.py \
  --dataset-db /large-disk/datasets.mdb examples/genesys_network_probe.py
```

This is a JTAG debug boot, not a standalone SD/QSPI boot image. No flash was
written. The board keeps the worker/network application running after tests.

## Memory/cache and failure policy

| Region | Owner/use |
|---|---|
| low DDR | CPU0 AMD application/BSP/heap |
| 0x20000000 | AArch64 CPU1 entry bridge |
| 0x200FF000–0x200FF03F | CPU0 command sequence/opcode/length; CPU0 flushes before SEV |
| 0x200FF040–0x200FF07F | CPU1 event sequence/status/length; CPU0 invalidates before reading |
| 0x200FF080 | CPU1 trap LR/SPSR diagnostic fields |
| 0x200FF100 + 4096 bytes | CPU1 serialized response/RPC body |
| 0x20200000–0x20400000 | CPU1 ARM image, 1 MiB heaps, stack |
| 0x21000000 + 1 MiB | CPU0 uploaded ELF or scalar RPC reply; flush before command |

Cacheline ownership separates producers. AMD cache-maintenance functions
are used on CPU0; CPU1 keeps MMU/cache off as in the physical ABI diagnostic,
so it reads/writes the shared DDR uncached. This is a deliberate initial
bring-up policy, not the final production MMU/security/cache architecture.
The maintained linked_list_allocator 0.10.5 manages separate 512 KiB heaps
for runtime/ELF and kernel malloc. Kernel heap resets on a new load; the old
library is dropped first. ELF target image is limited to 504 KiB, with heap
headroom; uploads are limited to 1 MiB and RPC events to 4096 bytes.

CPU0 management counter reads are rejected while a kernel is active or the
worker has failed: both cores otherwise contend for one hardware counter
latch. Metadata/log management remains available. A 30-second progress
watchdog bounds this initial runtime's load/run/RPC waits. Long-running
experiments require a proper watchdog/cancellation policy before support.

Worker hardware traps, panic, unsupported RPC return/host exception or
unwinding fail closed and require restarting the worker/runtime; they never
report KernelFinished. CPU0 remains independent. Kernel isolation, hardened
ELF parsing, cancellation, idle-owner eviction, application exceptions and
complex return allocation are not production-ready. Only trusted local
compiler artifacts were used. Tests do not claim physical TTL, RTIO DMA,
analyzer, moninj or DRTIO success.
