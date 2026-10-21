# KASLI04 preparation

User selected KASLI04 and confirmed SFP1 for the Genesys connection. Under
the named KASLI04 lock, read-only JTAG matched DNA0x006c440674704854 at
USB1-11.1/001:036. No FPGA load, reset, UART, I2C or flash/Si writes.
Existing secure-link mode10 SRAM remains unchanged. Kasli01/03 not accessed.

An isolated pinned source worktree was prepared using the existing RAM-only
NAC3/DMA result overlays and distinct shared bootloader/runtime MAC. CPU
build started using the existing pinned Nix/Rust environment; completion is
not yet qualified. Build recipe/config and source hash are recorded here.
No hardware wrapper is enabled for KASLI04 yet.

Known unresolved hardware admission: secure-link's latest fixed EEPROM
access on04 NACKed at mux0x70 read, also through FTDI B. Do not bypass that
fault or run ARTIQ clock initialization without a valid per-board snapshot
and physically qualified restoration path. Existing01/03 clock baselines
and full-checker restoration cannot be silently substituted for04's retained
mode10 baseline. Next offline step is CPU build qualification; physical
bring-up requires resolving04 clock-bus access and preserving its baseline.
