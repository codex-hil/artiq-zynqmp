"""Read-only observer CSR prototype; LGPL-3.0-or-later.

Epoch qualification deliberately tied low: host reads cannot certify drain.
Not wired into production gateware; no CSR address allocated yet.
"""
from migen import Module, Cat
from misoc.interconnect.csr import CSRStatus
from axi_read_observer import AXIReadObserver

class AXIReadObserverCSR(Module):
    def __init__(self,bus,capacity=127):
        self.submodules.observer=AXIReadObserver(bus,capacity)
        self.outstanding=CSRStatus(len(self.observer.outstanding),name='outstanding')
        # bits0 accounting error,1 response error,2 quiet,3 epoch qualified.
        self.flags=CSRStatus(4,name='flags')
        self.comb += [self.observer.epoch_qualified.eq(0),
                      self.outstanding.status.eq(self.observer.outstanding),
                      self.flags.status.eq(Cat(self.observer.accounting_error,
                                               self.observer.response_error,
                                               self.observer.quiet,
                                               self.observer.epoch_qualified))]
    def get_csrs(self):
        return [self.outstanding,self.flags]
