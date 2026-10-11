# Satellite packet header truncation correction

The preserved Piotr ARTIQ dependency and archived current ARTIQ reference
both put the satellite INPUT-state truncation guard inside the opposite
condition: `If(frame, ... If(~frame & ongoing, error=1))`. A write header
ending after one16-bit word is consequently discarded without reporting
`packet_truncated`; it must not issue a CRI command.

`diagnostics/drtio/satellite_packet.py` subclasses the upstream packet engine
and moves that existing guard outside the enclosing `If(frame, ...)`. It
checks the exact original FSM structure and fails explicitly if an upstream
update changes it. Serializer, layouts and original checkout files remain
unchanged. This is a port-local overlay, not an upstream merged fix, and
callers must explicitly instantiate `CheckedRTPacketSatellite` to use it.

Three tiny bounded RTL tests verify the original negative control (zero
truncation reports), the corrected header (exactly one report) and a complete
unknown-type packet (exactly one unknown report and zero truncation reports).
All cases verify that no CRI command is issued. They pass on both snapshots;
source revisions and evidence are in
`evidence/satellite-truncation-2026-10-11.json`. These are simulations, not
physical satellite qualification.

```sh
PYTHONPATH="$PWD/diagnostics/drtio:$PWD/common/artiq:$PWD/common/migen:/path/to/misoc" \
  /path/to/HDL/python -m unittest discover -s diagnostics/drtio \
  -p test_satellite_truncation.py -v
```

For the modern reference, replace only the common/artiq entry with that
checkout's absolute path. Original new glue is LGPL-3.0-or-later; upstream
ARTIQ copyright and license remain with its authors.
