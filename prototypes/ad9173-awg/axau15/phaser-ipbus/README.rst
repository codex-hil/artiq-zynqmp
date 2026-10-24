AXAU15 Phaser generator over IPbus
=================================

This target combines ARTIQ Phaser MultiToneDDS with the qualified AXAU15
AD9172 dual-link JESD transport and CERN IPbus 2.0 over 1Gb RGMII Ethernet.
It produces two complex samples per JESD clock, 307.2 MS/s per channel,
with five independently programmable oscillators on each of two outputs.
There is no DRTIO, Fastlink, MIQRO sequencer or timestamped RTIO interface.
Ethernet controls parameters; samples are generated locally in FPGA.

The DAC runs at 4.9152 GS/s. Four GTH lanes run at 6.144 Gb/s using the
existing dedicated 245.76 MHz MGTREFCLK and QPLL1 configuration. The normal
RF example uses DAC main NCOs at 150 MHz and FPGA offsets -1/+1 MHz.
The generator FTW rate is 307.2 MHz, not the original Phaser 250 MHz.

Baseline CW status and evidence
-------------------------------

2026-10-24: simulation, implementation and physical Ethernet/RF tests PASS.
Evidence: ``../../evidence/axau15/phaser-ipbus-20261024/acceptance.json``.

* Simulation: three DDS/register tests, two asynchronous FIFO tests, and
  localhost UDP loss/reordering test PASS. The RF analysis phase estimator
  was separately checked using synthetic data before physical measurements.
* Vivado2025.2: WNS+0.157ns, WHS+0.012ns, no critical CDC or DRC errors;
  five6ns bus-skew constraints PASS (maximum actual1.793ns). Final RX clock
  phase was changed to-90deg in the routed checkpoint and all reports rerun
  before bitgen. Current HDL and implementation Tcl contain the same phase.
* Hardware: both JESD links clean throughout; PHY937c:4032 at MDIO address1,
  gigabit negotiation/link active. Native IPbus200 writes, error responses,
  twenty parameter commits PASS without read retries. Official uHAL256
  ordered writes and256x21 pipelined read words PASS. RX error counter zero.
* MSO4104 CH3/4: full/half/zero/recovery,149/151->149.5/150.5MHz tuning,
  independent channel amplitude, five simultaneous145/147/149/151/153MHz
  tones on each channel, and90deg phase change of one tone PASS. Phase
  comparison uses second differences across tones to remove acquisition
  time/common LO phase; this is not absolute synchronized phase accuracy.
* Final nominal149/151MHz: measured148.996364/150.996701MHz,
  0.47565/0.48280Vpp. Free-running clock offset is not calibrated.

Running SRAM image SHA256::

  5018618518cab3bab43e02a8c1a81691434db69754ef31abb09686d57b8bfb3f

Local bitstream: ``/srv/codex-hil-data/artiq-zynqmp/artifacts/alinx-phaser-20261024g/phaser_ipbus.bit``.
Raw captures: ``/srv/codex-hil-data/artiq-zynqmp/artifacts/alinx-phaser-rf-20261024c``.
A separate normal warm-start test also passed, followed by RF measurements;
see ``normal-start.json`` in the evidence directory.

Final state: one tone per channel, FPGA offsets-1/+1MHz, ASF32767,
main DAC NCO150MHz on both. Scope settings restored/read back.


Local envelope extension
------------------------

Current sources also provide a finite complex envelope sequencer over IPbus
(ABI0x00010001):256 entries, independent I/Q gains on both channels,
6.5104ns nominal steps, finite repeats and abort. See ``ENVELOPE.rst`` for
its register map, CLI, validation and shared-board restoration procedure.
The baseline CW evidence above belongs to ABI0x00010000, which remains the
shared default image. The envelope client rejects older images explicitly. The extension has
separate simulation, Vivado and physical RF PASS evidence in
``../../evidence/axau15/envelope-20261024/acceptance.json``. Its qualification
runner restores the shared CW image after every bounded session.

Interface
---------

Static IP 192.168.2.241, MAC 02:00:00:00:a1:15, UDP 50001.
This is a native CERN IPbus endpoint, compatible with official uHAL.
``addresses.xml`` describes the word-addressed register map::

  000 identity=41585048  001 ABI=00010000  002 sample rate  003 tone count
  004 scratch RW       005 accepted write count          006/007 uptime
  010 JESD status      011 commit busy   012 acknowledged commit count
  013 mute RW          014 commit (write 1)
  018 RX frames        019 TX frames     01a RX error bytes
  100..114 shadow words RW              200..214 held image RO

Each channel has five pairs of words: 32-bit frequency tuning word, then
signed 16-bit amplitude in the high half and 16-bit phase turns in the low
half. Word20 contains channel enables in bits0/1 and optional phase reset
in bit8. Other bits are rejected. Commit copies all shadow words into an
immutable held bank and toggles a request to the JESD clock domain. The
receiver blanks the outputs while the DDS pipeline settles, then returns
an acknowledgement. Writes to the shadow bank and further commits are
rejected while busy. Held readback shows the last requested image;
acknowledgement confirms its application. This is not timed RTIO playback.

