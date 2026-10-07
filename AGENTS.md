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
