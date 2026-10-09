# Genesys ZU / ARTIQ port workspace

Continue Piotr Jedyk's port on `bringup/genesys`; original main/wip snapshots
and full mirrors are preserved separately. Read PORTING_STATUS.md before work.
Never report build/QEMU/RTL simulation as hardware validation.

All large sources, toolchains and build outputs belong on
`/srv/codex-hil-data/artiq-zynqmp`, not the nearly full root filesystem.
Reuse existing tools instead of reinstalling them.

- Python: `/srv/codex-hil-data/artiq-zynqmp/venv/bin/python`.
- Rust 1.87: `RUSTUP_HOME=/srv/codex-hil-data/artiq-zynqmp/rustup`.
  Explicitly set this for runtime cargo/rustfmt/rustup commands. The repository
  rust-toolchain file otherwise may trigger a download into the global home.
- NAC3 ABI prototype compiler uses the global `cargo +stable` (tested 1.99).
  The runner separates compiler and runtime RUSTUP_HOME.
- Verified LLVM19/GCC ARM/QEMU tools:
  `/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified`.
  Registry: scripts/abi-tools.json. Setup does not require sudo.
- Prototype NAC3 checkout: `/srv/codex-hil-data/artiq-zynqmp/work/nac3-abi`,
  pinned at 322b7bd2537e176d7997f816ae2fb6ab9e029939; do not edit it.
- Current ARTIQ: `/srv/codex-hil-data/artiq-zynqmp/reference/artiq`.
  Compatible current sipyco: `/srv/codex-hil-data/artiq-zynqmp/work/sipyco-abi`.

`make test hdl` verifies host/RTL/builds. `make test-kernel-abi` separately
checks actual NAC3/ARTIQ kernel execution under A53 emulation, including a
negative control. Instructions are in prototypes/kernel-abi/README.md.
Original daemon still rejects kernel execution; the prototype is separate.
Shared Vivado 2025.2 is installed and Piotr blinker bitstream built successfully.
Read /home/codex-hil/docs/toolchains/vivado.md. Physical Genesys cable is
210383B7F02DA, UART FTDI channel B (if01). Other FPGA boards are attached:
select exclusively the identified cable. PS/DDR/UART/IRQ/GEM/local-RTIO
and Rust management TCP1380 have physical PASS evidence in PORTING_STATUS.md.
See diagnostics/services/README.md for the management-only integration.
Kernel loader/RPC, physical TTL loopback, RTIO DMA, analyzer/moninj remain pending.
Use PS system reset → PMU/FSBL → local-RTIO bitstream → PS/PL setup and
CSR preflight → application. PL before PS reset led to AXI timeout/core hang.

Physical CPU1 EL3/AArch64 → EL1/AArch32 trusted-kernel ABI/loader diagnostic
passed 2026-10-07, including negative assertion and real PL counter read.
See diagnostics/kernel-a53/README.md; outputs remain a memory model.
It reserves 0x20000000/0x200FF000/0x20200000–0x20400000; CPU0 management
remains active. Network kernel upload/run and real RTIO exports still pending.

Shared host ARTIQ CLI venv: /srv/codex-hil-data/artiq-zynqmp/venvs/artiq-host.
Launchers ~/.local/bin/artiq_{compile,run,coremgmt} and artiq-host.
See docs/ARTIQ_HOST.md for pinned compiler/source revisions and dependencies.
Offline examples/genesys_ttl.py compilation passed; do not run physical
experiments until kernel network runtime/real RTIO exports are integrated.

Current physical runtime: network-kernel-services-final + kernel-worker.
Normal artiq_run examples/genesys_network_probe.py now performs genuine
Ethernet load/execute/scalar RPC on CPU1, preserving CPU0 management.
See boards/genesys_zu-5ev/3_kernel/README.md and evidence/network-kernel-*.
Runtime mode kernel-bringup; TTL exports, exceptions/unwind, complex returns,
DMA/analyzer/moninj remain pending. Do not run physical TTL experiments yet.
Boot CPU1 before CPU0; run_a53_runtime.tcl preserves it. Old run_ethernet.tcl
halts all cores. Management rtio_counter returns Error while a kernel runs
(to avoid contending with CPU1 for the shared latch). Reserve 0x21000000
for 1 MiB upload, in addition to the earlier CPU1 image/mailbox range.

