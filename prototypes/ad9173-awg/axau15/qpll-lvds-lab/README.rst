Bounded LVDS reference experiment
================================

2026-10-24 user explicitly authorized trying HMC LVDS with the existing
AD9172-FMC/AXAU15 assembly, noting operation on another UltraScale carrier.
This supersedes the earlier schematic-only stop for this laboratory trial.
It does not establish measured common-mode, termination current or jitter.
No assumption that the prior Trenz fabric-reference path equals this GTH path.

Uses qpll-probe bit SHA256
3b11544a0ae242cf7e9fbce19ddf9d8d05325ec870620a91875831cf51558ab7.
The runner owns the ALINX210512180081 lease, exposes only its USB node to its
own temporary hw_server, checks xcau15p/04ac2093, and uses SRAM programming.
No flash/EEPROM/OTP/eFUSE writes. No scope, Trenz, Genesys, Kasli or SDWire access.

Prerequisite: clock-setup baseline, AD9172 identity, TX muted, digital clock
powerdown, DAC PLL/DLL locked. Only HMC output12 registers0x140..0x148 are
changed. Divider12 from nominal2949.12MHz gives nominal245.76MHz; output
mode0x148=0x10 selects LVDS. Do not label output current as measured4mA.
Readback of HMC is unavailable; all HMC writes are marked UNVERIFIED.

Sequence: reference off -> three stopped captures -> LVDS on -> three
advancing captures with QPLL lock -> off/stopped -> on/recovered -> final
off/stopped -> verify DAC mute and PLL/DLL. Cleanup disables output12 and
mutes DAC. Counter activity is not a calibrated frequency measurement.
QPLL LOCK can remain high during reference loss: use activity detection too.

Initial attempt used global HMC divider restart/reseed. Reference/QPLL activity
and recovery passed, but final DAC PLL lock failed. Baseline was restored
with clock-setup and confirmed PLL/DLL PASS. Final script removes global
writes entirely. Keep failed evidence; do not report initial whole test PASS.

Run on Optiplex with the exact bit and a new absolute evidence directory::

    python3 run_hardware.py /path/to/qpll_probe.bit --sha256 HASH --output /new/directory

Final FPGA remains the QPLL diagnostic; HMC output12 is commanded disabled,
DAC TX muted and digital powerdown preserved. JESD and RF remain NOT_RUN.
