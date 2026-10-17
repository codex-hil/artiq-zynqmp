"""Opt-in laboratory AXI read delay; LGPL-3.0-or-later.

Not wired into production images. Both sides share an always-running clock/reset.
Caller must assert idle only when there are no outstanding reads. A trigger is
accepted only while idle with no exposed memory response. Once accepted, the
fixed hold expires regardless of trigger/idle changes. Never reset mid-flight.
"""
from migen import Module, Signal, If


class DMAReadDelay(Module):
    def __init__(self, upstream, downstream, cycles):
        if not isinstance(cycles, int) or not 1 <= cycles <= 1048576:
            raise ValueError('Read hold must be 1..1048576 clock cycles')
        if (len(upstream.r.data), len(upstream.r.id)) != (len(downstream.r.data), len(downstream.r.id)):
            raise ValueError('AXI response widths must match')
        self.trigger, self.idle = Signal(), Signal()
        self.accepted, self.rejected, self.holding = Signal(), Signal(), Signal()
        remaining = Signal(max=cycles+1)
        accept = Signal()
        self.comb += [accept.eq(self.trigger & self.idle & ~downstream.r.valid & (remaining == 0)),
                      self.holding.eq(remaining != 0)]
        for name in ('aw', 'w', 'ar'):
            self.comb += getattr(upstream, name).connect(getattr(downstream, name))
        self.comb += downstream.b.connect(upstream.b)
        self.comb += downstream.r.connect(upstream.r, omit={'valid', 'ready'})
        self.comb += [upstream.r.valid.eq(downstream.r.valid & ~self.holding),
                      downstream.r.ready.eq(upstream.r.ready & ~self.holding)]
        self.sync += [self.accepted.eq(accept), self.rejected.eq(self.trigger & ~accept),
                      If(accept, remaining.eq(cycles)).Elif(remaining != 0, remaining.eq(remaining-1))]
