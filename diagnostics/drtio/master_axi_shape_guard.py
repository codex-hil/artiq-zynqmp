# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated strict singlebeat guard plus drain. No AXI error responder.

Malformed eligible requests see READY0 and latch fault. Initiator may wait until
explicit abandonment and coordinated guard/drain/target reset. Fault is only an
output here, NOT mapped into management. No clear/retry or autonomous reset.
"""
from migen import Module,Signal,If
from litex.soc.interconnect.axi import AXIInterface
from master_axi_drain import MasterAXIDrain

class MasterAXIShapeGuard(Module):
    def __init__(self,target):
        self.submodules.drain=d=MasterAXIDrain(target)
        self.axi=a=AXIInterface(data_width=32,address_width=40,id_width=16)
        self.stop=Signal(reset=1);self.fault=Signal();self.idle=d.idle
        self.comb += d.stop.eq(self.stop | self.fault)
        for name in ('aw','w','ar'):
            source,sink=getattr(a,name),getattr(d.axi,name)
            good=Signal()
            if name=='w':shape=source.last
            else:shape=((source.len==0)&(source.size==2)&(source.addr[:2]==0)
                        &(source.lock==0)&(source.burst<=1))
            self.comb += [good.eq(shape),source.connect(sink,omit={'valid','ready'}),
                          sink.valid.eq(source.valid & good),
                          source.ready.eq(sink.ready & good)]
            # Eligibility comes from drain; accepted missing halves still drain.
            self.sync += If(source.valid & sink.ready & ~good,self.fault.eq(1))
        for name in ('b','r'):
            self.comb += getattr(d.axi,name).connect(getattr(a,name))
