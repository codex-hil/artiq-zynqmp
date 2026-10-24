Dedicated FMC reference activity probe
======================================

Offline candidate; do not enable HMC output12 until AC coupling on the actual
AXAU15/ACAU15 revision is established. No hardware validation of this image.
No QPLL or JESD logic is included yet.

V7/V6 -> IBUFDS_GTE4 ODIV2 (/2) -> BUFG_GT -> registered 32-bit Gray counter
-> two TCK synchronizer stages -> USER1 signature0x41585231. USER2 preserves
the qualified clock-setup GPIO v2 SPI transport (0x41534760/0x41534762).
read.tcl only observes clock activity; host scan timing is not a calibrated
frequency measurement. It must be run inside an ALINX-only leased session.
It neither programs the FPGA nor enables HMC outputs.

Build on Dell with build.tcl, exact part xcau15p-ffvb676-2-i and global Vivado
build lease. Register-to-synchronizer max delay and bus skew are bounded by
the nominal 122.88MHz counter period. SPI constraints retain the limitations
of clock-setup: slow host-driven GPIO, asynchronous ownership/MISO inputs.

Electrical prerequisite
----------------------

Shared AD917x schematic drawing02_046765 revisionD, sheet4: HMC output12
BR40_P/N feeds FMC GBTCLK0. The supplied AXAU15 manual maps this to V7/V6,
bank225 MGTREFCLK0. Neither source establishes carrier/module series AC
capacitors for the actual board revision. The manual's AC coupling statement
on page27 concerns PCIe and must not be applied to FMC.

AMD DS931 v1.9, GTH clock input table2, requires external AC coupling
(nominal10nF), differential input250..2000mVpp and nominal100ohm termination:
https://docs.amd.com/r/en-US/ds931-artix-ultrascale-plus/GTH-Transceiver-DC-Input-and-Output-Levels
UG576 also requires AC coupling at MGTREFCLK. GPIO VADJ1.8V does not establish
MGT reference electrical compatibility. Obtain actual carrier/module schematic
and identify both series capacitors before selecting HMC driver mode/enabling.
No unverified HMC output12 writes are provided by this diagnostic.

Current physical baseline is the clock-setup image: DAC ID9172 and PLL/DLL
lock passed, TX muted, digital clock powerdown asserted; only HMC output2
commanded enabled. HMC is write-only over FMC; its register/lock readback is
not available. Nothing in this directory changes that baseline automatically.

Implementation 2026-10-23
-------------------------

Dell job alinx-refclk-probe-20261023b: bitstream PASS, setup6.749ns,
hold0.046ns, bus-skew slack7.201ns, DRC0 errors,32 safe CDC bits and no
unconstrained internal endpoints. Evidence: ../../evidence/axau15/refclk-probe-20261023.
Simulation of this new top and physical reference activity remain NOT_RUN.
Earlier job20261023a had ODIV2 undivided; it is superseded and never programmed.

2026-10-24 physical continuation
--------------------------------

The user explicitly authorized a bounded LVDS trial on the existing assembly.
``../qpll-lvds-lab/`` and ``../../evidence/axau15/qpll-lvds-hardware-20261024/``
record physical dedicated-reference activity/QPLL lock and off/on recovery PASS.
This supersedes the earlier schematic prerequisite as a stop for this lab
bringup. Actual coupling population, common-mode and jitter remain unmeasured.
DAC PLL/DLL preserved with channel12-only writes; do not restart global HMC
dividers after establishing DAC lock. QPLL LOCK remains high during reference
loss; a running-clock watchdog is required. JESD and RF remain NOT_RUN.
