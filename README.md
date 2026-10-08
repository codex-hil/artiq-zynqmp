# ARTIQ / Genesys ZU-5EV — odzyskanie portu Piotra Jedyka

Rozwój kontynuuje `pjedyk/artiq-new`, na gałęzi `bringup/genesys` bazującej
na `wip@b25e75b`. **Runtime wykonuje już kernela przez Ethernet i obsługuje
podstawowy RPC oraz fizyczny TTL output/input na Genesys ZU.**

Host `artiq_run` → AMD/lwIP na CPU0 AArch64 → loader M-Labs na CPU1 AArch32
→ rzeczywiste wykonanie i RPC działa. Pięć uruchomień oraz testy negatywne PASS.
Management, DDR/UART/IRQ/Ethernet oraz kernel→RTIO timeline/input/sample sprawdzone.
Fizyczny JB1→JB2 loopback: 10/10 PASS, impuls100 µs, stałe opóźnienie120 ns.
Native wyjątki kernel/RPC/RTIO, reraise/finally oraz odzyskiwanie po błędzie
bez resetu urządzenia przeszły testy hardware (30 eksperymentów).
Boot z SD, RTIO DMA, analyzer/moninj i produkcyjna kwalifikacja pozostają do integracji.

Instrukcja buildu/startu/runtime i test bez TTL:
[boards/genesys_zu-5ev/3_kernel/README.md](boards/genesys_zu-5ev/3_kernel/README.md).
Poprzednie etapy: [diagnostics/kernel-a53/README.md](diagnostics/kernel-a53/README.md),
[diagnostics/services/README.md](diagnostics/services/README.md).

Narzędzia hosta są zainstalowane: `artiq_compile`, `artiq_run`, `artiq_coremgmt`.
Instrukcja: [docs/ARTIQ_HOST.md](docs/ARTIQ_HOST.md).

Dokładny stan: [PORTING_STATUS.md](PORTING_STATUS.md). Architektura i decyzje:
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Źródła i revisions:
[docs/SOURCES.md](docs/SOURCES.md). Problemy buildu:
[docs/BUILD_COMPATIBILITY.md](docs/BUILD_COMPATIBILITY.md).

## Clone i zachowanie źródeł

Ta gałąź nie została wypchnięta na GitHub. Na hoście roboczym:

```sh
git clone --branch bringup/genesys \
  /home/codex-hil/artiq-zynqmp/work/artiq-new-wip artiq-genesys
cd artiq-genesys
git submodule update --init common/artiq common/migen
```

Na innym hoście należy skopiować `genesys-bringup.bundle`, potem:

```sh
git clone --branch bringup/genesys genesys-bringup.bundle artiq-genesys
cd artiq-genesys
git submodule update --init common/artiq common/migen
```

Oryginał do porównania:

```sh
git clone https://github.com/pjedyk/artiq-new.git piotr-original
git -C piotr-original checkout wip
```

Nie nadpisuj oryginalnych checkoutów. Mirrory na tym hoście są w
`/srv/codex-hil-data/artiq-zynqmp/sources`, kod roboczy w `work`, artefakty
w `build`. `/home/codex-hil/artiq-zynqmp/work` wskazuje na duży wolumen.

Pełne archiwum źródeł można odtworzyć niezależnie:

```sh
python3 scripts/acquire_sources.py --destination /large-disk/artiq-sources \
  --manifest evidence/sources.json --include-yocto
```

Istniejące mirrory nie są automatycznie aktualizowane. Manifest zapisuje
dokładny SHA wszystkich refs oraz sprawdza pinowane gitlinki. Aktualny
upstream M-Labs jest zapisany osobno od historycznych refs GitHub.

## Build/test bez hardware i bez Vivado/Vitis

Wymagania: Python3.12, git, GNU make, rustup; około1 GB na narzędzia i kilka
GB na kompletne źródła/Yocto. Użyj wolumenu z odpowiednią ilością miejsca.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-host.txt
rustup toolchain install 1.87.0 --profile minimal --component rustfmt \
  --target armv7r-none-eabihf --target aarch64-unknown-none
