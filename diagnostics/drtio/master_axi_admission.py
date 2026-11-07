# SPDX-License-Identifier: LGPL-3.0-or-later
"""Gate AXI handshakes during coordinated reset; no cancellation or retry.

Enable must belong to PS clock domain. Disabling with in-flight operations is
only allowed with requester abandonment and target/bridge reset protocol.
"""
from migen import Module, Signal
from litex.soc.interconnect.axi import AXIInterface

class MasterAXIAdmission(Module):
    def __init__(self,target):
        if (len(target.w.data),len(target.aw.addr),len(target.aw.id))!=(32,40,16):
            raise ValueError('Expected AXI32/address40/id16')
        self.enable=Signal()
        self.axi=AXIInterface(data_width=32,address_width=40,id_width=16)
        for name in ('aw','w','ar','b','r'):
            source,sink=((getattr(target,name),getattr(self.axi,name))
                         if name in ('b','r') else
                         (getattr(self.axi,name),getattr(target,name)))
            self.comb += [source.connect(sink,omit={'valid','ready'}),
                          sink.valid.eq(source.valid & self.enable),
                          source.ready.eq(sink.ready & self.enable)]