Latest runtime: rtio-kernel-services + kernel-worker-rtio-final (2026-10-07).
Kernel CSR timeline, scheduled channel1 input sample and data/timeout have
hardware PASS; rtio_output/input exports enabled. TTL and loopback ELF load
without execution are checked. Physical JB1 pulses/JB1→JB2 still NOT_RUN.
make test-hw-rtio-kernel runs without a jumper or output pin transitions.
Optional --underflow parks CPU1; full runtime reboot required afterward.

2026-10-08: physical JB1→JB2 loopback PASS10/10 after user corrected jumper.
Both edges, width12500mu=100us, latency15mu=120ns fixed; no extra edge.
make test-hw-ttl-loopback validates real artiq_run; jumper currently fitted.
USB ACL restored on001/006; restarted JTAG server172.17.0.2:3121.
Evidence ttl-loopback-2026-10-08.json supersedes older pending/fail notes.

2026-10-08 native exceptions: latest CPU0 build-vivado/eh-kernel-services and
CPU1 build/kernel-worker-eh-final. M-Labs ARM unwinder + DWARF preserved.
Catch/reraise/finally, kernel/RPC/RTIO errors and automatic CPU1 activation
recovery PASS; same TCP connection works afterward. make test-hw-kernel-exceptions.
Network test --underflow now expects typed exception and successful recovery,
not historical fail-stop. Old probe_rtio_failure.tcl applies to old images.
Hardware traps/panic/watchdog/disconnect and complex RPC still limited.
Evidence kernel-exceptions-*-2026-10-08.json; standard boot order unchanged.

2026-10-08 SD boot image prepared at build/sd-boot-2026-10-08/BOOT.BIN.
Cold SD boot NOT_RUN; do not claim autonomous boot from JTAG evidence.
Embedded CPU1 bridge build/sd-worker-2026-10-08/worker-boot.elf clears
cold mailbox; current CPU0 waits up to5s for READY. JTAG networking and
TTL10/10 PASS. Read docs/SD_BOOT.md; no card/flash writes performed.

Latest: physical cold SD boot PASS2026-10-08, one power cycle. Board runs
from card/J9/JP3 SD without JTAG download/setup. Evidence sd-cold-boot-*.
Management9, network5, TTL10/10, exception30 and Ethernet PASS. Prior SD
NOT_RUN notes historical; repeat power cycles and production qualification pending.

Latest2026-10-08: hardware RTIO DMA engine PASS through JTAG, variant
local-rtio-dma, build-vivado/genesys-rtio-dma and dma-ps-2025.2.5 plays,
20 pulses/40 JB1→JB2 edges,2 negative underflow/ACK tests and next replay PASS.
CoreDMA exports/recording/named storage are NOT implemented; do not claim
CoreDMA experiment support. DMA buffer debug0x22000000. Read diagnostics/
DMA_BRINGUP.md and evidence/dma-*. Existing SD image still non-DMA.
Boot debug: select alternate JTAG before system reset (fixed script), because
a working SD image otherwise boots during FSBL download. Shared launchers
unchanged; new build script limits local Vivado threads2 after exit137.

Latest2026-10-08 CoreDMA API physical PASS. Current CPU1 is
build/kernel-worker-dma-final with same DMA PL/PS and CPU0 eh-kernel-services.
make test-hw-core-dma uses normal ARTIQ API;21 CLI invocations,216 pulses/
432 edges (100us and64ns), lifecycle/limits/errors/persistence PASS.
Reserve DDR0x22000000–0x22200000 for32x64KiB named traces; survives ELF
reload and exception recovery, not CPU1 hardware/image reset. Do not use
old DAP DMA probe on committed traces: it overwrites slot0. New SD package
build/sd-core-dma-2026-10-08/BOOT.BIN prepared; its cold SD boot NOT_RUN.
Card still holds validated earlier non-DMA image. Read docs/CORE_DMA.md.
NAC3 pinned return tuple ABI24B(header8); compile-time offsets enforced.
Wide outputs,DDMA, hardware-stall recovery and production qualification pending.

