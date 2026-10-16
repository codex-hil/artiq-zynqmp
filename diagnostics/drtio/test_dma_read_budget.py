"""Read budget conserves accepted/completed bursts with bounded addresses; LGPL-3.0-or-later."""
import sys
from pathlib import Path
import unittest
from migen import Module,passive
from migen.sim import run_simulation
from litex.soc.interconnect.axi import AXIInterface
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'boards/genesys_zu-5ev/1_gateware'))
sys.path.insert(0,str(ROOT/'tests'))
from dma_memory_guard import DMAMemoryGuard
from test_zynqmp_dma import AXIMemorySim

class ReadBudgetTests(unittest.TestCase):
    def exercise(self,limit,queue):
        d=Module();bus=AXIInterface(data_width=64,address_width=49,id_width=6)
        d.submodules.guard=g=DMAMemoryGuard(bus)
        memory=AXIMemorySim(bus,[0]*4096,max_queue=queue)
        requests=[];completed=[]
        @passive
        def monitor():
            while True:
                if (yield bus.ar.valid) and (yield bus.ar.ready):requests.append((yield bus.ar.addr))
                if (yield bus.r.valid) and (yield bus.r.ready) and (yield bus.r.last):completed.append(1)
                yield
        def run():
            yield g.source.ack.eq(1)
            yield g.max_bursts.eq(limit)
            yield from g.reader.base_address.write(1024)
            yield g.start.eq(1);yield;yield g.start.eq(0)
            for _ in range(5000):
                if (yield g.done):break
                yield
            else:self.fail('Read budget did not stop/drain')
            self.assertEqual((yield g.budget_error),1)
            self.assertEqual((yield g.failed),1)
            self.assertEqual(len(requests),len(completed))
            self.assertEqual(bool(requests),limit>=4)
            self.assertLessEqual(len(requests),limit)
            self.assertEqual(requests,list(range(1024,1024+128*len(requests),128)))
            if requests:self.assertLessEqual(requests[-1]+128,1024+limit*128)
        run_simulation(d,[run(),monitor(),memory.ar(),memory.r()])
    def test_bounded_reads_under_fast_ar_and_r_backpressure(self):
        for limit in (1,2,3,4,5,16,32):
            for queue in (1,12):
                with self.subTest(limit=limit,queue=queue):self.exercise(limit,queue)
