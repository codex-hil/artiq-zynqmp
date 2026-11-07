# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated ring pointer candidate; not wired into native AUX.

Advance at most once per source edge. Encoding is registered alongside binary
state. Both domains require coordinated reset while packet admission is disabled.
Physical Gray bus skew/max-delay constraints, reset release and packet SRAM
visibility remain integration requirements; MultiReg alone is not signoff.
"""
from migen import Module, Signal, If
from migen.genlib.cdc import MultiReg


class AuxGrayPointer(Module):
    def __init__(self, width=3, *, source='rtio_rx', destination='sys'):
        if not isinstance(width, int) or isinstance(width, bool) or width < 2:
            raise ValueError('Pointer width must be an integer of at least two')
        if source == destination:
            raise ValueError('Expected distinct clock domains')
        self.advance = Signal()
        self.binary = Signal(width)
        self.gray = Signal(width)
        self.gray_remote = Signal(width)
        self.remote = Signal(width)
        next_binary = Signal(width)
        self.comb += next_binary.eq(self.binary + 1)
        source_sync = getattr(self.sync, source)
        source_sync += If(self.advance,
            self.binary.eq(next_binary),
            self.gray.eq(next_binary ^ (next_binary >> 1)))
        self.specials += MultiReg(self.gray, self.gray_remote, destination)
        for bit in range(width):
            parity = self.gray_remote[bit]
            for higher in range(bit+1, width):
                parity = parity ^ self.gray_remote[higher]
            self.comb += self.remote[bit].eq(parity)
