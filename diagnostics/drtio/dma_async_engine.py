"""Native DMA decoder/CRI after running-clock AXI guard and raw CDC.

LGPL-3.0-or-later. Offline integration only. sys stays alive until done;
external abort must span a sys edge. CRI ownership belongs to the caller.
Completion means records admitted/drained, not all scheduled TTL events fired.
"""
from migen import Module,Signal,If,FSM,NextState,ClockDomainsRenamer,ResetInserter,Mux
from migen.genlib.cdc import MultiReg
from artiq.gateware.rtio.dma import RecordSlicer,TimeOffset,CRIMaster
from dma_memory_guard import DMAMemoryGuard
from dma_raw_cdc import DMARawCDC

class DMAConsumer(Module):
    def __init__(self,width):
        self.reset=Signal()
        self.offset=Signal(64)
        self.complete=Signal()
        self.submodules.slicer=s=ResetInserter()(RecordSlicer(width))
        self.submodules.offsetter=t=ResetInserter()(TimeOffset())
        self.submodules.master=m=ResetInserter()(CRIMaster())
        self.sink=s.sink;self.cri=m.cri
        self.comb += [s.reset.eq(self.reset),t.reset.eq(self.reset),m.reset.eq(self.reset),
            t.time_offset.storage.eq(self.offset),s.source.connect(t.sink),t.source.connect(m.sink)]
        self.finish=s.end_marker_found
        self.error=m.error.w;self.error_channel=m.error_channel.status
        self.error_timestamp=m.error_timestamp.status
        self.submodules.fsm=f=ResetInserter()(FSM(reset_state='FLOW'))
        self.comb += f.reset.eq(self.reset)
        f.act('FLOW',If(s.end_marker_found,NextState('FLUSH')))
        f.act('FLUSH',s.flush.eq(1),NextState('WAIT_EOP'))
        f.act('WAIT_EOP',If(m.sink.stb & m.sink.ack & m.sink.eop,NextState('WAIT_IDLE')))
        f.act('WAIT_IDLE',If(~m.busy,NextState('COMPLETE')))
        f.act('COMPLETE',self.complete.eq(1))

class AsyncSatelliteDMA(Module):
    # error bits: abort, AXI response, native underflow, native unreachable,
    # unaligned start. Payload error snapshot is valid only after done.
    def __init__(self,membus):
        if len(membus.r.data)!=64 or len(membus.ar.addr)<=7:
            raise ValueError('AsyncSatelliteDMA requires 64-bit memory and byte address width>7')
        self.start,self.abort=Signal(),Signal()
        self.address=Signal(len(membus.ar.addr));self.time_offset=Signal(64)
        self.active,self.done,self.failed=Signal(),Signal(),Signal()
        self.error=Signal(5);self.error_channel=Signal(24);self.error_timestamp=Signal(64)
        self.rejected_start=Signal()
        self.rtio_reset_request=Signal()
        self.submodules.guard=g=DMAMemoryGuard(membus)
        self.submodules.cross=q=DMARawCDC(len(membus.r.data))
        self.submodules.consumer=c=ClockDomainsRenamer('rtio_rx')(DMAConsumer(len(membus.r.data)))
        self.cri=c.cri
        address=Signal.like(self.address);offset=Signal(64);offset_rx=Signal(64)
        finish,complete=Signal(),Signal()
        abort_rx=Signal()
        err,ch,ts=Signal(2),Signal(24),Signal(64)
        self.specials += [MultiReg(self.error[0] | self.abort,abort_rx,'rtio_rx'),
            MultiReg(offset,offset_rx,'rtio_rx'),MultiReg(c.finish,finish),
            MultiReg(c.complete,complete),MultiReg(c.error,err),
            MultiReg(c.error_channel,ch),MultiReg(c.error_timestamp,ts)]
        self.submodules.fsm=f=FSM(reset_state='IDLE')
        sending=f.ongoing('SEND_EOP')
        reset_queue=(f.ongoing('IDLE') | f.ongoing('ABORT') | f.ongoing('DONE') | self.abort)
        self.comb += [self.active.eq(~f.ongoing('IDLE')),self.done.eq(f.ongoing('DONE')),
            self.failed.eq(self.error!=0),q.reset.eq(reset_queue),c.reset.eq(q.read_reset),
            c.offset.eq(offset_rx),q.source.connect(c.sink),
            self.rtio_reset_request.eq(abort_rx & q.read_reset),
            g.reader.base_address.storage.eq(address[7:]),
            q.sink.data.eq(Mux(sending,0,g.source.data)),
            q.sink.stb.eq(Mux(sending,1,g.source.stb)),q.sink.eop.eq(sending),
            g.source.ack.eq(q.sink.ack & ~sending)]
        self.sync += [If(self.start & self.active,self.rejected_start.eq(1)),
            If(f.ongoing('IDLE') & self.start,
                address.eq(self.address),offset.eq(self.time_offset),
                self.error.eq(Mux(self.abort,1,Mux(self.address[:7]!=0,16,0))),
                self.error_channel.eq(0),self.error_timestamp.eq(0),
                self.rejected_start.eq(self.abort | (self.address[:7]!=0))),
            If(self.active,self.error.eq(self.error | Mux(self.abort,1,0) |
                Mux(f.ongoing('RUN') & g.done & g.reader.wb_reader.bus_error.status,2,0) |
                Mux(f.ongoing('CAPTURE'),err<<2,0))),
            If(f.ongoing('CAPTURE'),self.error_channel.eq(ch),self.error_timestamp.eq(ts))]
        f.act('IDLE',If(self.start,
            If(self.abort | (self.address[:7]!=0),NextState('DONE')).Else(NextState('ARM'))))
        f.act('ARM',If(self.abort,NextState('ABORT')).Elif(q.write_ready,
            g.start.eq(1),NextState('RUN')))
        f.act('RUN',g.finish.eq(finish),g.abort.eq(self.abort),
            If(self.abort,NextState('ABORT')).Elif(g.done,NextState('SEND_EOP')))
        f.act('SEND_EOP',If(self.abort,NextState('ABORT')).Elif(q.sink.ack,NextState('WAIT_RX')))
        f.act('WAIT_RX',If(self.abort,NextState('ABORT')).Elif(complete,NextState('SETTLE')))
        # Consumer holds payload stable until queue reset in DONE. Two extra
        # sys edges after synchronized complete provide bundled-data settling.
        f.act('SETTLE',If(self.abort,NextState('ABORT')).Else(NextState('CAPTURE')))
        f.act('CAPTURE',If(self.abort,NextState('ABORT')).Else(NextState('DONE')))
        f.act('ABORT',g.abort.eq(1),If(~g.active | g.done,NextState('DONE')))
        f.act('DONE',NextState('IDLE'))
