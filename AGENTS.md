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

2026-10-11 packet diagnostic development: use shared exact-board flock
/home/codex-hil/.cache/genesys-210383B7F02DA.lock across Genesys reset,
programming, UART/DAP/network test and restoration. Packet bring-up wrapper
scripts/test_drtio_packets_bringup.py enforces it and attempts restoration
in finally. New DRTIO_PACKETS diagnostic replaces local RTIO while loaded;
it is a time-slotted single-GTH protocol test with a diagnostic CRI backend,
not a production satellite. Refer to newest PORTING_STATUS for results.

Latest2026-10-11 physical RT packets PASS: final diagnostic PL
build-vivado/drtio-packets-armed-2026-10-11, WNS2.641/WHS0.012ns,
604 CDC bits/19 Gray buses. Three resets/36 cases/36239 requests with
exact quiescent request/result counts, native error controls and recovery.
Both request and reply traverse actual GTH using lab time slots/FIFO and
checked CRI backend; no local satellite RTIO/SED, AUX firmware, external
SFP/Kasli or deterministic latency proof. Normal rtio-debug-fixed PL,
debug-services CPU0 and kernel-worker-dma-final CPU1 restored to192.168.2.3.
Two restore suites PASS: normal DMA/TTL, analyzer/MonInj and Ethernet.
Evidence drtio-packets-hardware-2026-10-11.json. SD/flash/OTP/Si unchanged.

Latest2026-10-11 physical AUX PASS: routed drtio-aux-route-2026-10-11,
WNS2.696/WHS0.011ns,153 CDC bits/five Gray buses. Three resets;57 sends,
54 byte-exact checked receives, three deliberate full-ring discards;
ring wrap/overflow/recovery and six1024-byte packets PASS. Diagnostic SRAM
transport only: AUX firmware/protocol/CRC/discovery and remote Kasli remain
NOT_RUN. No physical in-flight reset proof. Normal local core restored to
192.168.2.3 and physical TTL/DMA/debug/Ethernet PASS. Shared Genesys lease
covered129.218-second load/test/restore; no persistent or Si writes.
Use scripts/test_drtio_aux_bringup.py; evidence aux-hardware-2026-10-11.json.

Genesys2026-10-11 AUX Rust firmware lab PASS: unchanged current upstream
packet codec/libio plus CRC linked into A53 firmware,31 request/reply pairs,
bad CRC/unknown type and recovery through physical GTH loopback. Both roles
on one CPU; after self-test firmware idles. Destination DOWN, laboratory
ResetAck only; no production satellite RTIO reset, persistent service,
remote Kasli or TSC/routing proof. Piotr/current seven basic vectors match.
Normal local core restored192.168.2.3 with physical TTL/DMA/debug/Ethernet
PASS. Shared lock held139.957s; no Si/SD/flash/OTP writes. Evidence
artiq-new-wip/evidence/aux-firmware-hardware-2026-10-11.json; reproducer
 diagnostics/drtio/aux_protocol/README.md. Use bounded AUX wrapper --firmware.

Genesys2026-10-11 persistent AUX lab service PASS: echo/status-DOWN responder
stays active after31-pair self-test.18 UART-injected requests,9 responses,
9 ignored loopback replies,3 each CRC/unknown/unsupported-reset drops and
recovery PASS through physical GTH. Persistent ResetRequest remains unsupported
until real RTIO/SED backend exists. UART injector and responder share one A53;
no remote Kasli/TSC/routing proof. Normal core restored192.168.2.3 with physical
TTL/DMA/debug/Ethernet PASS. Shared lease168.681s; no persistent/Si writes.
Evidence aux-service-hardware-2026-10-11.json; bounded AUX wrapper requires
--firmware ELF --service-test. Next work is upstream satellite RTIO/SED wiring.

2026-10-13 KASLI03 BRAM boot PASS: DNA0048458a64b04854, USB topology1-6.2,
three shared Kasli locks, corrected SRAM bit4fb33ce8.../reset0/ROM128KiB.
Bootloader CRC/DDR/memory test/listener PASS; no runtime uploaded, restored
full-checker CSR baseline PASS. First flash-first image qualification withdrawn;
it ran old flash ARTIQ8 and set Si5324 internal125MHz (exact original registers
not restored). Corrected runs did not run it. Separate flash-free runtime compile
PASS, identical generated memory/CSR maps; physical runtime NOT_RUN. Read
 diagnostics/kasli-master/KASLI03.md and newest evidence/status before hardware.

