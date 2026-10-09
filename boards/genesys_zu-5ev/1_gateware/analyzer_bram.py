"""Small bring-up ring using the preserved upstream ARTIQ MessageEncoder.

No new analyzer wire format; storage is local BRAM rather than DDR DMA.
Original glue: LGPL-3.0-or-later.
"""
from migen import Module, Signal, Memory, If
from misoc.interconnect.csr import AutoCSR, CSR, CSRStatus, CSRStorage
from artiq.gateware.rtio.analyzer import MessageEncoder

class AnalyzerBRAM(Module, AutoCSR):
    def __init__(self,tsc,cri,depth=256):
        if depth & (depth-1): raise ValueError('depth must be a power of two')
        self.enable=CSRStorage(1,reset=1,name='enable')
        self.clear=CSR(name='clear')
        self.count=CSRStatus(64,name='count')
        self.read_index=CSRStorage((depth-1).bit_length(),name='read_index')
        self.read_update=CSR(name='read_update')
        self.data=CSRStatus(256,name='data')
        self.depth=CSRStatus(32,name='depth')
        self.submodules.encoder=MessageEncoder(tsc,cri,self.enable.storage)
        memory=Memory(256,depth)
        wr=memory.get_port(write_capable=True)
        rd=memory.get_port()
        self.specials += memory,wr,rd
        total=Signal(64)
        self.comb += [self.encoder.source.ack.eq(1),wr.adr.eq(total[:(depth-1).bit_length()]),
            wr.dat_w.eq(self.encoder.source.data),wr.we.eq(self.encoder.source.stb),
            rd.adr.eq(self.read_index.storage),self.count.status.eq(total),self.depth.status.eq(depth)]
        self.sync += [If(self.encoder.source.stb,total.eq(total+1)),
            If(self.clear.re & ~self.enable.storage,total.eq(0)),
            If(self.read_update.re,self.data.status.eq(rd.dat_r))]
