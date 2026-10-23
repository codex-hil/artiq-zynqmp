"""Passive AXI read burst accounting prototype; LGPL-3.0-or-later.

Not wired into production gateware. A reset loses history: a separate, reviewed
external owner must qualify the epoch before any quiet indication is usable.
"""
from migen import Module, Signal, If

class AXIReadObserver(Module):
    def __init__(self, bus, capacity=127):
        if type(capacity) is not int or capacity<1:raise ValueError('Positive capacity required')
        self.epoch_qualified=Signal()
        self.outstanding=Signal(max=capacity+1)
        self.accounting_error=Signal()
        self.response_error=Signal()
        self.quiet=Signal()
        accepted=Signal();completed=Signal()
        self.comb += [accepted.eq(bus.ar.valid & bus.ar.ready),
                      completed.eq(bus.r.valid & bus.r.ready & bus.r.last),
                      self.quiet.eq(self.epoch_qualified & ~self.accounting_error &
                                    ~self.response_error & (self.outstanding==0) &
                                    ~bus.ar.valid & ~bus.r.valid)]
        self.sync += [
            If(bus.r.valid & bus.r.ready & (bus.r.resp!=0),self.response_error.eq(1)),
            If(accepted & ~completed,
                If(self.outstanding==capacity,self.accounting_error.eq(1))
                .Else(self.outstanding.eq(self.outstanding+1))),
            If(completed & ~accepted,
                If(self.outstanding==0,self.accounting_error.eq(1))
                .Else(self.outstanding.eq(self.outstanding-1)))]
