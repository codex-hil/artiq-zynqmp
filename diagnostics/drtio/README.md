# Genesys single-SFP DRTIO PHY preparation

This stage builds a separate GTHE4 diagnostic board bitstream and runs
upstream DRTIO protocol simulations. Internal PMA PRBS7 hardware tests
passed on 2026-10-08. A working DRTIO satellite is still missing. Clocking plan: ../../docs/DRTIO_CLOCKING.md.

## Reproduce

Use the shared Vivado 2025.2 launcher and existing Python environment:

```sh
make drtio-phy PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python \
  DRTIO_REFCLK_MHZ=125 O=/srv/codex-hil-data/artiq-zynqmp/build/drtio-user
# Separate profile for the board's unchanged factory reference:
make drtio-phy PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python \
  DRTIO_REFCLK_MHZ=156.25 O=/srv/codex-hil-data/artiq-zynqmp/build/drtio-user-factory
make test-drtio-protocol PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python \
  ARTIQ_SOURCE=/srv/codex-hil-data/artiq-zynqmp/reference/artiq
```

Generated configuration: GTHE4 X0Y7 (Genesys SFP mux channel), CPLL,
2.5Gb/s TX/RX, raw20-bit words,125MHz TX/RX user clocks. Both125MHz and
156.25MHz reference profiles are independent of the serial word rate.
The latter permits initial RX diagnostics with the factory Si5342 profile.
The125MHz-reference profile requires the corresponding Si5342 programming.
Reset/controller freerun input needs an independent125MHz bootstrap clock.

PRBS selection/error, loopback, PLL lock, RX/TX resetdone, RXOUTCLK,
and the wizard CDR-stable indication are exposed. The CDR-stable indication
is a reset-sequencer estimate, not a substitute for measured clock activity
or a verified remote link. User-clock buffers/active/reset handling are
external to this generated core and are supplied by diag_gateware.py.
No 10G Ethernet MAC or protocol is instantiated. There is no need to change
PS Ethernet, existing local RTIO or CPU1 firmware for this build.

The generated AMD transceiver wizard is an initial diagnostic reference for
GTHE4 parameter/reset behavior. ARTIQ's existing raw8b10b/link/satellite
logic is retained separately; the wizard does not implement DRTIO.
Diagnostic TX/RX elastic buffers are enabled. Their build success must not
be reported as deterministic-latency validation. The final adapter needs
buffer-bypass/phase-alignment/word-alignment behavior and repeated-reset
latency tests. Kasli125MHz is the initial profile;150MHz requires a separate
3Gb/s profile once the real master configuration is identified.

## Next hardware stages

1. Confirm board revision and physical SFP mux/clock-forwarding pin mapping.
2. Read Si5342 identity/status and save its existing register configuration.
3. DONE: separate diagnostic top with clock buffers, reset control, PRBS
   counters and PS-readable status; place/route and internal loopback PASS.
4. Verify local loopback, then Kasli-to-Genesys RX125MHz and raw symbol stream.
5. Configure recovered-input jitter attenuation and test lock/reacquisition.
6. Integrate ARTIQ satellite/auxiliary firmware and synchronized TTL tests.

Prerequisites to bring with Kasli: working master gateware, ARTIQ version,
RTIO frequency, a free DRTIO SFP port and compatible SFP modules/cable.
A cable from the Ethernet switch is not a DRTIO connection.

## Recovered existing clock-control work

The already archived Digilent HDMI demo contains si5432_axi.c/.h (name typo;
the code controls Si5342) at the revision in clock-source-origins.json. It
provides an existing411-register jitter-attenuation profile, paged register
access and the300ms configuration-preamble delay. Reuse its configuration
sequence as a reference rather than inventing a new clock-control protocol.
Its HDMI frequency/input profile is not a125MHz SFP DRTIO profile. Its
transport uses AXI IIC, so the existing AMD XIicPs driver is the appropriate
PS-I2C transport for our runtime. Verify mux mapping before access. The
reference status routine does not propagate all I2C errors; our adapter
must fail explicitly on failed reads instead of reporting lock from an
uninitialized buffer. No clock writes have been performed at this stage.

The archived revC constraints identify SFP recovered-clock P as A2 and mux
select as D10 (sel_sfp_not_fmc). Treat these as historical reference only
until matched against the physical board revision; confirm complementary
clock pin/electrical standard before driving it.

## Separate board diagnostic

`make drtio-top DRTIO_PS_EXPORT=/path/to/genesys-rtio-dma
DRTIO_PHY_EXPORT=/path/to/validated156 O=/fresh/output` builds a separate
PS/HPM0-accessible diagnostic bitstream. Put the command on one line.
It reuses Piotr's PS export and AXI bridge, selects SFP on D10, and keeps
external SFP TX disabled. This image replaces local RTIO while loaded.
It does not implement a satellite or change Si5342 configuration.

Run `make test-drtio-monitor` with the existing Migen Python environment.
The tests exercise counter wrap, gated error counting and held snapshots.
Gray counters cross RX/TX clock domains into PS; synthesis must find all
32 source and destination bits and routing reports the 8ns bus-skew limit.