2026-10-13 KASLI03 IPv6 netboot network PASS: operator added enp1s0 address
fe80::c0de:3/64, three TCP4269 connections to fe80::4b:3ff:fe48:4854, unknown/
boot-without-firmware rejection and recovery with MAC confirmation. No firmware
uploaded/executed; diagnostic restored PASS under three shared Kasli locks.
Evidence kasli03-netboot-network-2026-10-13. Next bounded RAM download only;
runtime Si5324/sys-clock switch/reboot behavior not qualified yet.

2026-10-13 KASLI03 netboot RAM download PASS1752788 bytes runtime.bin,
UART completed confirmation, no B/execute/Si setup, restored diagnostic PASS.
No RAM readback checksum claim. See evidence/kasli03-netboot-download-2026-10-13.
Runtime execution still pending clock capture/restoration and sys-switch reboot
handling; download flag is connection-scoped, so later B needs re-download.

2026-10-15 KASLI03 now USB1-2.4.1/001:019, channelC path usb-0:2.4.1:1.2-port0,
DNA0048458a64b04854 verified. Fresh original54 reads/13 retried NACKs vs settled54/
zero; same registers. Volatile soft-reset23-register restore/calibration/PLL and
nominal125MHz ±1% counter check PASS, shared three-Kasli lease149.249s. Expected
reset-value NACK only. No FPGA/flash/runtime/Genesys writes. Evidence
kasli03-clock-restore-2026-10-15. Runtime NOT_RUN and must also lock Genesys due
connected downstream TX. Capture/netboot wrappers accept explicit hub location.

2026-10-15 KASLI03 current ARTIQ10 RAM startup hardware PASS: first upload/B
PLL/sys-switch reboot→BRAM, second upload/B matching runtime management/session
UART active. Runtime TCP client/kernel/remote DRTIO NOT_RUN. Shared Genesys plus
three Kasli locks held through startup and full-checker/clock-profile restoration
PASS. No Genesys config/flash/OTP writes; volatile Si setup/restore explicit.
Evidence kasli03-runtime-startup-2026-10-15. Use --execute-runtime only with
reviewed clock baseline/validation and exact payload hash; current enp2s0.

2026-10-15 KASLI03 standard artiq_coremgmt log and artiq_run counter/RPC hardware
PASS twice. Scoped core fe80::4b:3ff:fe48:4854%enp2s0, rv32ima,1ns machine unit.
Kernel RTIO wait>=1ms, synchronous scalar RPC return asserted; no TTL writes.
Netboot wrapper --counter-experiment requires --management-client and reviewed
runtime/clock inputs. Full-checker and clock baseline restored PASS under
Genesys+three Kasli locks. External DRTIO remains NOT_RUN. Evidence
kasli03-counter-2026-10-15. Next external-link test needs both board leases and
reviewed Genesys diagnostic load/restore, never rely on old USB bus numbers.

2026-10-15 external receive-only LinkObserver RTL simulation PASS20 serial
offsets with arbitrary RT/AUX payload/counts and disabled-count controls.
No HW action. Not integrated in top/routed; no external link claim. Existing
ProtocolProbe's synthetic payload checker must not qualify real Kasli data.
See diagnostics/drtio/EXTERNAL_LINK.md for integration/CDC/reset/lease/restore
requirements. Evidence link-observer-simulation-2026-10-15.json.

2026-10-15 observer top integrated/preflight PASS252 CDC bits/seven Gray buses,
CSR bank3, hard optical TX disable. RX reset/reacquire simulation PASS. Corrected
Vivado build running build-vivado/drtio-observer-route-fixed-2026-10-15; acceptance
PENDING. Do not edit active build_top.sh/check_top_build.py before it finishes.
First drtio-observer-route-2026-10-15 stopped/withdrawn after HDL caught incorrect
CSR defaults; never load it. See latest PORTING_STATUS/EXTERNAL_LINK. No HW access.

