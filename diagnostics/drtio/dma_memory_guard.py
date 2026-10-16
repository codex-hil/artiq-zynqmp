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
        self.clear=Signal()
        self.active,self.done,self.failed=Signal(),Signal(),Signal()
        self.rejected_start=Signal()
        self.max_bursts=Signal(32) # zero keeps the original unlimited lab mode
        self.burst_count=Signal(32)
        self.budget_error=Signal()
        self.source=stream.Endpoint([('data',len(membus.r.data))])
        flow=Signal();limit=Signal(32);budget=Signal();bad_limit=Signal()
        self.submodules.reader=reader=DMAReader(membus,flow)
        self.submodules.fsm=fsm=FSM(reset_state='IDLE')
        self.comb += [self.active.eq(~fsm.ongoing('IDLE')),
                     self.source.data.eq(reader.source.data),
                     self.source.eop.eq(0),
                     budget.eq((limit!=0) & (self.burst_count>=limit-3)),
                     bad_limit.eq((self.max_bursts!=0) & (self.max_bursts<4))]
        self.sync += [If(self.clear & ~self.active,
                self.failed.eq(0),self.budget_error.eq(0),self.rejected_start.eq(0)),
            If(self.start & self.active,self.rejected_start.eq(1)),
            If(fsm.ongoing('IDLE') & self.start,
                self.failed.eq(bad_limit),self.rejected_start.eq(self.abort | bad_limit),
                limit.eq(self.max_bursts),self.burst_count.eq(0),self.budget_error.eq(bad_limit)),
            If(self.active & membus.ar.valid & membus.ar.ready,
                self.burst_count.eq(self.burst_count+1)),
            If(fsm.ongoing('RUN') & budget,self.failed.eq(1),self.budget_error.eq(1)),
            If(self.active & self.abort,self.failed.eq(1)),
            If(self.active & membus.r.valid & membus.r.ready & (membus.r.resp!=0),
                self.failed.eq(1))]
        fsm.act('IDLE',If(self.start & ~self.abort,
            If(bad_limit,NextState('DONE')).Else(NextState('RUN'))))
        fsm.act('RUN',
            # Retain a full RUN edge even for an immediate abort: DMAReader
            # must observe its enable rising edge and create its final read.
            flow.eq(1),
            self.source.stb.eq(reader.source.stb & ~self.abort & ~self.finish & ~budget),
            reader.source.ack.eq(self.source.ack | self.abort | self.finish | budget),
            If(self.abort | self.finish | budget,NextState('DRAIN')))
        fsm.act('DRAIN',reader.source.ack.eq(1),
            If(reader.source.stb & reader.source.eop,NextState('DONE')))
        fsm.act('DONE',self.done.eq(1),NextState('IDLE'))