make test hdl
```

Jeśli systemowy Python nie ma ensurepip, potrzebny jest pakiet venv albo
izolowany bootstrap pip. Nie modyfikuj systemowych pakietów Python przez pip.

`make test` wykonuje12 testów host/symulacji, buduje oryginalną bibliotekę
R5 oraz A53 diagnostic, i sprawdza rzeczywisty ELF entry/load segments.
`make hdl` generuje local RTIO/AXI subsystem Verilog i CSR map bez PS IP.
Nie wytwarza board bitstreamu ani XSA.

```sh
make test hdl O=/large-disk/artiq-build
make test-sim
make firmware
make diagnostics
```

Artefakty:

| Artefakt | Znaczenie |
|---|---|
| build-host/original-r5/cargo-build/armv7r-none-eabihf/release/librust_firmware.a | oryginalny Rust staticlib Piotra; nie runtime ARTIQ |
| build-host/a53/aarch64-unknown-none/release/genesys-a53-bringup | ELF diagnostyczny A53 ze startupem/MMU/UART/DDR/timer/IRQ |
| build-host/local-rtio-hdl/local_rtio.v | rzeczywiste upstream RTIO + AXI/CSR, bez PS board wrapper |
| build-host/local-rtio-hdl/csr-map.json | wygenerowane adresy CSR32 i numery kanałów |
| build-host/local-rtio-hdl/*.init | zawartości ROM wymagane razem z HDL |

Rust jest przypięty do1.87.0 zgodnie z wip/Nix Piotra; nowe diagnostics
sprawdzono także na1.99.0. Main Piotra odtworzono z oryginalnym1.75.0.
Python i źródła HDL są przypięte w requirements i manifestach.

## Nix

Zachowano flake/lock Piotra. Dodano target AArch64 do istniejącego Rust1.87
i dopuszczono brak proprietary settings64.sh podczas pracy bez FPGA.

```sh
git submodule update --init --recursive
nix develop
make test hdl
```

Recursive update jest istotne: meta-xilinx ma własny gen-machine-conf.
Sprawdzono metadane flake po rozwinięciu tych submodules; pełnej Nix closure
nie zbudowano. Do testów programowych prostsza zweryfikowana ścieżka powyżej
nie wymaga Yocto, SDK, Vitis ani PetaLinux.

## Vivado: najpierw oryginalny blinker, potem local RTIO

Wip zakłada Vivado2025.2. Main miał2024.2. Nie zweryfikowano zgodności
pełnego flow z inną wersją. Vivado ma wygenerować PS IP/XSA i zsyntezować
HDL; firmware diagnostyczny pozostaje budowany przez Cargo/LLVM.

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

Platforma generuje XSA, XCI i rzeczywiste metadata pinów. Importer sprawdza
obecność i szerokości portów HPM0. Nigdy nie zastępuj tych eksportów
wymyślonymi plikami, żeby ukryć brak Vivado. Używaj osobnych katalogów dla
wariantów; Makefile wykrywa próbę mieszania.

`gateware.py --no-run` działa dopiero z prawdziwym eksportem PS:

```sh
python boards/genesys_zu-5ev/1_gateware/gateware.py \
  -B /large-disk/genesys-rtio -M /large-disk/genesys-rtio/migen-build \
  --variant local-rtio --no-run
```

Migacz Piotra zbudowano Vivado 2025.2 (synteza/routing/bitgen PASS);
dowody: `evidence/vivado-blinker-2026-10-06.json`. Wspólne `vivado`
działa przez kontener; patrz `/home/codex-hil/docs/toolchains/vivado.md`.
Wariant local-rtio również przeszedł pełny build (125 MHz, timing PASS);
dowody: `evidence/vivado-local-rtio-2026-10-06.json`. Hardware NOT_RUN. W historycznym main XSA jest stary bitstream, który nie
zawiera dodanego local RTIO.

## Boot i minimalne testy hardware

Zachowano golden BSP/FSBL flow Piotra w `3_bootable`; obecny skrypt
`vitis_script.py` rzeczywiście wymaga Vitis do wygenerowania C BSP/FSBL
i przykładu R5/OpenAMP. Nie jest wymagany do Cargo diagnostic ani symulacji.
Zastąpienie generowania FSBL utrzymywanym AMD CMake/SDT flow jest nadal do
odtworzenia, z board DDR patch Piotra. Nie przepisano DDR do Rust.

Sam bootgen zbudowano z otwartego kodu AMD, bez instalacji Vitis. Na tym hoście:
`/srv/codex-hil-data/artiq-zynqmp/work/bootgen/build/bin/bootgen`.
W innym środowisku potrzebuje GCC12+ i OpenSSL development libraries:

```sh
git clone https://github.com/Xilinx/bootgen.git amd-bootgen
git -C amd-bootgen checkout d93c3fa6e6ef8aa1d4fb4532c58ed4a5efa8804e
make -C amd-bootgen -j2
python3 scripts/build_boot_image.py --bootgen amd-bootgen/build/bin/bootgen \
  --fsbl /path/to/matching-fsbl.elf --bitstream /path/to/top.bit \
  --application build-host/a53/aarch64-unknown-none/release/genesys-a53-bringup \
  --output-dir /large-disk/genesys-a53-boot
