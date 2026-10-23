AXAU15 candidate target — offline handoff, 2026-10-21
=================================================

Status: HDL_GENERATED, SIMULATION_PASS, VIVADO_SYNTHESIS_PASS.
No ALINX, Trenz, Genesys, Kasli or SDWire hardware operations were performed.
This is an incomplete port, not a programming-ready image.

Tool/device gate — resolved 2026-10-22
------------------------------------

Artix UltraScale+ support was added to Dell Vivado 2025.2 using the official
installer's Add operation and the SMB archive. Exact part
``xcau15p-ffvb676-2-i`` matches XCAU15P-2FFVB676I: FFVB676, speed -2,
industrial temperature grade, 12 GTHE4 and IDCODE0x04ac2093. The Synthesis/device
license checkout and exact-part probe passed with no warnings or errors.
The SPI-only and JESD candidates also passed synthesis. The final shared-TX
clock candidate removes all six critical CDC groups seen with separate lane
TX clocks (114 endpoints). This is not full CDC sign-off: the USER2 TCK/mailbox
constraints are still absent. These are not routed implementation results or
physical validation. See ``../evidence/axau15/vivado-20261022/status.json``.

The earlier empty enumeration in ``../evidence/axau15/part-enumeration.txt`` is
historical. Installation evidence is in
``/home/codex-hil/artifacts/axau15-vivado-install-20261021``; the installation
itself is on Dell at ``/srv/nvme-fast-2/toolchains/amd/Xilinx``.
The Optiplex installation was not modified.

Pin and clock review
--------------------

The local 44-page manual SHA-256 matches the recorded pinmap. Pages 29–34
confirm the supplied FMC GPIO, eight GT lanes, bank225 DP0–3, bank226 DP4–7,
GBTCLK0 V7/V6 and GBTCLK1 P7/P6. The 200 MHz input is T24/U24. GPIO is 1.8 V.
This checks the document; physical module/carrier revisions remain unconfirmed.
Vivado package-pin/function cross-check passed for every target pin, including
MGTREFCLK0 V7/V6 and the four TX channels of bank225.

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
The synthesized Vivado clock report derives these clocks. Routing and
physical PLL qualification remain pending. All four lanes share lane0 TX user
clock; the original independent-clock candidate is superseded.
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
bitstream or hardware-manager command. Full implementation must follow completion of CDC/IO timing constraints; do not bypass
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

Offline installer retained on Dell SATA
--------------------------------------

The complete Vivado 2025.2 installer (102739568640 bytes) is stored under
``/srv/backup-local/installers/amd/`` on Dell, with verified SHA-256 and
``REUSE.rst`` instructions for local read-only payload access without SMB.
See ``../evidence/axau15/vivado-20261022/installer-sata.json`` for the exact
filename, checksum and payload readback evidence. The Optiplex installation
and installers remain unchanged.

Physical AXAU15 clock baseline (2026-10-23)
-----------------------------------------

``clock-probe/`` now has a separate routed and physically validated clock-only
image. JTAG-HS1 cable210512180081 identifies XCAU15P IDCODE04AC2093. Volatile
SRAM programming and three advancing counter readbacks passed. Final image
has no FMC outputs or DAC/JESD path. This does not qualify the SPI/JESD candidate
above; AD9172 identity and RF remain pending. See ``clock-probe/README.rst``.
