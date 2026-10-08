# Genesys single-SFP DRTIO PHY preparation

This stage generates and synthesizes the GTHE4 PHY and runs upstream DRTIO
protocol simulations. It does not yet produce a board-level bitstream or a
working DRTIO satellite. Clocking plan: ../../docs/DRTIO_CLOCKING.md.

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
external to this generated core and still require a board-level wrapper.
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
3. Add a separate diagnostic top: user clock buffers, reset control, PRBS
   counters, recovered-clock counter and PS-readable status. Place/route.
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
