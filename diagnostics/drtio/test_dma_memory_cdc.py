"""Real AXI guard + async queue, stalled consumer/reset epochs; LGPL-3.0-or-later.

Reset uses the existing functional model, not silicon reset-release timing.
Clock-pause case postpones RX clock-driver transitions while sys keeps ticking;
this is simulated clock loss, not physical clock or reset-release qualification.
"""
import sys
from pathlib import Path
import unittest
from migen import Module,ClockDomain,passive
from migen.sim.core import Simulator
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.soc.interconnect.axi import AXIInterface
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'boards/genesys_zu-5ev/1_gateware'))
sys.path.insert(0,str(ROOT/'tests'))
from test_zynqmp_dma import AXIMemorySim
from test_aux_ps import FunctionalReset
from dma_memory_guard import DMAMemoryGuard
from dma_raw_cdc import DMARawCDC

class MemoryCDCTests(unittest.TestCase):
    def exercise(self,rx_period,short_reset=False,pause_rx=False):
        d=Module();d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
        bus=AXIInterface(data_width=64,address_width=49,id_width=6)
        d.submodules.guard=g=DMAMemoryGuard(bus)
        d.submodules.cross=q=DMARawCDC(depth=8)
        d.comb += g.source.connect(q.sink)
        memory=AXIMemorySim(bus,list(range(4096)),max_queue=3)
        accepted=[];seen=[];requests=[];last=[];rx_ticks=[];sim_box=[]
        @passive
        def sink():
            while True:
                rx_ticks.append(1)
                if (yield q.source.stb) and (yield q.source.ack):seen.append((yield q.source.data))
                yield
        @passive
        def monitor():
            while True:
                if (yield g.source.stb) and (yield g.source.ack):accepted.append((yield g.source.data))
                if (yield bus.ar.valid) and (yield bus.ar.ready):requests.append((yield bus.ar.addr))
                if (yield bus.r.valid) and (yield bus.r.ready) and (yield bus.r.last):last.append(1)
                yield
        def ready():
            for _ in range(200):
                if (yield q.write_ready):return
                yield
            self.fail('Queue epoch did not become ready')
        def done():
            for _ in range(1500):
                if (yield g.done):return
                yield
            self.fail('Memory did not drain independently of consumer')
        def run():
            yield q.source.ack.eq(0)
            for _ in range(8):yield
            yield q.reset.eq(0)
            yield from ready()
            yield from g.reader.base_address.write(0)
            yield g.start.eq(1);yield;yield g.start.eq(0)
            for _ in range(100):yield
            self.assertGreater(len(accepted),0)
            self.assertLess(len(accepted),32) # FIFO backpressure really occurred
            self.assertFalse(seen)
            if pause_rx:
                for name in ('rtio_rx','dma_read'):
                    sim_box[0].time.clocks[name].time_before_trans=10**9
                paused_ticks=len(rx_ticks)
            yield q.reset.eq(1);yield g.abort.eq(1)
            if short_reset:
                yield
                yield q.reset.eq(0)
            yield from done()
            self.assertEqual(len(requests),len(last))
            self.assertFalse(memory.queue)
            self.assertFalse(seen)
            self.assertEqual((yield g.failed),1)
            if pause_rx:
                self.assertEqual(len(rx_ticks),paused_ticks)
                self.assertEqual((yield q.write_ready),0)
                self.assertEqual((yield q.read_reset),1)
                for name in ('rtio_rx','dma_read'):
                    clock=sim_box[0].time.clocks[name]
                    clock.time_before_trans=clock.half_period
            for _ in range(8):yield
            yield g.abort.eq(0);yield q.reset.eq(0)
            yield from ready()
            accepted.clear()
            yield q.source.ack.eq(1)
            yield from g.reader.base_address.write(1024)
            yield g.start.eq(1);yield;yield g.start.eq(0)
            for _ in range(200):yield
            yield g.finish.eq(1)
            yield from done()
            for _ in range(200):yield
            self.assertEqual(seen,accepted)
            self.assertGreater(len(seen),16)
            self.assertEqual(seen,list(range(128,128+len(seen))))
            self.assertEqual(len(requests),len(last))
            self.assertEqual((yield g.failed),0)
        with Simulator(d,{'sys':[run(),monitor(),memory.ar(),memory.r()], 'dma_read':sink()},
            clocks={'sys':10,'rtio_rx':rx_period,'dma_write':10,'dma_read':rx_period},
            special_overrides={AsyncResetSynchronizer:FunctionalReset}) as sim:
            sim_box.append(sim)
            sim.run()
    def test_slower_consumer_reset_and_fresh_epoch(self):self.exercise((17,3))
    def test_faster_consumer_reset_and_fresh_epoch(self):self.exercise((7,1))

    def test_one_sys_edge_reset_cannot_reuse_stale_ready(self):self.exercise((17,3),short_reset=True)

    def test_actual_simulator_rx_clock_pause_does_not_block_axi_drain(self):self.exercise((17,3),pause_rx=True)
