# Historical I2C findings — 2026-10-14

Operator suggested an early Kasli hardware issue. Primary hardware issue:
https://github.com/sinara-hw/Kasli/issues/46 (2019-08-27), I2C pullups/repeaters.
It discusses excessively strong parallel pullups, low-level voltage margins
and TCA9517 topology. A maintainer reported implementing suggested changes on
2019-08-29. This supports a historical electrical issue, but does not identify
our Si5324 path or prove a specific Kasli1.1→later revision fix.
Do not transfer the EEM Si570 anecdote to the onboard Si5324 without tracing
schematics and exact component population.

Pinned ARTIQ history, preserved checkout:
- f4d331d05d7160c5895348c2031c6bb324b86541 (2020): true open-drain I2C,
  explicit phase handover and arbitration/stuck-clock checks.
- 0d2f89db5366ff52f618d9fe1789a6242359a99c (2018): Si5324 does not ACK
  reset-register write. f213b8e1ca3abfcf2681a8a05252fbeb294530fe (2025)
  preserves this special case with the newer Result API.
- 4ddad5fd17bb07fc754d764d3ff157300d27e109 (2025): STOP after NACK.
- A 2020 doubled mux-control-byte workaround f265976d was reverted8719bab7;
  do not revive it without evidence.

Our seven snapshot NACKs occurred on address/register-offset bytes during
read-only access, not the reset value byte. The expected soft-reset NACK does
not explain them. The diagnostic uses LiteX open-drain GPIO and our UART-side
Python bitbang, not the upstream Rust transaction implementation. Attribution
to hardware remains unproven; compare timing/ACK sampling first and trace the
repeater/pullup path before any physical rework. No hardware accessed here.

## First timing overlay experiment

`settled_i2c.py` reuses original RNG-RPI transactions but separates falling SCL
from SDA changes, holds phases100us and samples SDA again after settling.
Physical54 register reads PASS with zero retries/NACKs; all27 pairs match the
prior original snapshot exactly and PLL remains locked. Session79.554s under
three shared Kasli locks; mux/bus restored, no clock configuration writes.
Previous original run had seven retried NACKs. This is a promising observation,
not causal proof: fresh interleaved original/settled controls remain pending.

Two offline controls PASS: delayed ACK is detected by late sampling, while a
true persistent NACK remains a failure. Simulation does not qualify electrical
margins. Evidence kasli03-clock-settled-2026-10-14; capture wrapper --settled-timing.

## Fresh A/B repeat blocked by missing board

The next original-timing attempt stopped before JTAG/UART access: expected
KASLI03 topology1-6.2 and its handed-over UART path were absent. Host inventory
showed Genesys plus another FT4232H on the historical KASLI01 path, which was
not accessed or substituted. No fresh timing comparison result exists.
The capture wrapper now reports BLOCKED_HARDWARE_ABSENT explicitly.
Operator must reconnect KASLI03 or provide a new handoff location; exact DNA
must be reconfirmed under its shared locks before any retargeted access.

## Fresh ordered original/settled comparison — 2026-10-15

KASLI03 reappeared through hubs at USB1-2.4.1/001:019. Exact DNA confirmed;
UART channelC maps to usb-0:2.4.1:1.2-port0. Both captures hold all three Kasli
locks, check DNA and diagnostic identity, restore mux/bus state and release.
54 original-timing reads needed13 retried NACKs;54 settled reads needed zero.
All register pairs and values match across modes; PLL remains locked.
No clock configuration/FPGA/flash writes. Evidence kasli03-clock-ab-2026-10-15.

This reinforces a timing-sensitive diagnostic effect; it does not identify
which timing change matters or exclude electrical margins. The settled mode
now has two separate54-read zero-NACK runs. Do not label Kasli1.1 defective or
claim a universal hardware cure from this ordered pair. Next use settled
sampling for diagnostic profile handling while qualifying actual runtime.
