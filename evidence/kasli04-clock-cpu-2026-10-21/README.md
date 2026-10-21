# KASLI04 current clock read and corrected CPU qualification

Physical clock read PASS under named04 lease after fresh DNA and idle mode10
UART snapshot. Reused existing FTDI B open-drain bus in the kasli-diot-bringup
venv (pyftdi0.57.2); reset pin remains input. Only mux0x71 routing and Si5324
register pointers changed. No access to physically absent EEM mux0x70.

All28 clock registers read twice exactly, identity0x0182, PLL status locked.
Mux71 restored/read back to saved0, FTDI released, retained mode10 unchanged.
No Si configuration data, FPGA/reset/flash/OTP/SD writes, no other boards.
The snapshot is NOT a soft-reset/restoration qualification.

Corrected CPU build and reset-zero embedded ROM qualification PASS. Bootloader
112296 bytes fits131072-byte ROM; mem.init byte-equivalent to bootloader.
Firmware hashes recorded in cpu-qualification.json. Full Vivado build started
with included recipe; not yet qualified. Next finish FPGA qualification and
prepare04-only clock restore using this baseline, missing0x70 and retained
mode10 restoration. No runtime execution before restoration path qualified.
