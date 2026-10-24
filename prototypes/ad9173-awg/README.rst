AD9173 AWG: Trenz hardware reference and AXAU15 parallel port
==========================================================

Budget AWG satellite for ARTIQ/Kasli. This export is an implementation starting
point, not completed AXAU15 support. The ALINX has no hard A53 cores. Kernels
initially execute on Kasli; a softcore may run satellite management firmware.
Local subkernels, PCIe processing and DSP performance need separate decisions.

Read ``HANDOFF_ALINX.txt`` for the complete task for a new thread.

Contents
--------

* ``gateware/``: working Trenz reference HDL generators, SPI console and seven
  simulations. The board-specific ``generate-fabric.py`` and Tcl use Trenz IOs
  and a laboratory fabric reference clock. They are NOT an AXAU15 target.
* ``boards/axau15-manual-pinmap.json``: candidate ALINX wiring derived from the
  user's 44-page manual, with provenance and SHA-256. No vendor PDF redistributed.
* ``reference/trenz_lab/``: historical host scripts, explicitly Trenz-only.
  They contain a fixed Trenz cable identity, local tool paths and shared leases.
  They are archived as reference, not portable programming commands.
* ``evidence/``: real Trenz scope/JESD evidence and an earlier startup failure.
  AXAU15 identification, SPI and DAC clock evidence is under evidence/axau15/.
* ``dependencies.json``: exact clean dependency revisions used for the export.
* ``docs/vivado-remote-handoff.md``: build server and shared build lease.

Demonstrated on Trenz
--------------------

TE0803-02-04EV-1EA / TEBF0808-04 plus AD9173-FMC-EBZ RevC:

* Four GTHE4 TX at 6.144 Gb/s; two JESD204B links, mode3, subclass0, HD1.
* Per link L=2, M=2, N=NP=16, F=2, S=1, K=32; scrambling enabled.
* DAC Fs=4.9152 GS/s, main interpolation8, channel interpolation2, complex
  input307.2 MS/s per RF output; two samples/clock at153.6 MHz.
* FMC SPI read/write to DAC, write-only to HMC, FMC USB disconnected.
* FPGA constant I / Q=0 through JESD; main DAC NCO upconversion. Internal DC
  injection disabled. High/half/zero/recovery, asymmetric word and fullscale
  amplitude tests passed on both outputs, with settled link checks.
* Latest configuration left on the Trenz: DAC0/CH2=149 MHz (0.463 Vpp),
  DAC1/CH1=151 MHz (0.474 Vpp), I=0x7FFF, Q=0.

Missing-payload root cause: FabricTX drove core.sink while the DualLink wrapper
subsequently overwrote it with undriven converter ports. Drive the wrapper's
converter_inputs through drive_payload instead. The regression test verifies
both transport inputs and rejects the former parent/core connection.

Limits: an earlier payload-fixed build failed link startup; a later diagnostic
build and live validation passed. Restart repeatability remains unqualified.
The GTGREFCLK fabric clock path is experimental. Raw PHY PRBS and the constant
sample receiver comparator did not qualify their negative controls. No BER,
jitter, deterministic RF phase or production-clock claim. Variable FPGA I/Q
waveform generation and ARTIQ integration remain to be implemented.

AXAU15 scope
------------

The supplied manual identifies XCAU15P-2FFVB676I,12 GTH,8 routed to FMC
(bank225/226) and4 routed to PCIe. FMC GPIO1.8 V and dedicated GBTCLK0/1
references are documented. The J33/J34 headers are3.3 V IO in banks84..86;
LVDS/SERDES support there must not be assumed from P/N signal names.

No native SFP is listed. The user owns a PCIe-to-SFP adapter, but its model and
schematic are not yet available. A passive lane breakout may enable raw DRTIO;
a PCIe Ethernet NIC is not interchangeable. Trace coupling, direction, SFP
controls and legal reference-clock routing before assigning a DRTIO PHY.
Do not claim that FMC spare lanes can reach that adapter without wiring.

Offline checks
--------------

