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