```

Opcjonalne `--pmufw /path/to/pmufw.elf` dodaje PMU firmware, jeśli wymaga go
docelowy boot flow. Wrapper generuje BIF i zapisuje SHA-256 dostarczonych
artefaktów; nie wytwarza brakującego FSBL/bitstreamu i niczego nie programuje.
Pakowanie nie zostało jeszcze wykonane z kompletem artefaktów Genesys.

Kolejność uruchamiania: konfiguracja FPGA -> PS boot/FSBL -> UART ->
clocks/DDR -> AXI -> timer/IRQ -> Ethernet. Zapisuj wersje płytki/DIMM,
PS config, SHA bitstreamu, FSBL i ELF oraz raw UART logs.

Diagnostic A53 wymaga zakończonej inicjalizacji DDR przez FSBL i wyłącznego
dostępu do obszaru `0x00100000..0x01100000`. Uruchamiaj tylko A53#0.
**Nie wgrywaj go do tego regionu podczas pracy Linux/OpenAMP.** Nie jest
drop-in aplikacją R5 ani zamiennikiem FSBL. Entry pochodzi z ELF, nie z
domyślnego adresu0. Adapter obsługuje EL3/EL2/EL1 zgodnie z upstream AdaCore.

Na hoście podłączonym do zidentyfikowanego UART (otwórz przed startem ELF):

```sh
make test-hw-uart SERIAL=/dev/serial/by-id/GENESYS_UART
```

Skrypt zapisuje JSON i UART log, sprawdza TX, wysyła PING i oczekuje PONG,
zbiera test DDR128 KiB z cache maintenance, timer polling i timer interrupt
PPI30. Sam build nie zalicza tych testów. Ten test DDR nie wystarcza jeszcze
do potwierdzenia pełnej pojemności i stabilności RAM.

Wariant local RTIO: JB1 output, JB2 input, oba3.3 V, pinout z oryginalnego
revC XDC Piotra. Po potwierdzeniu rewizji połącz JB1->JB2. Test z Linux PS
potrzebuje **matching local-rtio bitstream**, mapy CSR oraz `/dev/mem`:

```sh
sudo python3 scripts/test_rtio_hw.py \
  --csr-map /path/to/migen-build/csr-map.json --output rtio-hardware.json