2026-10-15 physical KASLI03→Genesys external RX clock/comma observed: four
status255/alignment31 snapshots, RX/PS ratio~1.00002, zero RT/AUX frames.
Optical Genesys TX hard-disabled; no remote DRTIO/CRC/TSC/latency acceptance.
Normal Kasli diagnostic+clock and Genesys192.168.2.3 TTL/DMA/debug restored PASS.
Original final Ethernet FAIL was stale enp1s0; four-board-locked enp2s0 recheck
20/20 ping and1129210 exact TCP bytes PASS. Explicit restore network_interface
now required by external_session.py. Raw failure retained in evidence/
kasli03-external-rx-2026-10-15. No active HW/build sessions. Next: upstream idle
return TX and external AUX echo/status-DOWN (no production ResetAck yet).

2026-10-15 external Kasli↔Genesys AUX echo physical PASS. KASLI03 LINK#0 master
confirms reply after1 packet; Genesys1 echo/71 DOWN replies, zero reported
send/RX/bad-CRC drops,2 unsupported packets. External firmware build flag
--external bypasses lab self-test/UART injection, enables real idle/AUX TX and
never production ResetAck/UP. TSC/routing/remote RTIO still absent. Same four
leases cover startup/service/full normal restoration PASS; Genesys192.168.2.3
TTL/DMA/debug/Ethernet and Kasli diagnostic/clock baseline verified. No active
session. Evidence kasli03-external-aux-2026-10-15; next real satellite backend
clock/reset/CDC/TSC integration. Config mode external-aux-down and qualified
firmware/map hashes required. No flash/SD/OTP/Genesys Si writes.

2026-10-15 SatelliteTransport RTL simulation3 tests/HDL generation PASS: real
RX-clock packet/SED/TTL, actual TSC-load Gray counter and existing whole-packet
RT reply CDC to TX. Busy arrivals drop whole and latch fatal RX-domain fault.
AuxEndpoint.rx_ready exposes existing settled qualifier. No top/routed/HW
integration or TSCAck yet. See SATELLITE_SED.md/newest PORTING_STATUS. Last HW
normal restored state unchanged. Next AuxPS common-reset/top/CSR integration.

2026-10-15 AuxPS satellite integration/raw20/AXI simulations6 methods PASS;
includes two reset epochs of real TSC-load counter, legacy AUX, transport and
Kasli fine3 timestamp compatibility. Optional pad mode uses fine-width3; simple
TTL8ns, wire machine unit1ns. New CSR fields actual load/fatal reply/sticky SED/
spread. Top DRTIO_SATELLITE pins JB1AE13/JB2AG14. Generated209 CDC bits/eight
Gray buses; Vivado build running satellite-fine3-route-2026-10-15 (session96547),
qualification PENDING. Do not edit active build_top.sh/check_top_build.py.
Old satellite-route-2026-10-15 fine0 stopped/withdrawn, never load. No HW actions;
prior normal baseline unchanged. Next inspect build then actual-load-gated
TSCAck firmware; production reset/routing/UP and deterministic latency pending.

2026-10-15 fine3 satellite bitstream BUILD_PASS WNS2.560/WHS0.007,209 CDC bits/
eight Gray buses. Actual TSC-load ACK physical PASS: count0→1, native master
LINK#0 proceeds without TSC timeout;1 echo/119 DOWN/2 unsupported route-rank
packets. Full four-board-locked restoration local TTL/DMA/debug/Ethernet and
Kasli diagnostic/clock PASS; normal Genesys192.168.2.3. No active build/HW.
TSC offset/jitter/deterministic latency still NOT_MEASURED; routing/rank/reset/
remote TTL remain pending. Use external-tsc-down and final aux-tsc-firmware-final-
2026-10-15 ELF/map/policy hash. Non-final build superseded/never loaded. Source
banner still legacy no-RTIO-backend; correct it with next firmware revision;
loaded bit actually contains real backend. Raw evidence preserved/clarified in
kasli03-external-tsc-2026-10-15/acceptance.json. Next SED/PHY reset must preserve
running TSC; never reset entire transport/time just to acknowledge ResetRequest.

2026-10-15 split RTIO/PHY reset RTL11 methods PASS. Match upstream satman:
ResetRequest resets queues/input control, preserves output PHY state/TSC;
separate PHY reset can clear output. Actual applied flags after4 backend edges,
new AuxPS CSR req/applied pairs default asserted cold holds. Firmware must
release holds explicitly; ResetAck remains unsupported. Raw20/AXI two-epoch,
SED buffer124→128, pending input removal, output-state preservation verified.
No HW touched. Build satellite-split-reset-route-2026-10-15 running(session31053),
213 generated CDC bits/eight Gray constraints; qualification pending. Do not
edit active build_top.sh/check_top_build.py. Earlier satellite-reset-route-
2026-10-15 combined lab build stopped/never loaded. Next qualify then bounded
CSR hold/release and physical native ResetRequest proof; no fake transport
recovery (RT reply fault remains fatal). Evidence satellite-split-reset-simulation.