2026-10-08 DRTIO preparation: user target now Kasli master -> ZynqMP satellite
with future AD9172 JESD204B DAC. diagnostics/drtio contains separate GTHE4
X0Y7 raw20-bit2.5Gb/s OOC build for125/156.25MHz refs (user clocks125MHz),
verifier and protocol simulation targets. Both profiles synthesis PASS;
19 legacy +19 current protocol RTL tests PASS. No DRTIO link or Si5342
write/readback hardware test yet; no board bitstream/top generated here.
Elastic buffers enabled in diagnostic PHY, no deterministic latency claim.
Existing Digilent clock-control sources preserved in mirrors; origins in
diagnostics/drtio/clock-source-origins.json. Read docs/DRTIO_CLOCKING.md.

Latest2026-10-08 physical GTH diagnostic PASS supersedes the earlier
no-board-top note. Separate PS/HPM0 diagnostic top is in diagnostics/drtio;
build-vivado/drtio-diagnostic-relocated-2026-10-08 contains bitstream,
resumed build logs and corrected timing/Gray bus-skew reports. Physical
internal PMA PRBS7 passed3 resets, RX/TX-to-PS clock ratios, intentional
PRBS15 mismatch errors and reset recovery. Module TX remained disabled,
mux D10=1. This proves local GTH only, not external SFP/remote DRTIO.
No Si5342 writes, recovered-input lock or deterministic latency test.
Old Migen mr_ff false-path targets nets; diagnostic checked register-D
constraints fix that locally. Separate copied XCI output paths prevent
multi-IP collisions. Do not modify original archived IP/Migen sources.
Board restored to prior CoreDMA runtime192.168.2.16; Ethernet and normal
artiq_run genesys_dma.py physical8 pulses/16 edges PASS. Evidence files
evidence/drtio-{top-build,phy-loopback,restored-core}-2026-10-08.*.
Diagnostic CSR magic0x44525430 is incompatible with RTIO map; only use its
probe while diagnostic PL loaded and A53 CPUs halted. Next remote-link test
needs user's Kasli, matched ARTIQ/RTIO frequency and suitable SFP/cable.

Latest Kasli master preparation2026-10-08: user requested newest standard
Kasli hardware, v2.1 (not Kasli-SoC). diagnostics/kasli-master has JSON,
minimal Nix tools environment, reproducible build script and README.
Separate upstream worktrees work/kasli-master@486e8f8 and
work/kasli-misoc@0e99d28 preserve sources; Migenbeffe831 and Vex2e4f43d.
build/kasli-v2.1-master-2026-10-08/generated/genesys_drtio_master/software
contains verified bootloader/ksupport/runtime; firmware PASS, ELF32 RISC-V
and runtime.fbi length/CRC PASS. Build overall PARTIAL: shared Vivado lacks
Artix-7/XC7A100T support. AMD installed-tree Add rejects expired token;
user was asked to run vivado-installer2025.2 AuthTokenGen. Do not claim a
successful Kasli bitstream. 117 offline archives cached by symlink under
Xilinx/Downloads/Vivado_2025.2/payload, originals extracted selectively
under shared/installers/kasli-offline-2025.2 (~2.47GB). Add configuration is
shared/install-2025.2-kasli-artix7.conf. Use installed .xinstall/2025.2/xsetup
-b Add after auth renewal; full offline-image Add tried fresh install and
failed disk check. Shared installation and Genesys physical state unchanged.
Firmware toolchain Nix Rustnightly2021-09-01/LLVM20.1.8 prepared; old Cargo
index is cached under build/kasli-v2.1-master-2026-10-08/cargo-home.
Assumed test configuration: no EEM, RTIO125MHz, WRPLL off; optional question
about user's modules remains pending. Evidence kasli-v2.1-master-2026-10-08.json.

Latest2026-10-09: shared Vivado Artix-7 Add completed offline from SMB,
no AMD token needed. get_parts XC7A100T24 / XCZU5EV26 and small synthesis
for both PASS. evidence/artix7-install-2026-10-09.json. Read shared Vivado
notes for read-only SMB tar FUSE helper; it is unmounted after installation.
Full Kasli master gateware build resumed in existing output tree. Previous
AMD-token blocker is superseded; do not ask user to renew authentication.

