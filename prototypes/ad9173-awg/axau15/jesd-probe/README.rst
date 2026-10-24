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
status_scan.v, constraints.tcl and synth.tcl; run synth.tcl on Dell under lease.
Then implement.tcl on that synth.dcp and audit.tcl on routed.dcp. Keep all
reports and exact hashes; never accept build output as physical evidence.
