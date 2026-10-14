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
