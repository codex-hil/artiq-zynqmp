AXAU15 / AD9172 SPI diagnostic — physical PASS 2026-10-23
======================================================

USER2 host-paced GPIO, single TCK domain; no FPGA system/DAC clock dependency.
Cable Digilent210512180081, part xcau15p IDCODE04AC2093, VADJ1.8V measured by
user. FMC pins from axau15-manual-pinmap.json. CS_HMC is always inactive.
SPI_EN is an input owned by PIC; high asynchronously tri-states all FPGA SPI
outputs. Two-flop synchronized ownership also rejects commands and parks CS.
Unused pins PULLNONE; no TXEN, JESD, clock initialization, or scope commands.

Protocol: 64-bit LSB-first JTAG scan, USER2 IR6-bit value3. Command marker
0x41534750 in high32; low bits0=SCK,1=MOSI,2=CS_DAC. Response marker0x41534752,
low bits0:2 latched pins, bit4 synchronized MISO, bit5 PIC ownership. Bad command
markers have no effect. Every GPIO state lasts a complete scan; TCK<=10MHz,
physical test6MHz. Host explicitly sets up MOSI low, raises SCK, samples MISO,
then completes24 cycles, deasserts CS. No autonomous transfer or retries.

Synthesis/route/bitstream ran on Dell under its shared build lock, final job
/srv/nvme-fast-1/vivado-work/alinx-spi-probe-20261023c. WNS17.108ns,WHS0.037ns,
DRC0 checks, no unconstrained internal endpoints. Input datapath20ns and
output/clamp30ns budgets are tiny compared to host scan dwell. Both async inputs
have two-flop synchronizers. check_timing reports2 partial input delays because
no synchronous hold relationship is assigned to those external inputs. This is
explicitly a slow diagnostic, not production SPI timing signoff. CDC report has
no clock-to-clock crossings; that is not proof that external pins are synchronous.

Testbench: Icarus12.0 on Dell, valid update/bad marker/MISO/ownership/recovery PASS.
XSim attempts failed first on timescale then missing GCC; neither was a passing
simulation. Isolated rootless Icarus package under /srv/nvme-fast-4/toolchains/
iverilog-12 is recorded with package hash in evidence. test_host.tcl runs the
actual read.tcl against an SPI slave model, warm/cold/wrong-ID paths. Model
output includes script PASS tokens but is explicitly SIMULATION_ONLY.

Hardware sequence and results
-----------------------------

Initial cold read was zero; setting SPI_INTFCONFA0x18 enabled four-wire reads:
chip type4/revision2 became readable but product ID remained zero. This failed
attempt is retained, not relabeled as identity PASS. For this exact guarded
state, read.tcl now follows AD9172 datasheet Rev C Table49 up to boot loading:
0x000=0x81,0x000=0x3c,0x091=0,0x206=1,0x705=1, bounded wait. This reads factory
nonvolatile trim into working state; it does NOT program NVM/OTP/eFUSE.
No0x090 DAC-power, RF-enable, NCO, HMC or JESD configuration is issued.
Source: https://www.analog.com/media/en/technical-documentation/data-sheets/ad9172.pdf

Physical result: register4=0x72,5=0x91,chip3=4,revision6=2. Register0x705=2
(bit0 cleared; do not interpret reserved bit1 as a portable success flag).
Scratch0x00a original0x05;0xA5/0x5A readback PASS; restored0x05 and verified.
Clock diagnostics0x0c3=0,0x7b5=2,0x281=0: no PLL/DLL lock qualification.
Full evidence under ../../evidence/axau15/spi-probe-20261023.

Host wrapper requires exact bit SHA and cable/part checks, holds
/home/codex-hil/.cache/alinx-210512180081.lock, exposes only this USB device to
its temporary server and stops the server on exit. run_hardware.py BIT
--sha256 HASH --output NEW_ABSOLUTE_DIRECTORY programs SRAM and executes the
bounded test. --reuse-image skips programming and requires existing probe
signature; it does not verify full in-device bitstream contents. All paths must
be under /srv/codex-hil-data for the container. Never use this wrapper on Trenz.

Final state: volatile SPI probe running, CS idle, HMC untouched, DAC initialized
through factory loader in4-wire mode, scratch restored. Trenz and MSO4104 were
not accessed. CH3/CH4 RF remain unmeasured; CH1/CH2 protected. No flash/EEPROM/
OTP/eFUSE writes. Next: qualify HMC reference routing/driver mode, cold clock
configuration and DAC PLL before JESD. Do not reuse AD9173 warm profile blindly.