Use the existing host venv for the export on this machine::

    make -C prototypes/ad9173-awg test \
      PYTHON=/home/codex-hil/trenz-bringup/jesd-venv/bin/python

For a fresh environment use ``requirements-gateware.txt`` (pinned Git sources;
pytest is a test dependency). ``make hdl`` generates the Trenz reference only.
``make build-trenz-reference`` builds it, but never programs hardware.

For Dell builds generate HDL on the lab host first, then::

    make -C prototypes/ad9173-awg hdl PYTHON=/path/to/python
    python3 prototypes/ad9173-awg/tools/package-build-inputs.py --output /path/to/new-job

The package contains generated Verilog, all referenced .init files, portable
reference Tcl, constraints and input SHA-256. Transfer to a NEW Dell directory,
never into a running job. The packaged build.tcl is Trenz-only. A new AXAU15
Tcl/XDC/clock target must be implemented before any ALINX programming.
Use the global Dell flock from the remote handoff. JTAG and measurements stay
on the lab host with board-specific leases; do not change a running Trenz.

AXAU15 offline continuation (2026-10-21)
--------------------------------------

``axau15/`` now contains a separate dedicated-reference candidate, SPI-only
variant, pin constraints, synthesis/package scripts and offline tests.
``control/ad9173_profile.py`` separates warm-clock DAC/HMC operations from the
Trenz session. See ``axau15/README.rst`` for exact limitations and reproduction.
As of 2026-10-22, Dell Artix UltraScale+ support, exact-part licensing and
SPI/JESD synthesis pass. Implementation and physical AXAU15 validation remain
pending. This is not a programming-ready port.

Phaser A/B comparison inventory (2026-10-23)
------------------------------------------

``comparison/feasibility.md`` records the new milestone order: inventory,
minimal DRTIO satellite, local Phaser-compatible DDS, JESD integration, measured
A/B comparison. The user confirmed using existing AD9173 RevC hardware.
M0 is partial and M1 blocked on physical SFP/clock/board identification;
no stock Phaser, Kasli or ALINX hardware access is claimed. Source/license and
golden Trenz artifact hashes, interface semantics and measurement prerequisites
are recorded under ``comparison/``. Do not attach the DDS/JESD path before M1
passes. This milestone ordering supersedes the older JESD-before-DRTIO plan in
``HANDOFF_ALINX.txt`` for the comparison task.

Target correction (2026-10-23)
-----------------------------

The user subsequently confirmed that the NEW DAC devkit is AD9172. The AD9173
material above remains the preserved Trenz reference. Immediate scope is basic
devkit bringup; the DRTIO-first comparison sequence is deferred. Do not use the
AD9173 identity guard or claim its warm-clock profile qualifies AD9172. Physical
revision, attachment, identity and clock configuration of the new kit are pending.

AXAU15 / AD9172 physical progress (2026-10-23)
--------------------------------------------

JTAG xcau15p identification, system-clock activity, AD9172 SPI identity and
scratch restoration, and DAC PLL/DLL lock have physical PASS evidence under
``evidence/axau15/``. Exact-part implementation/bitstreams passed on Dell.
The DAC is muted; JESD, sample transport and RF output remain NOT_RUN.
``axau15/refclk-probe/`` prepares dedicated FMC clock activity diagnostics;
actual AXAU15/ACAU15 GBTCLK0 AC coupling remains an electrical prerequisite.
These results supersede earlier no-hardware statements, not the Trenz results.

AXAU15 / AD9172 JESD physical milestone (2026-10-24)
-------------------------------------------------

Dedicated HMC LVDS -> FMC MGTREFCLK, QPLL1, four GTH at nominal6.144Gb/s and
both JESD204B mode3 subclass0 links now have physical startup PASS. Three
consecutive DAC status sets per link confirm CGS/frame/ILAS/checksum with
no selected lane error flags. FPGA sends fixed zeros; DAC SPI TXEN remains
low. RF tones and full/half/zero/recovery payload proof remain NOT_RUN.
See ``axau15/jesd-probe/`` and ``evidence/axau15/jesd-20261024/``.
