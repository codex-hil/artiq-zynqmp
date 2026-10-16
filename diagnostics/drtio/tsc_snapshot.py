"""Request-scoped coherent RX TSC snapshot via async FIFO; LGPL-3.0-or-later.

Both domains must share reset assertion through loss/restart. Valid is cleared
at request acceptance and held only after a complete FIFO read; no bitwise
synchronization of the running binary counter. Physical FIFO CDC qualification
is required before hardware use.
"""
from migen import Module, Signal, If, ClockDomainsRenamer
from migen.genlib.cdc import MultiReg
from migen.genlib.fifo import AsyncFIFO


class TSCSnapshot(Module):
    def __init__(self):
        self.request, self.busy, self.valid = Signal(), Signal(), Signal()
        self.value, self.sample = Signal(64), Signal(64)
        token, seen, synced = Signal(), Signal(), Signal()
        previous = Signal()
        self.specials += MultiReg(token, synced, 'sample')
        self.submodules.fifo = f = ClockDomainsRenamer({'write':'sample','read':'sys'})(AsyncFIFO(64,4))
        self.comb += [f.din.eq(self.sample),f.we.eq((synced!=seen) & f.writable),
                      f.re.eq(self.busy & f.readable)]
        self.sync.sample += If(f.we,seen.eq(synced))
        self.sync += [previous.eq(self.request),If(self.request & ~previous & ~self.busy,
                token.eq(~token),self.busy.eq(1),self.valid.eq(0)),
            If(self.busy & f.readable,
                self.value.eq(f.dout),self.valid.eq(1),self.busy.eq(0))]
