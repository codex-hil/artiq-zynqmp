AXAU15 / AD9172 JESD diagnostic
==============================

Separate target derived from the synthesis candidate. Uses qualified SPIv2
TCK-paced GPIO, dedicated FMC MGTREFCLK0, QPLL1 in bank225, four GTH TX at
nominal6.144Gb/s and one shared153.6MHz TX user clock. Two subclass0 mode3
links L2/M2/N16/NP16/F2/S1/K32/HD1, scrambling. Payload is constant zero;
no payload mailbox, RF tone or amplitude proof in this image.

Generator preserves the corrected HD ILAS bit/checksum and drives DualLink
converter_inputs. No changes to shared dependency clones or Trenz sources.
RX is disabled. No deterministic latency, reference-loss recovery/watchdog,
BER or production PHY claim. The known QPLL LOCK-stays-high behavior requires
activity detection before production use; this bounded startup test keeps the
reference on throughout, and does not claim automatic fault containment.

USER1 high word0x41584a31, low bits:0 QPLL lock,1..4 GTH TX ready,
5..6 raw SYNC levels,7..8 link ready. Each bit independently synchronized;
repeated host reads, no atomic multi-bit status promise. USER2 GPIOv2 unchanged.

DAC register plan is generated offline from control/ad9172_profile.py by
emit_plan.py. The ID is9172; AD9173-only profile is never run. AD9172 Rev.C
Tables53..57 and register map checked for dual mode3/interpolation8x2,
SERDES startup, lane crossbar, sync and SPI muting. 0x45a HD is read-only1.
Source: https://www.analog.com/media/en/technical-documentation/data-sheets/ad9172.pdf

0x03f=0 is NOT an explicit TXEN-low command; it disables TXEN datapath muting.
Earlier clock diagnostics additionally had digital clock powerdown0x100=1.
Here set both main pages0xc0,0x596=4 (SPI TXEN low),0x03f=0x30 before powering
digital clocks. Keep internal DC injection disabled and zero FPGA samples.

Hardware runner is restricted to ALINX cable210512180081, xcau15p ID04ac2093,
its existing lease and isolated USB node. Only volatile SRAM/register writes.
No scope, Trenz, Genesys, Kasli, SDWire, flash, EEPROM, OTP or eFUSE access.
HMC output12 incremental LVDS profile only; NEVER global divider restart
while preserving DAC PLL lock. Success leaves zero JESD traffic, SPI-muted
DAC and reference enabled. Failure attempts mute, links off, digital powerdown
and reference off. HMC writes have no readback; capture all evidence.

Validation: seven existing transport simulations pass. test_host.tcl runs the
actual read.tcl against an explicit abstract model: positive, wrong-ID no-write,
PHY-timeout cleanup and bad-link cleanup pass. These are SIMULATION_ONLY.
Vivado implementation and physical results must be recorded separately.

Status paging correction: retain LINK_EN=3 when reading link pages. Use
0x300=0x0b/0x0f, not0x08/0x0c. Initial hardware script disabled links while
reading status, producing CGS0x02; cleanup muted/powered down. The corrected
host model now makes CGS depend on LINK_EN and rejects the former sequence.

2026-10-24 outcome: implementation and physical startup PASS. Final bit SHA256
6ac3a607bc150e038e599059cdf4c9d6d22dbcf94a028ac26b342f28ec0010ee.
Three status sets per link:0x470..473=3 and0x46d..46f=0; FPGA status0x1ff.
DAC PLL/DLL/SERDES PLL stay locked. Zero payload only, TXEN held low.
Hardware reference loss/recovery, repeated cold starts, amplitude/RF not qualified.
Build: generate HDL/init files into a new directory, copy core.v, spi_gpio.v,
status_scan.v, payload_scan.v, constraints.tcl and synth.tcl; run synth.tcl on Dell under lease.
Then implement.tcl on that synth.dcp and audit.tcl on routed.dcp. Keep all
reports and exact hashes; never accept build output as physical evidence.


Programmable payload diagnostic (2026-10-24)
------------------------------------------
``generate.py --payload`` selects image signature0x41585031 and adds USER3
(IR0x22). The default generator still builds the historical zero-only image.
USER3 write magic0x41585060 with low16 sample bits; read magic0x41585062,
low16 held sample, bit16 busy. The host must wait until busy=0 and the echoed
sample matches. Reads have no write magic. Both links receive the same signed
I word twice per153.6MHz cycle and Q=0; no sample bit selects PRBS.

