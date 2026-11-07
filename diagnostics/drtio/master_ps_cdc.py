# SPDX-License-Identifier: LGPL-3.0-or-later
"""Candidate PS/master AXI-Lite crossing with coordinated FIFO reset.

Both external domain resets must be asserted together with requester and target
reset. Requester must abandon outstanding transactions before release. Reset
cannot undo a target write or establish whether an unacknowledged write executed.
No timeout, retry, board reset sequencer or physical CDC qualification is supplied.
"""
from migen import Module
from litex.soc.interconnect import stream


class GenesysMasterPSCDC(Module):
    def __init__(self, ps, master, *, ps_clock='sys', master_clock='master'):
        if ps_clock == master_clock:
            raise ValueError('This boundary requires distinct declared clock domains')
        if ps.data_width != 32 or master.data_width != 32:
            raise ValueError('Expected 32-bit AXI-Lite data')
        if ps.address_width != master.address_width:
            raise ValueError('Address truncation across CDC is forbidden')
        if ps.mode != 'rw' or master.mode != 'rw':
            raise ValueError('All five AXI-Lite channels are required')
        self.crossings = {}
        for name in ('aw', 'w', 'b', 'ar', 'r'):
            reverse = name in ('b', 'r')
            source_bus, sink_bus = (master, ps) if reverse else (ps, master)
            source_clock, sink_clock = ((master_clock, ps_clock) if reverse
                                        else (ps_clock, master_clock))
            source, sink = getattr(source_bus, name), getattr(sink_bus, name)
            crossing = stream.ClockDomainCrossing(
                source.description, cd_from=source_clock, cd_to=sink_clock,
                depth=4, with_common_rst=True)
            self.crossings[name] = crossing
            self.submodules += crossing
            self.comb += [source.connect(crossing.sink), crossing.source.connect(sink)]