# lub, na tym samym PS:
sudo make test-hw CSR_MAP=/path/to/migen-build/csr-map.json
```

Test sprawdza PS-PL CSR readback, counter, przybliżoną częstotliwość125 MHz,
input timestamps i deterministyczną szerokość impulsu przez fizyczny
loopback. Mierzy także końcowy stan MonInj CSR i błędy RTIO. Nie zastępuje
pomiaru wyjścia oscyloskopem. UART/DDR/IRQ to osobna faza A53 diagnostic;
Ethernet i DMA nie są jeszcze testowane przez ten runner.

`make test-hw` bez konfiguracji zapisuje NOT_RUN i zwraca niezerowy kod.
Także częściowo wykonana seria pozostawia niezaimplementowane etapy jako
NOT_RUN i nie zgłasza pełnego sukcesu. Na obecnym hoście wszystkie testy
hardware mają NOT_RUN.

## Do normalnego eksperymentu ARTIQ

Wymagane pozostałe kroki: kernel ISA/ABI -> loader/ksupport/unwind ->
networking -> management -> RPC -> RTIO kernel syscalls. Dopiero potem:

```sh
artiq_coremgmt -D device_db.py log
artiq_run -D device_db.py examples/ttl_loopback.py
```

To **warunek akceptacji do wdrożenia**, a nie komendy obecnie zakończone
sukcesem. Nie dostarczono fikcyjnego device_db z CortexA9 dla R5/AArch64.
Przykład eksperymentu jest przygotowany dla ARTIQ9 i wymaga zweryfikowanego
Core target/ABI; NAC3 master wymaga osobnej zgodności. Obecny daemon
`artiq_cored` jawnie odrzuca LoadKernel/RunKernel zamiast udawać wykonanie.

DMA/analyzer/moninj network są kolejną warstwą. DRTIO, GT/recovered clock,
master/satellite i AFCZ pozostają po fizycznym potwierdzeniu local RTIO.

## Kernel ABI bez Vivado

Dostępny jest wykonywany pod QEMU prototyp A53/AArch32 z prawdziwym
kernellem NAC3 oraz aktualnymi klasami ARTIQ `EnvExperiment`, `Core`,
`TTLOut.pulse_mu()`. Instrukcje: [prototypes/kernel-abi/README.md](prototypes/kernel-abi/README.md).
`make test-kernel-abi` uruchamia kompilację, loader M-Labs, A53 bare-metal
i test negatywny. To nadal nie jest uruchomiony core device na Genesys.

## Zweryfikowana diagnostyka OCM przez JTAG

Ta ścieżka uruchamia UART/timer/GIC bez DDR, nie pełny ARTIQ. Zatrzymuje
wszystkie A53 wyłącznie na kablu o podanym serialu i resetuje A53#0.
Startup: adaptacja AdaCore/rust-zynqmp c326ece7eb0a6dda54fa634c52c1cbd0d36a1db8
(Apache-2.0), z osobnym linkerem i pominięciem MMU wymagającego DDR.

```sh
cd diagnostics/a53
TMPDIR=/srv/codex-hil-data/toolchains/amd/shared/tmp \
RUSTUP_HOME=/srv/codex-hil-data/artiq-zynqmp/rustup \
cargo build --release --locked --features ocm --target-dir /large-disk/a53-ocm
cd ../..
python scripts/validate_a53_elf.py --memory ocm /large-disk/a53-ocm/aarch64-unknown-none/release/genesys-a53-bringup
python scripts/capture_a53_uart.py --ocm --port /dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0 --output /large-disk/ocm-hardware.json
# W drugim terminalu, zanim capture upłynie:
xsdb scripts/run_a53_ocm.tcl tcp:HW_SERVER_IP:3121 /large-disk/a53-ocm/aarch64-unknown-none/release/genesys-a53-bringup /large-disk/genesys-blinker/migen-build/ip/psu_init.tcl 210383B7F02DA
```

XSDB jest dostarczone razem z zainstalowanym Vivado; można je uruchomić
przez `vivado-container shell -c 'exec /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb ...'`.
Adres hw_server to IP jego kontenera w osobnym Dockerze (docker inspect).
Capture z `--ocm` wymaga PASS UART/RX/timer/IRQ oraz DDR NOT_RUN.
Oryginalny test DDR uruchamia się bez `--ocm` po poprawnym FSBL.

## Physical Genesys milestones (2026-10-07)

JTAG configuration, A53 EL1 startup, bidirectional UART, timer PPI30,
AMD PMU/FSBL with Piotr's dynamic DDR/SPD patch, and a cache-flushed 128 KiB
DDR test passed on the physical ZU-5EV. Local RTIO CSR readback and counter,
a scheduled output's internal PHY probe, and GEM0 PHY link passed too.
This does not yet provide a working ARTIQ core device. Physical TTL loopback,
full DDR stress, Ethernet packets, management/RPC and DMA remain pending.
See `PORTING_STATUS.md` and `evidence/genesys-fsbl-rtio-hardware-2026-10-07.json`.

### Reproduce PMU and FSBL without Vitis IDE

Run in the shared Ubuntu container. Use a fresh output directory; the script
copies Piotr's DDR patch into generated application sources, leaving vendor
sources intact. SDT/empyro are supplied with this Vivado installation.
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

Output: `app/build/zynqmp_fsbl.elf`, `pmu-app/build/zynqmp_pmufw.elf`,
`artifacts.sha256`. Generated SDT and BSP/build logs remain in the output.
The complete script was exercised in `build-vivado/fsbl-reproduced` and both
resulting ELFs were booted through JTAG.

### Guarded JTAG diagnostic runners

Inside `vivado-container shell`, invoke the installed `Vivado/bin/xsdb`.
Each runner requires an explicit cable serial and rejects ambiguous/missing
targets; other connected boards are left alone. Resolve the running hw_server
container's current IP rather than assuming it remains `172.17.0.3`.
Arguments (also in each script's first line):

- `scripts/run_boot_firmware.tcl SERVER_URL PMU_ELF FSBL_ELF CABLE_SERIAL`
- `scripts/run_a53_ddr.tcl SERVER_URL ELF CABLE_SERIAL`
- `scripts/probe_rtio_jtag.tcl SERVER_URL PSU_INIT_TCL CABLE_SERIAL`
- `scripts/probe_ethernet_jtag.tcl SERVER_URL CABLE_SERIAL`

Genesys cable: `210383B7F02DA`; URL used during validation:
`tcp:172.17.0.3:3121`. UART:
`/dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0`,
115200 8N1. Start `scripts/capture_a53_uart.py` on the host before the DDR
runner; it sends PING and requires all five diagnostics to pass.

Run PMU/FSBL before DDR. The boot runner selects alternate JTAG boot in
volatile BOOT_MODE_USER; power cycling restores boot-switch behavior.
Program the **local-rtio** bitstream before the RTIO probe and pass its
`migen-build/ip/psu_init.tcl`. The probe changes only PL clock/AFI/reset,
preserving trained DDR, and enables XSDB forced accesses to the known CSR
aperture. It checks internal output high/low, not the external pin.
The Ethernet probe uses AMD GEM register definitions for read-only PHY MDIO
queries and restores GEM management settings; it does not test packets.
Physical TTL input/output requires JB1→JB2 and the separate loopback test.

### Host-side repeatable hardware suite

After loading local-rtio and starting PMU/FSBL, run on the host:

```sh
make test-hw-jtag \
  PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python \
  O=/srv/codex-hil-data/artiq-zynqmp/build-vivado/hw-suite \
  JTAG_SERVER=tcp:172.17.0.3:3121 JTAG_CABLE=210383B7F02DA \
  SERIAL=/dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0 \
  A53_ELF=/srv/codex-hil-data/artiq-zynqmp/build/a53-ddr-updated/aarch64-unknown-none/release/genesys-a53-bringup \
  PSU_INIT=/srv/codex-hil-data/artiq-zynqmp/build-vivado/genesys-local-rtio/migen-build/ip/psu_init.tcl
