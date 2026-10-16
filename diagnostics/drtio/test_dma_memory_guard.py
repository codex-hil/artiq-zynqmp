"""AXI guard simulation with a permanently stalled consumer; LGPL-3.0-or-later."""
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

class MemoryGuardTests(unittest.TestCase):
    def exercise(self,abort_at=30,response=0,finish=False,ar_delay=0,r_delay=0):
        dut=Module();bus=AXIInterface(data_width=64,address_width=49,id_width=6)
        dut.submodules.guard=g=DMAMemoryGuard(bus)
        memory=AXIMemorySim(bus,list(range(2048)),max_queue=3);memory.response=response
        requests=[];last=[];delivered=[];done=[]
        @passive
        def monitor():
            while True:
                if (yield bus.ar.valid) and (yield bus.ar.ready):requests.append((yield bus.ar.addr))
                if (yield bus.r.valid) and (yield bus.r.ready) and (yield bus.r.last):last.append(1)
                if (yield g.source.stb) and (yield g.source.ack):delivered.append((yield g.source.data))
                if (yield g.done):done.append(len(last))
                yield
        def run():
            yield g.source.ack.eq(0) # stopped/blocked consumer for the whole run
            yield from g.reader.base_address.write(0)
            yield g.start.eq(1);yield;yield g.start.eq(0)
            for _ in range(abort_at):yield
            yield (g.finish if finish else g.abort).eq(1)
            for _ in range(1500):
                if (yield g.done):break
                yield
            else:self.fail('AXI did not drain while consumer was stalled')
            self.assertEqual((yield g.failed),int(not finish or response!=0))
            self.assertEqual(len(requests),len(last))
            self.assertFalse(memory.queue)
            self.assertFalse(delivered)
            yield g.abort.eq(0);yield g.finish.eq(0)
            for _ in range(4):yield
            self.assertEqual((yield g.active),0)
            # New independent address epoch after completed drain.
            memory.response=0
            yield from g.reader.base_address.write(1024)
            yield g.start.eq(1);yield;yield g.start.eq(0)
            for _ in range(4):yield
            yield g.finish.eq(1)
            for _ in range(1500):
                if (yield g.done):break
                yield
            else:self.fail('Second epoch failed')
            self.assertEqual((yield g.failed),0)
            self.assertEqual(len(requests),len(last))
            yield
        @passive
        def ar_driver():
            for _ in range(ar_delay):yield
            yield from memory.ar()
        @passive
        def r_driver():
            for _ in range(r_delay):yield
            yield from memory.r()
        run_simulation(dut,[run(),monitor(),ar_driver(),r_driver()])
        self.assertEqual(len(done),2)
        self.assertIn(1024,requests)
    def test_abort_stalled_consumer_and_restart(self):self.exercise()
    def test_abort_before_first_response_and_restart(self):self.exercise(abort_at=0)
    def test_normal_finish_drains_even_without_consumer(self):self.exercise(finish=True)
    def test_bus_error_latched_and_new_epoch_clears(self):self.exercise(response=2,finish=True)

    def test_abort_waits_for_delayed_axi_ready_and_response(self):self.exercise(abort_at=0,ar_delay=60,r_delay=100)
