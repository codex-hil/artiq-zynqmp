# KASLI04 volatile clock and retained SRAM restoration

Physical PASS under named04 lease for85.061s. Verified exact DNA and idle
mode10, loaded hash-pinned full-checker diagnostic, verified diagnostic
identity and disabled EEM/GTP/SFP outputs. Fresh28-register double-read
equaled recorded04 baseline before any Si configuration write. Only clock
mux71 addressed; absent EEMmux70 never accessed.

Reused bounded clock_restore exercise: softreset, exact23-register restore,
fresh ICAL, profile readback, product identity, PLLlock and three independent
host-referenced frequency samples PASS. Approximately124.950/125.010/125.014MHz
within existing1percent diagnostic tolerance; not jitter/phase qualification.
No retries;26.604s clock exercise. Mux71 and diagnostic bus CSR restored.
Exact retained mode10 bitstream reloaded and UART version/mode/idle checked.
Mode10 volatile counters naturally restart; prior one-shot I2C request history
is not replayed. No flash/OTP/SD, Genesys or other Kasli access. Lease released.

Reproducer: `scripts/test_kasli04_clock_restore_hw.py` defaults to offline
preflight; --run opts into bounded04-only SRAM/volatile-clock exercise. Both
images and the original per-board clock snapshot/plan are pinned before HW.
This establishes the restore building block, not master runtime or DRTIO.
Next complete master FPGA qualification and integrate this04 restoration path
into the guarded netboot/runtime wrapper, preserving both-device leases.