Latest2026-10-09 Kasli master complete BUILD_PASS_HARDWARE_NOT_RUN.
Existing generated output contains top.bit/top.bin plus firmware; timing
WNS0.141ns/WHS0.037ns and bitgen PASS. Packaged tar.gz and hashes/results
in build/kasli-v2.1-master-2026-10-08. Build script fixes suppression of .bit
locally. OpenOCD+bscan package symlink toolchains/kasli-openocd (from pinned
flake); prepend its bin to PATH for artiq_flash. Dry-run PASS, no flash/JTAG
write and no physical Kasli test. Review timing-scope caveats in evidence.

Resume2026-10-09: USB Genesys/Kasli absent after host restart. No hardware
writes. Raw20Codec plus wire-level RT/AUX simulation added under diagnostics/
drtio; make test-drtio-codec passes3 tests on Piotr/current snapshots.
Not wired into GTH top and no clock recovery/deterministic-latency proof.
Kasli1.1 qualification belongs to the separately requested thread.

Latest2026-10-09 Si5342 recovered-clock hardware PASS. Genesys USB returned.
New diagnostics/si5342 uses AMD XIicPs standalone BSP, main I2C0/mux0x70
channel2/Si0x68;100us held-RX-to-TX guard and STOP/bus-idle sequencing.
Two3072-register backups verified all12 pages/identity5342/rev03.
Optional FORWARD_RX_CLOCK=1 GTH top adds A2/A1 DIFF_HSTL_I_DCI_12,
ODDRE1/OBUFDS and BUFGCTRL PS125MHz vs GTH RX125MHz. CSR forward-enable
0xA0000030 and bootstrap-select0xA0000034, magic0x44525430. Build/timing PASS.
P0=63/M=1386 integer profile preserves factory VCO13.75GHz and OUT156.25MHz.
Hardware loader + make test-hw-si5342 passed two sessions/six loss/relock
cycles, both clocks active and zero new settled PRBS7 errors. Correct
integer clock gates, near-original1.984MHz PFD, GTH reset after Si config
and no redundant outer reset are required. Laboratory OOF window widened;
absolute threshold/jitter/remote accuracy are not measured. No OTP/flash.
Not a DRTIO satellite or deterministic-latency proof. Source evidence
si5342-{readout,recovered-clock,restored-core}-2026-10-09.json and README.
Normal ARTIQ/CoreDMA PL+worker+CPU0 restored, DHCP now192.168.2.3 (old.16
is stale). Normal artiq_run GenesysDMA passed8 physical pulses/16 edges.
Example device_db still has.16: use actual DHCP address or copied test DB.
Use exact Genesys JTAG cable210383B7F02DA; Kasli1.1 remains another thread.

Latest2026-10-09 continuation: physical upstream RT/AUX link framing over
GTH PMA loopback PASS3 resets, zero settled errors, detected corruption and
recovery. Autonomous diagnostic Si5342 firmware PS bootstrap/RX switch and
three loss/recovery cycles PASS, volatile registers restored. Neither is a
production satellite or deterministic latency proof. No other board writes.

Current normal local runtime: PL build-vivado/rtio-debug-fixed-2026-10-09/
top.bit, CPU0 build-vivado/debug-services-2026-10-09/amd/app/build/
lwip_echo_server.elf, same CPU1 build/kernel-worker-dma-final. DHCP192.168.2.3.
Standard analyzer1382 and MonInj1383 physical PASS;72 DMA pulses/144 edges
plus native DMA mask255/underflow record PASS. Analyzer is256-record BRAM
with brief retrieval pause, one client per port, MonInj500ms polling; DDR
analyzer DMA remains absent. Docs RTIO_DEBUG.md and evidence rtio-debug-*.
Shared hw_server restarted after daemon recovery, container172.17.0.3;
resolve its actual address each time and use exact Genesys cable.

New SD image build/sd-debug-2026-10-09/boot.bin packaged, NOT cold-booted.
USB card/reader absent; no card write. Preserve earlier image. User asked
whether card can be moved after debug tests; physical reply remains pending.
Do not edit shell script files while those scripts are executing: Bash may
read later commands from changed offsets. Copy scripts for active long runs.
