# Genesys ZU-5EV DRTIO clock-recovery investigation

2026-10-08: design investigation only; no DRTIO hardware PASS claimed.
Target role: satellite to the existing Kasli master. Existing local RTIO/DMA
artifacts remain unchanged.

## Board resources verified from Digilent documentation

The 5EV board has GTHE4 transceivers in quad224. SFP+ shares channel3
(X0Y7) with FMC DP0 through the board mux; select SFP routing before link
bring-up. IC46 Si5342A-D-GM drives quad224 MGTREFCLK0. Its default OTP
profile is free-running156.25MHz, not an ARTIQ clock configuration.

Si5342 can instead lock to SFP_REC_CLK_P/N, which the FPGA drives from
user I/O, filter that recovered clock, and return a reference to GTH.
Main I2C mux channel2, address0x68 accesses IC46. Verify actual board
revision/schematic and VADJ/output electrical standard before constraints.
No OTP programming is required: use a volatile boot-time register profile.
Do not reconfigure IC67, which also supplies the PS reference clock.

## Planned clock chain

Kasli serial DRTIO -> SFP -> GTHE4 CDR -> recovered RXOUTCLK
 -> BUFG_GT -> clock-forwarding output -> SFP_REC_CLK_P/N
 -> Si5342 jitter attenuation -> MGTREFCLK0 -> GTHE4 TX/RTIO clock chain.

The clean-reference-to-fabric path must use IBUFDS_GTE4/BUFG_GT or the
chosen transceiver TXOUTCLK path, with any required MMCM division. Exact
PLL/divider and user-clock settings are not yet generated or validated.
Clock forwarding uses a DDR output primitive and differential output buffer;
these are user-I/O pins, not dedicated OBUFDS_GTE4 transceiver outputs.

Retain an independent PS-derived bootstrap/management clock throughout.
Bring up RX using a free-running reference, wait for valid recovered clock,
acquire Si5342 lock, then reset/align and synchronize the DRTIO link.
Do not attempt acquisition from a stopped recovered clock. Input loss,
holdover/reacquisition and TX/RX reset interactions need an explicit FSM.
Loss of synchronized link must disable scheduled peripheral output until
link/timestamp synchronization is restored.

For first PHY diagnostics, recovered RXOUTCLK -> BUFG_GT can clock the RX
logic directly. This proves CDR/decoding, not filtered TX reference quality
or deterministic end-to-end timing.

## ARTIQ compatibility and implementation boundary

The checked-in upstream gtx_7series.py uses two 8b10b symbols per cycle,
20 serial bits per125MHz cycle,2.5Gb/s. A150MHz master requires its matching
3Gb/s configuration. Confirm the actual Kasli gateware version/frequency
before selecting profiles. These are DRTIO links, not10G Ethernet.

Piotr's checked-in work has no validated GTHE4 DRTIO PHY or Si5342 lock
sequence. Current upstream transceiver directory contains7-series GTX/GTP
and EEM implementations, not a drop-in GTHE4 implementation. Reuse the
ARTIQ link/protocol, ChannelInterface and satellite logic; adapt only the
GTHE4 PHY, initialization/alignment and board clock controls. A locked CDR
or Si5342 alone does not prove deterministic latency. Buffer bypass,
comma/word alignment, phase alignment and ARTIQ time synchronization all
need validation after repeated resets and cable reconnects.

## Staged verification

1. Read-only I2C mux/Si5342 identity and status dump, matched to its manual.
2. Generate separate free-run and recovered-reference profiles; preserve
   baseline registers and do not write OTP. Measure programmed frequency.
3. Build GTHE4 single-SFP PHY diagnostic with counters: PLL lock, resetdone,
   recovered clock activity, comma alignment, disparity/code errors.
4. Run PRBS loopback/remote PHY checks before adding satellite protocol.
5. Lock Si5342 to recovered input; log loss-of-signal/lock and reacquisition.
6. Integrate upstream DRTIO satellite and auxiliary management with Kasli.
7. Validate timestamp synchronization and cross-board TTL timing through
   repeated power cycles, GTH resets and cable disconnect/reconnect.
8. Only then connect the synchronized DAC/JESD204B timing chain on ZCU102.

Pending physical inputs: Kasli model, installed ARTIQ revision and RTIO
frequency, available DRTIO port, compatible SFPs/cable. Genesys has adequate
clock-recovery hardware for this proof but not the full8-lane AD9172 FMC
interface. DAC clock/SYSREF deterministic phase remains a separate test.

## Sources

- Digilent board clocks and SFP routing:
  https://digilent.com/reference/programmable-logic/genesys-zu/reference-manual
- AMD UG576 (GTHE4 initialization, recovered RXOUTCLK, buffer bypass):
  https://www.amd.com/content/dam/xilinx/support/documents/user_guides/ug576-ultrascale-gth-transceivers.pdf
- AMD UG572 BUFG_GT:
  https://docs.amd.com/r/en-US/ug572-ultrascale-clocking/BUFG_GT-and-BUFG_GT_SYNC
- Checked-in common/artiq/artiq/gateware/drtio/transceiver/gtx_7series.py.