After exact-cable PS reset, PMU/FSBL startup and PL configuration, run
`prepare_ps.tcl SERVER PSU_INIT CABLE` using the existing matching DMA PS
initialization file. All A53 CPUs must be halted. The diagnostic CSR magic
is `0x44525430`; ordinary RTIO register maps are incompatible. Then:

```sh
make test-hw-drtio-phy JTAG_SERVER=tcp:172.17.0.2:3121 \
  CSR_MAP=/path/to/diagnostic/csr-map.json O=/path/to/evidence
```

The test performs three reset/acquisition cycles in internal near-end PMA
loopback, checks RX/TX clock ratios against the 125MHz bootstrap counter,
and requires zero settled PRBS7 errors. A mismatched TX PRBS15 negative
control must register errors, then PRBS7 must recover after a GTH reset. External SFP TX stays disabled.
A passing result proves local GTH operation only. Remote DRTIO, recovered
Si5342 lock, symbol alignment and deterministic latency need separate tests.
Restore the working local-RTIO/CoreDMA image and matching firmware afterward.

The historical Migen CDC constraint targets nets carrying `mr_ff`, whereas
Vivado retains that attribute on first-stage registers. This diagnostic
adds a checked register-D false path and retains explicit Gray bus-skew
constraints. No archived Migen source is changed. The build verifier rejects
missing artifacts, unclosed timing and missing/failing bus-skew reports.

## Raw20 codec integration (simulation only)

`raw20_codec.py` connects the existing MiSoC Encoder(2, True), Decoder(True)
and ARTIQ ChannelInterface to a raw20-bit transceiver port. Lane0 occupies
bits0–9, lane1 bits10–19; the existing LSB-first convention matches Kasli's
upstream PHY. TX runs in sys; decoders run in recovered rtio_rx. Readiness
requires reset done, an active RX clock, verified word alignment and no
active reset. These status inputs must already be synchronized to sys.
No GT reset/alignment logic, elastic-buffer bypass, CDC timing constraints,
Si5342 control or satellite firmware is provided by this codec.
The diagnostic PRBS image is unchanged and does not instantiate this codec.

```sh
make test-drtio-codec PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python \
  ARTIQ_SOURCE=/srv/codex-hil-data/artiq-zynqmp/work/kasli-master \
  MISOC_SOURCE=/srv/codex-hil-data/artiq-zynqmp/work/kasli-misoc
```

Wire-level tests extend the upstream LGPLv3+ link-layer test with actual
8b/10b encoders/decoders and two phase-offset125MHz-model clocks. Concurrent
RT/AUX packets survive encoding/decoding byte-exactly. Swapping the10-bit
lanes is an intentional negative control and corrupts both traffic types.
All16 readiness combinations are checked. These tests do not prove GT
comma acquisition, clock recovery, link firmware or deterministic latency.

## RT/AUX framing through physical GTH

The optional `DRTIO_PROTOCOL=1` top instantiates the preserved upstream
ARTIQ LinkLayerTX/LinkLayerRX and software 8b/10b codec in the actual GTH
TX/RX clock domains. A fabric aligner searches all 20 serial offsets for
lane-zero K28.5, then holds its selected offset until the RX domain resets.
This laboratory aligner does not provide GT buffer bypass, deterministic
latency or automatic remote-link loss detection.

The generator sends 16-word RT and 16-nibble AUX frames, with known payload
sequences. RX-domain counters check payload and frame length; Gray counters
cross into independent PS management. Raw encoded-bit corruption is an
explicit negative control, followed by a clean recovery interval.
External SFP TX stays disabled. This is link framing, not satellite RTIO
packet execution or AUX firmware discovery.

```sh
make test-drtio-framing PYTHON=/path/to/venv/bin/python \
  ARTIQ_SOURCE="$PWD/common/artiq" MISOC_SOURCE=/path/to/misoc
FORWARD_RX_CLOCK=1 DRTIO_PROTOCOL=1 \
  PYTHON=/path/to/venv/bin/python MISOC_SOURCE=/path/to/misoc \
  bash diagnostics/drtio/build_top.sh \
  /path/to/ps-export /path/to/validated156 /fresh/drtio-protocol
```

Use the exact-cable reset → PMU/FSBL → PL programming → `prepare_ps.tcl`
sequence above, with all A53s halted. The unchanged PRBS hardware runner
can still be used first; it resets the GTH and selects PRBS7. Then:

```sh
make test-hw-drtio-framing PYTHON=/path/to/venv/bin/python \
  JTAG_SERVER=tcp:SERVER:3121 SI5342_CABLE=YOUR_GENESYS_SERIAL \
  CSR_MAP=/fresh/drtio-protocol/csr-map.json O=/path/to/evidence
```

The framing runner disables PRBS, selects internal PMA loopback, performs
three reset/alignment/traffic cycles, checks receiver-side RT and AUX
payloads, injects corruption and checks recovery. Restore the normal
ARTIQ/CoreDMA PL and both CPU images afterward. No Si5342 configuration is
changed by this runner; the default 156.25 MHz reference profile is used.

Physical result (2026-10-09): three cycles PASS, each with over 15,000 RT
and AUX frames, zero new settled errors, detected encoded-bit corruption
and clean recovery. Evidence: `evidence/drtio-framing-hardware-2026-10-09.json`.
