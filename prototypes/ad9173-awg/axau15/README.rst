AXAU15 candidate target — offline handoff, 2026-10-21
=================================================

Status: HDL_GENERATED, SIMULATION_PASS, VIVADO_DEVICE_SUPPORT_MISSING.
No ALINX, Trenz, Genesys, Kasli or SDWire hardware operations were performed.
This is an incomplete port, not a programming-ready image.

Tool/device gate
----------------

Dell Vivado 2025.2 returns an empty ``get_parts -quiet *xcau15p*`` result.
See ``../evidence/axau15/part-enumeration.txt``. Artix UltraScale+ support
is absent. The exact-part synthesis/license probe was withdrawn from the
shared build-lock queue after this result; no other job was interrupted.
License availability is UNKNOWN, not a confirmed license failure.

The expected spelling ``xcau15p-ffvb676-2-i`` remains a candidate until
``get_parts`` and package/speed/temperature properties validate it.
``check-part.tcl`` provides the exact-part enumeration/synthesis probe after
installation. Existing payload directories contain dangling links to an absent
installer cache. No usable local/Dell family package was found. Restore access
to the official installer source before adding Artix UltraScale+ on Dell;
do not modify an installation while other builds are using it.

Pin and clock review
--------------------

The local 44-page manual SHA-256 matches the recorded pinmap. Pages 29–34
confirm the supplied FMC GPIO, eight GT lanes, bank225 DP0–3, bank226 DP4–7,
GBTCLK0 V7/V6 and GBTCLK1 P7/P6. The 200 MHz input is T24/U24. GPIO is 1.8 V.
This checks the document; physical module/carrier revisions remain unconfirmed.
Vivado package-pin/function cross-check is blocked by missing device data.

A locally available AD917x schematic at
``/home/codex-hil/trenz-bringup/reference/dac.pdf`` has drawing revision D
(despite the online download filename mentioning RevC). Its sheets 4/8 show:

* HMC CLKOUT12 -> BR40_P/N -> FMC GBTCLK0 D4/D5 -> AXAU15 V7/V6.
* HMC output13 -> SYSREF2 -> FMC LA00, the Trenz laboratory reference path.
* GBTCLK1 takes BR40_EXT, branching from the DAC-clock route through components
  marked DNI; do not assume this alternative is physically populated.

The user's board is RevC. Component population, coupling, signal levels and
clock output driver/common-mode compatibility with GTE4 are NOT verified.
The dedicated-reference candidate uses GBTCLK0, not GTGREFCLK. The incremental
HMC helper requires explicit output, verified routing and driver configuration;
it does not silently reuse the Trenz fabric-LVDS driver setting.
No vendor PDF was copied into this repository.

Candidate HDL
-------------

``generate.py`` generates a SPI-only target or four-lane JESD candidate.
System clock is the board's 200 MHz input divided by BUFGCE_DIV to 100 MHz;
EOS reset deassertion is synchronized. SPI thus runs independently of the FMC
clock. The FMC selector SPI_EN remains an input, with the original console's
ownership checks. The shared console now has a payload-reset parameter;
Trenz's default stays 0x2000, AXAU15 selects zero.

The JESD candidate uses IBUFDS_GTE4 and one quad PLL: reference245.76MHz,
QPLL1 N100/M2/D2, VCO12.288GHz, lane6.144Gb/s and user clock153.6MHz.
This is a mathematical/dependency calculation, not a routed PLL qualification.
Four TX ports map to FMC DP0–3 / DAC physical lanes7–4. Two links reuse the
verified HD/checksum fix and wrapper converter-input wiring.

Full 16-bit constant signed I is transferred coherently through BusSynchronizer;
Q=0. Both samples in a cycle are identical. Native TXPRBSSEL is tied to zero:
bit15 never changes operating mode. There is no variable-I/Q DDS, timestamped
parameter interface, RTIO PHY or DRTIO integration in this target yet.

The inherited USER2 console is a bringup transport. Complete request/response
mailbox CDC constraints, timing of SPI IO and independent clock diagnostics
still need review and implementation. The current candidate does not expose
FPGA QPLL/clock counters over USER1. DAC PLL/DLL/SERDES status is available
through the portable SPI profile API. HMC readback/identity over FMC is not
assumed: the reference path supports HMC writes only.

``build.tcl`` deliberately stops at synthesis/reports/checkpoint. It has no
bitstream or hardware-manager command. Full implementation must follow exact
part/pin validation and completion of CDC/IO timing constraints; do not bypass
DRC or add blanket false paths just to produce a bitstream.

Portable profile
----------------

``../control/ad9173_profile.py`` contains only a transport protocol and volatile
register operations: AD9173 identity checks, PLL/DLL diagnostics, mode3/QBD/
SERDES setup, link status, streamed-DSP preparation and 149/151MHz NCO words.
It imports no Trenz host session, cable selector or programming routine.
Identity and initial clock prerequisites are checked before configuration
writes. NCO programming verifies load/readback and restores the page selector;
on failure the caller must keep samples muted, since frequency writes may be
partial. It does not implement a board-session rollback policy.

This is a WARM-CLOCK profile, not a complete cold-start sequence. HMC PLL and
DAC PLL initialization remain to be extracted/qualified for the actual board.
``prepare_fpga_dsp`` disables internal DC injection and leaves RF digitally
muted. Setting tones never enables RF. Mock tests establish software sequencing
only; they are not measurements or validation of physical register behavior.

Reproduce offline work
----------------------

From ``prototypes/ad9173-awg``::

    make hdl-axau15 test-axau15 PYTHON=/home/codex-hil/trenz-bringup/jesd-venv/bin/python
    python3 axau15/package.py build/axau15-spi /path/to/new-spi-job
    python3 axau15/package.py build/axau15-jesd /path/to/new-jesd-job

Packages include Verilog, initialization files, SPI RTL, target metadata,
constraints, synthesis Tcl, Git state and input SHA-256. Transfer only to fresh
Dell directories and use the global build lock documented in the remote handoff.
Do not run ``make build-trenz-reference`` as an AXAU15 build.

Physical acceptance still pending
---------------------------------

1. Identify exact AXAU15 cable, FPGA and board revisions; establish its own
   shared lease. No guessed serial or borrowed Trenz/Genesys/Kasli lease.
2. Verify RevC clock population/levels, 1.8V FMC supply and SPI ownership.
   Confirm exact device/primitive and IO legality in Vivado, then complete
   timing/CDC, route, review DRC and hash the new image before SRAM programming.
3. SPI-only image: verify DAC IDs73/91, prove read/write/readback on a documented
   volatile register and restore it. HMC identity requires a qualified readable
   transport; write-only FMC does not prove identity. Extract cold clock init.
4. Measure/reference-count the dedicated clock, confirm expected QPLL and all
   TX reset-done states. FPGA instrumentation is still to be added.
5. Enable dual mode3 links and record independent CGS/ILAS/data and errors on
   both links across retraining; no RF claim from status bits alone.
6. Disable internal DC injection. Measure both RF outputs for I=0x7fff,
   0x4000, zero, asymmetric0x1234 and recovery. Require half/full scaling,
   zero suppression and recovery, while recording settled link status.
7. Load DAC0=149MHz/DAC1=151MHz and verify actual RF. Then add local I/Q DDS,
   atomic updates and upstream RTIO integration. DRTIO requires verified
   PCIe–SFP adapter wiring and external clock synchronization.

No flash, EEPROM, OTP, eFUSE, SD or other-board writes are part of this plan.
