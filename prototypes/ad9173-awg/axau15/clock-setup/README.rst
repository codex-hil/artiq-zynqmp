AD9172 onboard clock setup — physical PLL/DLL PASS 2026-10-23
==========================================================

This separate diagnostic adds HMC chip select to the qualified JTAG-paced SPI
bridge. Command/response markers are0x41534760/0x41534762; low bits0=SCK,
1=MOSI,2=CS_DAC,3=CS_HMC. Idle=12. Hardware rejects simultaneous active chip
selects and tri-states SPI when PIC owns SPI_EN. No FPGA GT or FMC reference
receiver is instantiated. No NCO, RF enable, JESD or oscilloscope access.

Clock plan and limits
---------------------

Local schematic reference/dac.pdf (AD9172_FMC_EBZ drawing02_046765 RevD,
sheet4) routes HMC output2 to onboard DAC clock through the filter/coupling
network. It routes output12 separately to BR40/FMC GBTCLK0. This stage writes
all14 output controls disabled and enables only output2. Output12/13 and SYSREF
remain commanded off. User's exact DAC PCB revision/population is not yet
independently documented; DAC PLL lock provides evidence of the onboard path,
not proof of the unused FMC reference path.

HMC writes reuse the volatile onboard-only profile from the preserved
/home/codex-hil/trenz-bringup/usb-clock-bringup.py, not its Trenz/USB session:
PLL1 disabled/free-running122.88MHz VCXO, PLL2 nominal2949.12MHz, output2/12
nominal245.76MHz, CML driver setting3. FMC HMC transport is write-only: there
is NO HMC identity, register readback or direct PLL2 lock claim. AD9172 lock is
indirect evidence of a working reference, not calibrated frequency/jitter proof.

AD9172 datasheet RevC Tables50/51 qualify the DAC sequence:
https://www.analog.com/media/en/technical-documentation/data-sheets/ad9172.pdf
The selected DAC PLL N=5,M=1 and VCO output/2 correspond to nominal4.9152GS/s
for245.76MHz reference. Three consecutive status reads are required per lock,
with bounded polling. DLL search mode0x68/0x69 applies above4.5GHz. Digital
clock powerdown0x100=1 and TX enable0x3f=0 remain; this is not JESD initialization.

Physical evidence
-----------------

Same isolated cable210512180081, xcau15p IDCODE04AC2093 and existing ALINX
lease. New volatile bit SHA256:
6889865bf8145f25b2718dfd23bcc53c9d28a620a1b2bb50a96af73cc9bf4fe1.
PLL0x7b5=3 and DLL0xc3=1 each passed three consecutive reads, then passed again
in a separate verification session. ID remains0x9172. Register0x799=5,
0x793=0x18,0x094=0x11,0x3f=0,0x100=1.

Initial script marked the run FAIL after both locks because it compared the
entire0x094 byte to1. Actual bit4 is in the datasheet-reserved field. Corrected
verification compares only documented divider bits[1:0] to1 and preserves the
full raw readback. The initial failure is retained. Model now includes this
reserved bit and still checks the divider. No HMC/DAC reconfiguration was
needed for the second session; it only checked identity, mute and lock/dividers
(and rewrote TX disable0). No assumption about reserved bit4 meaning is made.

Validation and reproduction
---------------------------

RTL Icarus test: marker, GPIO/MISO, ownership recovery, dual-CS rejection and
HMC selection PASS. Host Tcl model: exact output2-only profile, wrong-ID/no
writes, and failed-lock/muted abort PASS. These are simulation evidence only.
Vivado2025.2 on Dell, job alinx-clock-setup-20261023a, routed/bitstream PASS,
WNS17.241ns,WHS0.037ns,DRC0 checks,no unconstrained internal endpoints.
Two partial input-delay warnings are the inherited asynchronous external-input
max-datapath budgets, not production synchronous SPI timing signoff.

Build core.v/top.v with build.tcl in a fresh Dell job under the shared lock.
Run run_hardware.py BIT --sha256 HASH --output NEW_ABSOLUTE_DIRECTORY on
Optiplex; --reuse-image skips programming and requires the versioned probe
signature. --verify-only requires --reuse-image and skips clock configuration.
Files/output must be under /srv/codex-hil-data for the isolated container.
transport.tcl is copied into the session directory. The wrapper validates FPGA
identity, holds /home/codex-hil/.cache/alinx-210512180081.lock, exposes only its
USB node, records logs and stops its own server. It does not restore the prior
clock profile on failure; it attempts TX mute and CS idle and records failure.

Final state: dual-SPI diagnostic running in SRAM, clocks configured and DAC
muted; no nonvolatile writes. Trenz and MSO4104 untouched. Next milestone is
qualified dedicated FMC MGTREFCLK routing/electrical levels and JESD bringup,
not yet RF. No external synchronization, jitter or deterministic-phase claim.
