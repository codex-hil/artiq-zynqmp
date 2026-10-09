# ARTIQ on Genesys ZU-5EV — continuing Piotr Jedyk’s port

This project continues [Piotr Jedyk’s `artiq-new`](https://github.com/pjedyk/artiq-new), rather than starting a new ZynqMP port from scratch. The `bringup/genesys` branch is based on `wip@b25e75b`; original history and source snapshots are preserved.

**The physical Genesys ZU-5EV runs kernels uploaded over Ethernet, basic RPC, local RTIO, TTL input/output and CoreDMA.** This is an experimental port, not an official M-Labs release or a production-qualified platform.

The execution path is:

`artiq_run` → AMD/lwIP on CPU0 (AArch64) → M-Labs loader on CPU1 (AArch32) → kernel execution, RPC and FPGA RTIO.

Hardware results include:

- Management, UART, timer interrupts, initial DDR tests, Ethernet and PS–PL AXI access.
- Physical JB1 → JB2 TTL loopback: 10/10 runs, 100 µs pulses and a fixed observed 120 ns input latency.
- Native kernel/RPC/RTIO exceptions, catch/reraise/finally and recovery without resetting the device: 30 experiments.
- Cold SD boot of the earlier runtime: one validated power cycle.
- CoreDMA recording and replay by name/handle, persistence between kernels and exception recovery: 216 pulses / 432 edges, including 64 ns pulses.
- Internal GTH PRBS7 loopback and Si5342 lock to recovered RXCLK: six loss/relock cycles with no new settled PRBS7 errors.
- Upstream ARTIQ RT/AUX framing through physical GTH loopback: three reset/alignment cycles, detected raw-bit corruption and clean recovery.
- Autonomous diagnostic Si5342 firmware: PS bootstrap, RX clock selection and three physical loss/recovery cycles. Satellite runtime integration remains pending.

Local analyzer/moninj have also passed physical tests using standard ARTIQ clients; see [RTIO debug instructions](docs/RTIO_DEBUG.md). The analyzer currently uses a finite 256-record BRAM ring. Full DDR stress testing, external DRTIO synchronization and production qualification remain outstanding. The newer CoreDMA/analyzer/MonInj SD image has been packaged but has not been validated by a cold boot; the validated SD image contains the earlier non-DMA runtime.

See [PORTING_STATUS.md](PORTING_STATUS.md) for detailed evidence and limitations, [architecture](docs/ARCHITECTURE.md), [source revisions](docs/SOURCES.md) and [build compatibility notes](docs/BUILD_COMPATIBILITY.md). Some supporting documents are still in Polish.

## Clone and licensing

Public repository: [codex-hil/artiq-zynqmp](https://github.com/codex-hil/artiq-zynqmp).

New original files are licensed under LGPL-3.0-or-later, subject to third-party notices. **The original Piotr snapshot has no repository-wide license grant; clarification with its author is outstanding.** See [THIRD_PARTY.md](THIRD_PARTY.md) for exact licensing boundaries.

```sh
git clone --branch bringup/genesys \
  https://github.com/codex-hil/artiq-zynqmp.git artiq-genesys
cd artiq-genesys
git submodule update --init common/artiq common/migen
```

An existing Git bundle is an alternative for offline transfer:

```sh
git clone --branch bringup/genesys genesys-bringup.bundle artiq-genesys
cd artiq-genesys
git submodule update --init common/artiq common/migen
```

Keep a separate original checkout for comparison:

```sh
git clone https://github.com/pjedyk/artiq-new.git piotr-original
git -C piotr-original checkout wip
```

Do not overwrite original checkouts. On the development host, mirrors live in `/srv/codex-hil-data/artiq-zynqmp/sources`, working trees in `work`, and artifacts in `build`. Paths, board serials and network addresses in laboratory examples must be adjusted for your host.

Recreate the source archive independently:

```sh
python3 scripts/acquire_sources.py --destination /large-disk/artiq-sources \
  --manifest evidence/sources.json --include-yocto
```

Existing mirrors are not updated automatically. The manifest records exact revisions and refs and verifies pinned gitlinks. Current M-Labs upstream sources are archived separately from historical GitHub refs.

## Build and test without hardware or Vivado/Vitis

Requirements: Python 3.12, Git, GNU Make and rustup. Allow roughly 1 GB for the basic tools and additional space for complete source histories and Yocto dependencies.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-host.txt
rustup toolchain install 1.87.0 --profile minimal --component rustfmt \
  --target armv7r-none-eabihf --target aarch64-unknown-none
make test hdl
```

If Python lacks `ensurepip`, install the corresponding venv package or use an isolated pip bootstrap. Avoid installing project dependencies into the system Python environment.

`make test` runs host/simulation checks, builds Piotr’s original R5 library and the A53 diagnostic, and validates ELF entry points and load segments. `make hdl` generates the local RTIO/AXI subsystem and CSR map without PS IP; it does not produce a board bitstream or XSA.

```sh
make test hdl O=/large-disk/artiq-build
make test-sim
make firmware
make diagnostics
```

| Artifact | Purpose |
|---|---|
| `build-host/original-r5/cargo-build/armv7r-none-eabihf/release/librust_firmware.a` | Piotr’s original Rust static library; not the ARTIQ runtime |
| `build-host/a53/aarch64-unknown-none/release/genesys-a53-bringup` | A53 startup/MMU/UART/DDR/timer/IRQ diagnostic ELF |
| `build-host/local-rtio-hdl/local_rtio.v` | Upstream RTIO with AXI/CSR, without the PS board wrapper |
| `build-host/local-rtio-hdl/csr-map.json` | Generated CSR32 addresses and channel numbers |
| `build-host/local-rtio-hdl/*.init` | ROM contents required alongside the HDL |

Rust is pinned to 1.87.0, matching Piotr’s wip/Nix environment. New diagnostics were also tested with 1.99.0; the original main branch was reproduced with 1.75.0. Python and HDL dependencies are pinned in requirements and source manifests.

## Nix

Piotr’s flake and lock file are preserved. The AArch64 target was added to Rust 1.87, and proprietary `settings64.sh` is optional for work that does not build FPGA artifacts.

```sh
git submodule update --init --recursive
nix develop
make test hdl
```

Recursive initialization matters because meta-xilinx has its own gen-machine-conf submodule. Flake metadata was checked after initialization; the complete Nix closure has not been built. The verified software-only path above does not require Yocto, SDK, Vitis or PetaLinux.

## Vivado: original blinker, then local RTIO

The wip flow targets **Vivado 2025.2**; the original main branch used 2024.2. Other versions have not been validated for the complete flow. Vivado generates PS IP/XSA and implements the HDL. Rust diagnostics use Cargo/LLVM; boot firmware uses the maintained AMD C sources and GNU tools.

```sh
export XILINX_VIVADO=/path/to/Vivado
. "$XILINX_VIVADO/settings64.sh"
. .venv/bin/activate
export PYTHONPATH="$PWD/common/artiq:$PWD/common/migen"
make -C boards/genesys_zu-5ev 1_gateware \
  O=/large-disk/genesys-blinker VARIANT=blinker
make -C boards/genesys_zu-5ev 1_gateware \
  O=/large-disk/genesys-rtio VARIANT=local-rtio
```

The platform exports XSA, XCI and actual pin metadata. The importer checks HPM0 port presence and widths. Use separate output directories for each variant; the Makefile rejects mixed variants.

`gateware.py --no-run` requires a real PS export:

```sh
python boards/genesys_zu-5ev/1_gateware/gateware.py \
  -B /large-disk/genesys-rtio -M /large-disk/genesys-rtio/migen-build \
  --variant local-rtio --no-run
```

The original blinker and local-RTIO variant both passed synthesis, routing and bitstream generation with Vivado 2025.2. Local RTIO runs at 125 MHz with passing timing. See `evidence/vivado-blinker-2026-10-06.json` and `evidence/vivado-local-rtio-2026-10-06.json`; later physical validation is recorded in PORTING_STATUS.md. The historical main-branch XSA does not contain the added local RTIO.

The development host uses a shared container-backed `vivado` launcher, documented in `/home/codex-hil/docs/toolchains/vivado.md`. This host-specific setup is not required on another machine with a suitable Vivado installation.

## Boot firmware and image packaging

Piotr’s original BSP/FSBL flow remains in `3_bootable`. Its `vitis_script.py` requires Vitis to generate the C BSP/FSBL and R5/OpenAMP example. The newer reproduced PMU/FSBL path uses AMD CMake/SDT tooling, GNU Arm and Piotr’s DDR/SPD patch without the Vitis IDE; see below. DDR initialization has not been rewritten in Rust.

AMD bootgen was built from open-source code. Building it requires GCC 12+ and OpenSSL development libraries:

```sh
git clone https://github.com/Xilinx/bootgen.git amd-bootgen
git -C amd-bootgen checkout d93c3fa6e6ef8aa1d4fb4532c58ed4a5efa8804e
make -C amd-bootgen -j2
python3 scripts/build_boot_image.py --bootgen amd-bootgen/build/bin/bootgen \
  --fsbl /path/to/matching-fsbl.elf --bitstream /path/to/top.bit \
  --application build-host/a53/aarch64-unknown-none/release/genesys-a53-bringup \
  --output-dir /large-disk/genesys-a53-boot
```

Optional `--pmufw /path/to/pmufw.elf` includes PMU firmware. The wrapper creates the BIF and records artifact SHA-256 hashes; it does not manufacture missing FSBL/bitstream files or program a device. For the actual ARTIQ runtime image, use [SD boot instructions](docs/SD_BOOT.md).

For the validated JTAG path, use PS system reset → PMU/FSBL → PL configuration → PS/PL setup and CSR preflight → application. Record board/DIMM versions, PS configuration, bitstream/FSBL/ELF hashes and raw UART logs.

## Minimal hardware diagnostics

The DDR-backed A53 diagnostic requires completed FSBL DDR initialization and exclusive access to `0x00100000..0x01100000`. Run it only on A53 core 0. **Do not load it into that region while Linux/OpenAMP is running.** It is neither an R5 application nor an FSBL replacement. The entry point comes from the ELF; startup supports EL3/EL2/EL1 following the upstream AdaCore implementation.

Open the identified UART before starting the diagnostic:

```sh
make test-hw-uart SERIAL=/dev/serial/by-id/GENESYS_UART
```

The runner saves JSON and UART logs, checks transmit/receive with PING/PONG, and collects the cache-maintained 128 KiB DDR test, timer polling and timer interrupt PPI30. Compilation alone does not validate hardware. This scratch test does not establish full RAM capacity or long-term stability.

Local RTIO uses JB1 output and JB2 input, both 3.3 V, with the original revC pin mapping. Verify your board revision before connecting JB1 → JB2. The Linux-PS diagnostic requires the matching local-RTIO bitstream, CSR map and `/dev/mem`:

```sh
sudo python3 scripts/test_rtio_hw.py \
  --csr-map /path/to/migen-build/csr-map.json --output rtio-hardware.json
# Alternatively, on the same PS:
sudo make test-hw CSR_MAP=/path/to/migen-build/csr-map.json
```

It checks PS–PL CSR readback, the RTIO counter and approximate 125 MHz frequency, input timestamps, loopback pulse width, MonInj CSR state and RTIO errors. It does not replace an oscilloscope measurement. UART/DDR/IRQ and Ethernet/DMA are tested by separate runners.

Without configuration, `make test-hw` records NOT_RUN and returns a nonzero status. Historical runners may leave later milestones NOT_RUN even when separate newer tests have passed; consult the evidence and current status rather than treating one partial suite as full acceptance.

## Run a normal ARTIQ experiment

Use the pinned host compiler and device database described in [ARTIQ host setup](docs/ARTIQ_HOST.md), then follow the actual two-core runtime build/start instructions in [3_kernel/README.md](boards/genesys_zu-5ev/3_kernel/README.md). These are separate from the original R5 firmware and management-only daemon, which still rejects kernel execution.

After booting the matching runtime and setting the actual DHCP address in your device database:

```sh
artiq_coremgmt -D device_db.py log
artiq_run --device-db device_db.py examples/ttl_loopback.py
```

The historical `examples/ttl_loopback.py` acceptance example is retained; current physical runtime examples and ABI requirements are documented in `3_kernel/README.md`. CoreDMA instructions are in [docs/CORE_DMA.md](docs/CORE_DMA.md). Use the compiler revision pinned for this port rather than assuming any ARTIQ release or NAC3 master is ABI-compatible.

The last recorded DHCP address was `192.168.2.3`; it can change. Some example databases still contain the earlier `192.168.2.16`, so update the address before running them.

Local analyzer/moninj networking is available in the optional debug runtime. DRTIO master/satellite synchronization and AFCZ remain later stages.

## Kernel ABI prototype without Vivado

The QEMU A53/AArch32 prototype executes a real NAC3 kernel with ARTIQ `EnvExperiment`, `Core` and `TTLOut.pulse_mu()`. See [kernel ABI prototype](prototypes/kernel-abi/README.md).

`make test-kernel-abi` builds the compiler output and M-Labs loader, executes the bare-metal kernel under emulation and runs a negative control. This is software/ABI evidence, separate from the physical Genesys runtime tests.

## OCM diagnostics through JTAG

This path exercises UART/timer/GIC without DDR. It halts all A53 cores on the explicitly selected cable and resets core 0. Startup is adapted from AdaCore/rust-zynqmp `c326ece7eb0a6dda54fa634c52c1cbd0d36a1db8` (Apache-2.0), with a separate linker layout and DDR-dependent MMU setup omitted.

```sh
cd diagnostics/a53
TMPDIR=/srv/codex-hil-data/toolchains/amd/shared/tmp \
RUSTUP_HOME=/srv/codex-hil-data/artiq-zynqmp/rustup \
cargo build --release --locked --features ocm --target-dir /large-disk/a53-ocm
cd ../..
python scripts/validate_a53_elf.py --memory ocm /large-disk/a53-ocm/aarch64-unknown-none/release/genesys-a53-bringup
python scripts/capture_a53_uart.py --ocm --port /dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0 --output /large-disk/ocm-hardware.json
# In another terminal, before capture times out:
xsdb scripts/run_a53_ocm.tcl tcp:HW_SERVER_IP:3121 /large-disk/a53-ocm/aarch64-unknown-none/release/genesys-a53-bringup /large-disk/genesys-blinker/migen-build/ip/psu_init.tcl 210383B7F02DA
```

XSDB is supplied with this Vivado installation. On the development host it can be launched through `vivado-container shell`; resolve the current hw_server container address rather than assuming a fixed IP. Capture with `--ocm` requires UART/RX/timer/IRQ PASS and DDR NOT_RUN. The DDR diagnostic runs without `--ocm`, after FSBL initialization.

## Reproduce PMU and FSBL without the Vitis IDE

Run in the shared Ubuntu container or an equivalent configured environment. Use a fresh output directory: the script copies Piotr’s DDR patch into generated application sources and leaves vendor checkouts intact. SDT/empyro are supplied with the development host’s Vivado installation.

GNU Arm 13.2.Rel1 AArch64 bare-metal archive SHA-256:
`7fe7b8548258f079d6ce9be9144d2a10bd2bf93b551dafbf20fe7f2e44e014b8`.
Obtain it from the official [Arm release](https://gitlab.arm.com/tooling/gnu-toolchains-for-arm/-/releases/13.2.Rel1).

```sh
vivado-container shell
scripts/build_boot_firmware.sh \
  /srv/codex-hil-data/artiq-zynqmp/build-vivado/genesys-blinker/platform.xsa \
  /srv/codex-hil-data/artiq-zynqmp/build-vivado/fsbl-new \
  /srv/codex-hil-data/artiq-zynqmp/toolchains/arm-gnu/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-elf
```

Outputs: `app/build/zynqmp_fsbl.elf`, `pmu-app/build/zynqmp_pmufw.elf` and `artifacts.sha256`. Generated SDT, BSP and build logs remain in the output directory. The reproduced ELFs were physically booted through JTAG.

## Guarded JTAG diagnostic runners

Invoke `Vivado/bin/xsdb` inside the configured tool environment. Each runner requires an explicit cable serial and rejects ambiguous or missing targets. Resolve the current hw_server address.

- `scripts/run_boot_firmware.tcl SERVER_URL PMU_ELF FSBL_ELF CABLE_SERIAL`
- `scripts/run_a53_ddr.tcl SERVER_URL ELF CABLE_SERIAL`
- `scripts/probe_rtio_jtag.tcl SERVER_URL PSU_INIT_TCL CABLE_SERIAL`
- `scripts/probe_ethernet_jtag.tcl SERVER_URL CABLE_SERIAL`

The laboratory Genesys cable is `210383B7F02DA`; UART is `/dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0`, 115200 8N1. Replace both identifiers for your board. Start UART capture before loading the DDR diagnostic.

Run PMU/FSBL before the DDR diagnostic. The boot runner selects alternate JTAG boot through volatile BOOT_MODE_USER; a power cycle restores the boot-switch behavior. The RTIO probe requires the matching PL image and `psu_init.tcl`; it checks an internal output probe rather than an external pin. The read-only Ethernet probe checks PHY MDIO state, not packet traffic.

### Host-side diagnostic suite

After loading the appropriate local-RTIO image and initializing PMU/FSBL:

```sh
make test-hw-jtag \
  PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python \
  O=/srv/codex-hil-data/artiq-zynqmp/build-vivado/hw-suite \
  JTAG_SERVER=tcp:172.17.0.3:3121 JTAG_CABLE=210383B7F02DA \
  SERIAL=/dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0 \
  A53_ELF=/srv/codex-hil-data/artiq-zynqmp/build/a53-ddr-updated/aarch64-unknown-none/release/genesys-a53-bringup \
  PSU_INIT=/srv/codex-hil-data/artiq-zynqmp/build-vivado/genesys-local-rtio/migen-build/ip/psu_init.tcl
```

Logs and `results.json` are saved under `O/jtag-hardware`. The runner returns 1 on diagnostic failure, or 2 when its checks pass but the physical TTL, Ethernet packet and DMA stages remain NOT_RUN in that suite. Make treats the incomplete suite as an error. This command temporarily halts A53 cores and runs the bare-metal diagnostic; it is not a background test of a running ARTIQ core.

## Ethernet packet validation

AMD’s maintained GEM driver and lwIP obtained a DHCP lease and passed ICMP and byte-exact TCP echo tests on the physical board. Repeat the full reset/boot/UART/DHCP/packet/counter test with `make test-hw-ethernet-bringup`, or test a running diagnostic with `make test-hw-ethernet BOARD_IP=<UART DHCP address>`.

See [Ethernet instructions](diagnostics/ethernet/README.md) and `evidence/ethernet-hardware-2026-10-07.json`. This initial golden diagnostic is distinct from the later ARTIQ networking/RPC integration described above.

## Standalone SD boot

The earlier two-core BOOT.BIN passed one physical cold SD boot, management/networking, kernel execution/RPC, TTL loopback and exception recovery. See [SD boot instructions](docs/SD_BOOT.md) for packaging, memory layout, card preservation and acceptance checks. Repeat power-cycle qualification and cold boot of the newer CoreDMA image remain outstanding.

## RTIO DMA

The optional `local-rtio-dma` variant reads standard ARTIQ DMA records from DDR through HP0 and replays them in FPGA. The initial engine test passed 20 pulses / 40 loopback edges and negative underflow/ACK/replay checks: [engine reproducer](diagnostics/DMA_BRINGUP.md).

The subsequent CoreDMA runtime also passed normal recording, named/handle replay and lifecycle tests through `artiq_run`: [CoreDMA instructions](docs/CORE_DMA.md). The previously validated SD image remains non-DMA.

## Si5342 and recovered RX clock

The physical Genesys ZU-5EV Si5342 locked to nominal 125 MHz RXCLK from internal GTH loopback while preserving the 156.25 MHz GTH reference output. The automated test starts with an independent PS clock, switches to RXCLK, removes/restores the clock three times per session and verifies active TX/RX counters with no new settled PRBS7 errors. Two complete sessions passed: six loss/relock cycles.

This is a laboratory profile and internal-loopback result. External Kasli synchronization, jitter, absolute frequency and deterministic latency remain unmeasured; it is not yet a working DRTIO satellite.

See [Si5342 diagnostics](diagnostics/si5342/README.md), `make test-si5342` and `make test-hw-si5342`. The hardware test backs up and restores changed registers without programming OTP. The normal ARTIQ/CoreDMA runtime was restored and its physical DMA experiment passed afterward.