The source holds all16 bits until the destination returns an acknowledgement.
Two ASYNC_REG stages synchronize each request/ack toggle. The destination
captures the bundled bus on the third destination edge after request launch;
all16 bus paths have a6ns datapath budget and6ns bus-skew limit. CDC-15 warnings
are expected for these16 clock-enable-controlled paths; they are not hidden
by false paths or blanket clock groups. Configuration initializes both ends
to0. There is no runtime mailbox reset and no reference-loss watchdog; a stopped
JESD clock keeps the mailbox busy. This remains a bounded lab diagnostic.

``test_payload.v`` exercises the actual RTL with asynchronous clocks, arbitrary
signed/asymmetric words, invalid magic, stopped destination clock and rejection
of writes while busy. Local XSim lacked GCC; the same RTL test runs with locally
extracted Icarus12.0 (no toolchain replacement). Existing seven JESD simulations
and host startup negative controls remain applicable. ``test_payload_host.tcl``
models positive RF sequencing, wrong-ID no-write, NCO failure and scope abort.
These tests do not constitute hardware evidence.

``emit_tones.py`` compiles149/151MHz NCO transactions from the portable AD9172
profile. Register semantics checked against AD9172 Rev.C, startup Table58 and
registers0x03f/0x596. ``run_payload.py`` requires the exact bitstream SHA and a
new output directory. It holds both ALINX and MSO4104 leases, programs only
ALINX volatile SRAM, runs the zero/muted JESD startup, verifies DAC identity,
DSP settings and disabled internal DC, then tests baseline/full/half/zero/
recovered/asymmetric/final samples. RF measurements use CH3/4 only, existing
continuous auto acquisition and existing horizontal settings. CH1/2 are not
configured. CH3/4 vertical and waveform-transfer settings are saved/restored.

Each stage waits for host measurement acceptance. Ratios are checked within
0.05 absolute, frequency within50kHz, zero residual tone below3% of full-scale
(or5mVpp), and clipping/poor sinusoidal fit rejected. Raw waveforms are retained.
Success leaves0x7fff streamed samples with149/151MHz main NCOs. Failure requests
zero samples and SPI mute, with a separate identity-guarded mute attempt in
the Python runner. Inspect cleanup logs before claiming a failed run's state.
No RTIO, local DDS, deterministic phase, cold-start or jitter qualification.


AXAU15 / AD9172 physical RF milestone — 2026-10-24
------------------------------------------------
The currently installed ALINX FMC is AD9172 (ID9172, revision2), not the
AD9173 attached to the separate Trenz. Four6.144Gb/s GTH lanes and two mode3
JESD links now deliver FPGA-sourced I samples, Q=0, with main DAC NCOs at
nominal149/151MHz. Internal DAC DC injection is disabled. Full/half/zero/
recovery plus nonsymmetric0x5a82 payload passed on MSO4104 CH3/4. Full levels
were0.4755/0.4830Vpp, half0.2353/0.2385Vpp; fitted residual near the expected
tones at zero was0.309/0.265mVpp. Recovered full levels0.4755/0.4830Vpp.
Final measured tones148.9967/150.9970MHz; clock reference is free-running,
not a calibrated frequency/phase/jitter result. Both JESD links stayed clean.

Running bit SHA256c23b923be1a0fa25ee6fcc181687d023431f9e40c5ed5148af9013327c7e09d3,
USER1 signature0x41585031. Final FPGA I=0x7fff on both links, SPI TXEN enabled;
HMC output12 LVDS remains on. Only ALINX volatile SRAM/registers were written.
Scope CH1/2 and global acquisition/trigger/horizontal settings were unchanged;
CH3/4 vertical and waveform-transfer settings were restored. Trenz untouched.

Evidence from AWG root: evidence/axau15/payload-rf-20261024/acceptance.json and hardware/.
Reproducer: axau15/jesd-probe/run_payload.py (exact bit SHA and new output path).
Implementation: WNS3.890ns/WHS0.023ns, DRC0errors; sixteen reviewed CDC-15
bundled-data paths with request/ack handshake and6ns timing budget.
Next: local signed complex DDS/IQ with atomic parameter updates, then RTIO.
Cold start, reference-loss watchdog, deterministic phase, long BER and DRTIO
remain unqualified; no claim of production ARTIQ AWG integration.
