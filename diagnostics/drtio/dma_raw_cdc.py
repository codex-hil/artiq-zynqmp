"""DMA raw-word async queue with coordinated reset epochs; LGPL-3.0-or-later.

sys always runs, rtio_rx may stall. reset requests must span a sys edge.
The consumer/decoder must share this reset; this queue never resets AXI state.
Physical Gray constraints and reset-release timing remain integration duties.
"""
from migen import Module,Signal,ClockDomain,ClockSignal,ClockDomainsRenamer,Cat,If
from migen.genlib.cdc import MultiReg
from migen.genlib.fifo import AsyncFIFOBuffered
from migen.genlib.resetsync import AsyncResetSynchronizer
from misoc.interconnect import stream

class DMARawCDC(Module):
    def __init__(self,width=64,depth=16):
        if depth<4 or depth&(depth-1):raise ValueError('Power-of-two depth>=4 required')
        self.reset=Signal(reset=1)
        self.write_ready=Signal()
        self.read_reset=Signal(reset=1)
        self.sink=stream.Endpoint([('data',width)])
        self.source=stream.Endpoint([('data',width)])
        self.clock_domains.cd_dma_write=ClockDomain('dma_write')
        self.clock_domains.cd_dma_read=ClockDomain('dma_read')
        release=Signal()
        internal_reset=Signal()
        read_ready,read_seen=Signal(),Signal()
        reset_edges=Signal(3)
        reset_ack,reset_ack_sys=Signal(),Signal()
        self.sync.rtio_rx += If(internal_reset,
            If(reset_edges!=7,reset_edges.eq(reset_edges+1))).Else(reset_edges.eq(0))
        self.comb += reset_ack.eq(reset_edges==7)
        self.specials += [MultiReg(read_ready,read_seen,'sys'),
                          MultiReg(reset_ack,reset_ack_sys,'sys')]
        # Pointer synchronizer stages are reset-less. Keep BOTH FIFO domains
        # reset through seven RX edges so they settle to zero; merely seeing
        # read_ready=0 after one edge can create phantom buffered reads.
        # Waiting for reset_ack to drop also prevents writing into the window
        # in which an old reset acknowledgement could still be synchronized.
        self.sync += If(self.reset,release.eq(0)).Elif(reset_ack_sys,release.eq(1))
        self.comb += [internal_reset.eq(self.reset | ~release),
            self.cd_dma_write.clk.eq(ClockSignal('sys')),
            self.cd_dma_read.clk.eq(ClockSignal('rtio_rx')),
            self.read_reset.eq(self.cd_dma_read.rst)]
        for domain in (self.cd_dma_write,self.cd_dma_read):
            self.specials += AsyncResetSynchronizer(domain,internal_reset)
        wp,rp=Signal(2),Signal(2)
        self.sync.dma_write += wp.eq(Cat(1,wp[0]))
        self.sync.dma_read += rp.eq(Cat(1,rp[0]))
        self.comb += [read_ready.eq(rp[1]),
            self.write_ready.eq(~internal_reset & wp[1] & read_seen & ~reset_ack_sys)]
        self.submodules.fifo=f=ClockDomainsRenamer({'write':'dma_write','read':'dma_read'})(AsyncFIFOBuffered(width,depth))
        self.comb += [f.din.eq(self.sink.data),
            self.sink.ack.eq(self.write_ready & f.writable),
            f.we.eq(self.sink.stb & self.sink.ack),
            self.source.data.eq(f.dout),
            self.source.stb.eq(~internal_reset & rp[1] & f.readable),
            f.re.eq(self.source.stb & self.source.ack),self.source.eop.eq(0)]
