"""Independent lab DMA counters, no AXI control; LGPL-3.0-or-later.

Not instantiated in any board target yet. TTL sampling is in rtio_rx; the
registered Gray counter crosses to sys. Reset/clock epochs must be unchanged
between snapshots; constrain this extra Gray crossing before physical use.
"""
from migen import Module,Signal,If
from misoc.interconnect.csr import CSRStatus
from monitor import GrayCounter


class LabDMAMetrics(Module):
    def __init__(self,memory,ttl_pad):
        self.ar=CSRStatus(32,name='dma_lab_ar_count')
        self.rlast=CSRStatus(32,name='dma_lab_rlast_count')
        self.edges=CSRStatus(32,name='dma_lab_ttl_edges')
        self.csrs=[self.ar,self.rlast,self.edges]
        self.sync += [If(memory.ar.valid & memory.ar.ready,self.ar.status.eq(self.ar.status+1)),
                      If(memory.r.valid & memory.r.ready & memory.r.last,
                         self.rlast.status.eq(self.rlast.status+1))]
        self.submodules.ttl_counter=counter=GrayCounter('rtio_rx')
        previous=Signal()
        self.sync.rtio_rx += previous.eq(ttl_pad)
        self.comb += [counter.enable.eq(ttl_pad ^ previous),self.edges.status.eq(counter.value)]
