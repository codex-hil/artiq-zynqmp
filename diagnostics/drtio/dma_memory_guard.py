"""Running-clock AXI DMA read drain/isolation, LGPL-3.0-or-later.

Memory side must keep its clock/reset alive until done. A link fault aborts
consumer delivery and drains all accepted AXI reads; it never resets the AXI
reader. This module is not an asynchronous FIFO or complete DMA engine.
"""
from migen import Module,Signal,If,FSM,NextState
from misoc.interconnect import stream
from zynqmp_dma import DMAReader


class DMAMemoryGuard(Module):
    def __init__(self,membus):
        self.start,self.finish,self.abort=Signal(),Signal(),Signal()
        self.active,self.done,self.failed=Signal(),Signal(),Signal()
        self.rejected_start=Signal()
        self.source=stream.Endpoint([('data',len(membus.r.data))])
        flow=Signal()
        self.submodules.reader=reader=DMAReader(membus,flow)
        self.submodules.fsm=fsm=FSM(reset_state='IDLE')
        self.comb += [self.active.eq(~fsm.ongoing('IDLE')),
                     self.source.data.eq(reader.source.data),
                     self.source.eop.eq(0)]
        self.sync += [If(self.start & self.active,self.rejected_start.eq(1)),
            If(fsm.ongoing('IDLE') & self.start,
                self.failed.eq(0),self.rejected_start.eq(self.abort)),
            If(self.active & self.abort,self.failed.eq(1)),
            If(self.active & membus.r.valid & membus.r.ready & (membus.r.resp!=0),
                self.failed.eq(1))]
        fsm.act('IDLE',If(self.start & ~self.abort,NextState('RUN')))
        fsm.act('RUN',
            # Retain a full RUN edge even for an immediate abort: DMAReader
            # must observe its enable rising edge and create its final read.
            flow.eq(1),
            self.source.stb.eq(reader.source.stb & ~self.abort & ~self.finish),
            reader.source.ack.eq(self.source.ack | self.abort | self.finish),
            If(self.abort | self.finish,NextState('DRAIN')))
        fsm.act('DRAIN',reader.source.ack.eq(1),
            If(reader.source.stb & reader.source.eop,NextState('DONE')))
        fsm.act('DONE',self.done.eq(1),NextState('IDLE'))