Genesys/KASLI03 external reset2026-10-15: native two core.reset kernels after
link setup PASS, two actual split queue reset completions/two AUX ResetAck,
TSC-load count1 unchanged,zero master reset errors. Routing/rank unsupported,
destination DOWN,remoteTTL pending; no absolute offset/jitter claim. Both boards
restored/validated (Genesys192.168.2.3 local TTL/DMA/debug/Ethernet; Kasli diagnostic
and internal125MHz clock). Evidence kasli03-external-reset-2026-10-15. Combined
wrapper owns Genesys/allKasli leases across entire load/test/restore. No flash/Si
Genesys writes. Next routing/rank state and readiness qualification.


External DRTIO DIO2026-10-15 PASS: real Kasli03 master -> Genesys destination1
rank1 direct leaf -> JB1/JB2 jumper -> timestamps. Two normal kernels,8 pulses/
8 rising edges each,all seven intervals100000mu,ninth read empty. Native UP,
TSC/reset handshake pass; no new master errors. Not absolute phase/jitter or
complete satellite service qualification. Both boards restored/validated,
Genesys192.168.2.3 local TTL/DMA/debug/Ethernet PASS; locks released. Evidence
kasli03-external-dio-final-2026-10-15; source examples/kasli_drtio_dio.py and
DIO_EXPERIMENT.md. Initial NAC3 compile failure kept in separate evidence.


2026-10-16 external DRTIO stability/recovery PASS. Two kernels measured4096
physical edges,4 width/period patterns,256 empty final reads,eight native RTIO
resets. Separate session forced two1s Genesys GTH resets: native master DOWN,
fresh TSC ACK/new UP each time; four post-recovery DIO kernels PASS. Both boards
restored/validated,Genesys192.168.2.3 local TTL/DMA/debug/Ethernet. Locks released.
Evidence external-stability-v2/external-recovery-2026-10-16. No absolute phase/
jitter/cable-removal proof; remote DMA NOT_IMPLEMENTED. Next native DMA+CRI work.
Old JTAG server disappeared; started filtered Genesys-only hw_server container
34e5dd105b4c,172.17.0.3:3121 (do not assume stale172.17.0.2 or touch other thread's
Vivado container). Re-discover metadata before use. Initial connection-refused
FAIL preserved; no board programming occurred in that failed attempt.


SatelliteDMA offline2026-10-16: optional SatelliteBackend dma_membus uses existing
AXI DMA + native CRISwitch;2 tests each Piotr/current upstream PASS,fine3/time
 offset,quiescent handoff,underflow/drain/reuse.7 SED+3 reset regressions PASS.
Standalone HDL emitted; no Vivado/HW/PS CDC or AUX DDMA trace handling. Default
qualified DIO image unchanged. AXI64/16 requires128-byte alignment (satman64
insufficient). Do not wire resettable recovered-clock DMA directly to PS AXI
without drain/isolation; active reset/concurrent commands unqualified. Next
memory/CRI CDC with running-clock isolation/quiescence. See SATELLITE_DMA.md
and evidence/satellite-dma-offline-2026-10-16. No HW accessed in this stage.


DMA memory/CDC offline2026-10-16:9 tests each Piotr/current PASS. DMAMemoryGuard
keeps AXI on sys and drains on abort even with RX simulator clock paused;
DMARawCDC coordinates FIFO resets across sys/rtio_rx. Short-reset phantom16-word
failure fixed by seven RX reset edges + fresh reset/ready handshake. read_reset
must hold future decoder/CRI. No physical timing/Gray constraints/PS target or
DDMA firmware yet. sys cannot reset/stop before guard.done. Queue reset during
trace needs guard.abort. No HW accessed; restored board baselines unchanged.
Next native record decoder/CRIMaster plus completion/error CDC/ownership.
Evidence dma-memory-offline-2026-10-16; SATELLITE_DMA.md updated.