The DDS sums with saturation. Keep the sum of tone amplitudes below full
scale when clipping is unwanted. Phase is expressed in turns, amplitude
in signed full-scale units. Both outputs start muted. A rephase commit
resets oscillator phase accumulators; a non-rephase commit preserves
accumulator phase but still blanks during parameter settling.

``client.Phaser.configure`` accepts two lists of up to five
``(frequency_hz, amplitude, phase_turns)`` tuples. The CLI acquires the
ALINX lease; applications using the class must hold the same lease for
all network and hardware operations. Example::

  python3 client.py --config example-tones.json
  python3 client.py --mute

These commands require an already initialized DAC/JESD target.
Writes are never automatically
retried after an uncertain response. Read retries are bounded.

Build and hardware
------------------

Use ``env.py`` pinned local source locations and the open-miqro Python
venv. ``prepare.py /absolute/fresh/staging`` emits complete Vivado inputs
and their hashes. Transfer explicitly to a fresh Dell job directory and
run ``build.tcl`` through the shared Vivado launcher/build lock described
in ``docs/vivado-remote-handoff.md``. Do not build this target on Optiplex.

``run_hardware.py`` programs only SRAM through cable210512180081, checks
DAC/JESD and reads PHY MDIO. With ``--start`` it also configures both
DAC main NCOs at150MHz, commits the default FPGA tones over IPbus and enables
RF. No scope is required for normal warm startup::

  python3 run_hardware.py /absolute/path/phaser_ipbus.bit \
    --sha256 5018618518cab3bab43e02a8c1a81691434db69754ef31abb09686d57b8bfb3f \
    --output /absolute/fresh/run-directory --start

Then ``python3 client.py --config example-tones.json`` changes the generator.
The provided example uses amplitude0.5; startup uses32767/32768. Without
``--start``, the runner is diagnostic only and leaves the DAC muted; the DDS starts
muted on programming and retains its state with ``--reuse-image``.

``run_rf.py`` additionally checks native IPbus,
official uHAL and scope CH3/4 RF. Both require a bitstream SHA256 and a new
absolute output directory. ``--reuse-image`` avoids programming but still
checks the image signature. The RF runner requires ``--uhal`` pointing to
the binary produced by ``build_uhal.sh``. Scope acquisition, trigger,
horizontal configuration and CH1/2 are preserved; CH3/4 display and DATA
transfer settings are restored. Both hardware scripts acquire the ALINX
lease; RF also acquires the shared scope lease. Failure attempts to mute
both FPGA and DAC. Restore the known payload image if qualification fails.

The existing HMC/DAC clock configuration must already be running. Startup
applies the qualified output12 LVDS profile and DAC mode3 setup; it
is not a cold-start power-management implementation. No flash, EEPROM,
OTP or eFUSE writes are used. Do not use Trenz hardware scripts here.

Ethernet and clock-domain assumptions
------------------------------------

JL2121-N040I PHY, MDIO address1, bank64 at1.8V. Pins and strap evidence are
in ``network.json`` (AXAU15 manual V1.0). PHY straps enable2ns TX and RX
clock delays; FPGA adds no data delay; an RX MMCM with -90deg (2ns) phase advance compensates clock insertion.
Both Ethernet MMCMs use integer dividers. Only1Gb/s is supported. The static
IP must be unique on the LAN. This is a laboratory network endpoint
without authentication.

The RGMII constraints budget nominal2ns skew with0.6ns RX variation and
1ns TX setup/hold plus0.2ns board margin. RX input delays describe the next data transition1.4..2.6ns after each
clock edge of the4ns DDR unit interval. These are engineering budgets,
not a measurement of the assembled PCB. Timing closure and working traffic
do not establish PVT margin. CDC constraints target synchronizer endpoints,
held configuration buses and Gray FIFO pointers; no blanket asynchronous
clock groups are used. MAC CDC memories use registered read data and BRAM;
FIFO pointer ownership prevents read/write address collision.

Sources
-------

* Phaser MultiToneDDS: ARTIQ7d7b85f377e0c172ae3496f0c03cfb6cb85ba022,
  vendored with its license; only the register-access constant import adapted.
* MiSoC d84551418042cea0891ea743442e20684b51e77a DDS primitives.
* LiteEth cb101652f69fab0979cfa1f9afbcfdf185fe662e MAC and TX primitives;
  local RX wrapper follows the UltraScale PHY implementation.
* CERN IPbus firmware v1.16,3eb6129c5546b20976a4722c8e0ad270821667d0,
  reused with qualified PM12 wrapper/inference patches from FIT_testing_sw
  9e2855ec7c9f1d7fc40e7539a1627eaa4dab11ce. Vendored provenance and license
  are in ``vendor``. No PM12 hardware scripts are run.
