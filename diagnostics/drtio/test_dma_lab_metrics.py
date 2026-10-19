"""Independent handshake/edge counts, simulation only; LGPL-3.0-or-later."""
import unittest
from migen import Module,Signal,ClockDomain
from migen.sim import run_simulation
from litex.soc.interconnect.axi import AXIInterface
from dma_lab_metrics import LabDMAMetrics

class MetricsTests(unittest.TestCase):
    def test_handshakes_not_valid_levels_and_both_ttl_edges(self):
        d=Module();d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
        bus=AXIInterface();pad=Signal()
        d.submodules.metrics=m=LabDMAMetrics(bus,pad)
        def rx():
            for _ in range(5):yield
            for state in [1,0,1,0,1,0]:
                yield pad.eq(state)
                for _ in range(3):yield
            for _ in range(8):yield
        def run():
            yield bus.ar.valid.eq(1);yield bus.ar.ready.eq(0)
            yield bus.r.valid.eq(1);yield bus.r.ready.eq(0);yield bus.r.last.eq(1)
            for _ in range(4):yield
            yield bus.ar.ready.eq(1)
            for _ in range(3):yield
            yield bus.ar.ready.eq(0)
            yield bus.r.ready.eq(1);yield bus.r.last.eq(0)
            for _ in range(2):yield
            yield bus.r.last.eq(1)
            for _ in range(3):yield
            yield bus.r.ready.eq(0)
            for _ in range(30):yield
            self.assertEqual((yield m.ar.status),3)
            self.assertEqual((yield m.rlast.status),3)
            self.assertEqual((yield m.edges.status),6)
        run_simulation(d,{'sys':run(),'rtio_rx':rx()},clocks={'sys':10,'rtio_rx':(8,1)})