```

Logs and `results.json` are saved under `O/jtag-hardware`. The Python runner
returns 1 on diagnostic failure, 2 when these diagnostics pass but physical
TTL, Ethernet packets and DMA remain NOT_RUN. Make reports that incomplete
suite as an error; do not interpret diagnostic PASS as the full project's DoD.
This command temporarily halts A53 cores and runs the bare-metal diagnostic.

## Ethernet packet milestone — physical PASS

The Genesys now obtains a DHCP lease and passes ICMP/TCP echo through GEM0
using AMD's maintained bare-metal driver and lwIP. The complete reset/PMU/FSBL/
UART/DHCP/MAC/packet/counter test is repeatable with
`make test-hw-ethernet-bringup`; an already running diagnostic is tested with
`make test-hw-ethernet BOARD_IP=<UART DHCP address>`.

See [Ethernet build and hardware instructions](diagnostics/ethernet/README.md).
Evidence: `evidence/ethernet-hardware-2026-10-07.json`. This validates Ethernet
hardware, GEM DMA and initial byte-exact packet transfers. Production ARTIQ
networking and management/RPC integration remain pending.

## Standalone SD boot preparation (2026-10-08)

Complete current two-core BOOT.BIN passed physical cold SD boot (one power
cycle), networking/management, kernels/RPC, TTL10/10 and exception recovery.
See [SD boot instructions](docs/SD_BOOT.md) for reproducible packaging,
memory layout, card preservation and physical acceptance checks.
Updated CPU0 + embedded CPU1 image passed JTAG networking and TTL10/10.

## RTIO DMA engine (2026-10-08)

Optional local-rtio-dma variant reads standard ARTIQ records from DDR through
HP0 and replays them in FPGA. Physical20 pulses/40 loopback edges and native
DMA underflow/ACK/replay passed. Ordinary CoreDMA recording/handles remain
pending. [Build and hardware reproducer](diagnostics/DMA_BRINGUP.md).
The validated SD image retains the preceding non-DMA runtime.
