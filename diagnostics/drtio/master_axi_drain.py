# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated single-beat AXI32 drain candidate, not production integration.

Caller restricts AW/AR len=0, size=2, aligned addresses and WLAST=1. One read and
one write outstanding; AW/W may arrive independently. stop blocks new transactions
but accepts the missing half of an already accepted write. Buffered requests and
responses remain visible until handshake. Target and bridge require coordinated
reset after explicit requester abandonment; stop never cancels or retries.
"""
from migen import Module,Signal,If,Cat
from litex.soc.interconnect.axi import AXIInterface

class MasterAXIDrain(Module):
    def __init__(self,target):
        if (len(target.w.data),len(target.aw.addr),len(target.aw.id))!=(32,40,16):
            raise ValueError('Expected AXI32/address40/id16')
        self.stop=Signal(reset=1)
        self.idle=Signal()
        self.axi=a=AXIInterface(data_width=32,address_width=40,id_width=16)
        aw_full,w_full,ar_full,aw_sent,w_sent,ar_sent=[Signal() for _ in range(6)]
        for name,full,sent,permit in (
                ('aw',aw_full,aw_sent,~self.stop | w_full),
                ('w',w_full,w_sent,~self.stop | aw_full),
                ('ar',ar_full,ar_sent,~self.stop)):
            source,sink=getattr(a,name),getattr(target,name)
            source_bits=Cat(source.first,source.last,source.payload.raw_bits(),source.param.raw_bits())
            sink_bits=Cat(sink.first,sink.last,sink.payload.raw_bits(),sink.param.raw_bits())
            stored=Signal(len(source_bits))
            self.comb += [source.ready.eq(~full & permit),
                          sink.valid.eq(full & ~sent),sink_bits.eq(stored)]
            self.sync += [If(source.valid & source.ready,
                             stored.eq(source_bits),full.eq(1)),
                          If(sink.valid & sink.ready,sent.eq(1))]
        for name in ('b','r'):
            self.comb += getattr(target,name).connect(getattr(a,name))
        self.sync += [If(a.b.valid & a.b.ready,
                         aw_full.eq(0),w_full.eq(0),aw_sent.eq(0),w_sent.eq(0)),
                      If(a.r.valid & a.r.ready & a.r.last,ar_full.eq(0),ar_sent.eq(0))]
        self.comb += self.idle.eq(~aw_full & ~w_full & ~ar_full)
