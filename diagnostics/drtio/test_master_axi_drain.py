# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen import Module
from migen.sim import run_simulation
from litex.soc.interconnect.axi import AXIInterface
from master_axi_drain import MasterAXIDrain

class DrainTests(unittest.TestCase):
    def exercise(self,first):
        d=Module();t=AXIInterface(data_width=32,address_width=40,id_width=16)
        d.submodules.bridge=b=MasterAXIDrain(t);a=b.axi
        def step(n=1):
            for _ in range(n):yield
        def accept(channel):
            yield channel.valid.eq(1)
            yield
            self.assertEqual((yield channel.ready),1)
            yield
            yield channel.valid.eq(0)
            yield
        def test():
            yield b.stop.eq(0);yield
            yield a.aw.addr.eq(0xa0000010);yield a.aw.id.eq(17)
            yield a.aw.size.eq(2);yield a.aw.len.eq(0)
            yield a.w.data.eq(0x12345678);yield a.w.strb.eq(15);yield a.w.last.eq(1)
            yield from accept(getattr(a,first))
            yield b.stop.eq(1);yield from step(3)
            missing='w' if first=='aw' else 'aw'
            self.assertEqual((yield getattr(a,missing).ready),1)
            self.assertEqual((yield a.ar.ready),0)
            # First request remains VALID and stable while target backpressures.
            self.assertEqual((yield getattr(t,first).valid),1)
            yield from accept(getattr(a,missing))
            for _ in range(5):
                self.assertEqual((yield t.aw.valid),1)
                self.assertEqual((yield t.aw.addr),0xa0000010)
                self.assertEqual((yield t.w.valid),1)
                self.assertEqual((yield t.w.data),0x12345678)
                self.assertEqual((yield a.aw.ready),0)
                self.assertEqual((yield a.w.ready),0)
                yield
            yield t.aw.ready.eq(1);yield t.w.ready.eq(1);yield from step(3)
            self.assertEqual((yield t.aw.valid),0);self.assertEqual((yield t.w.valid),0)
            yield t.b.id.eq(17);yield t.b.resp.eq(0);yield t.b.valid.eq(1)
            for _ in range(6):
                if _:
                    self.assertEqual((yield a.b.valid),1)
                    self.assertEqual((yield a.b.id),17)
                yield
            yield a.b.ready.eq(1);yield from step(2)
            yield t.b.valid.eq(0);yield a.b.ready.eq(0);yield from step(2)
            self.assertEqual((yield b.idle),1)
            self.assertEqual((yield a.aw.ready),0)
            self.assertEqual((yield a.w.ready),0)
        run_simulation(d,test())
    def test_aw_first_stop_then_w_drain(self):self.exercise('aw')
    def test_w_first_stop_then_aw_drain(self):self.exercise('w')
    def test_read_response_retained_after_stop(self):
        d=Module();t=AXIInterface(data_width=32,address_width=40,id_width=16)
        d.submodules.bridge=b=MasterAXIDrain(t);a=b.axi
        def test():
            yield b.stop.eq(0);yield a.ar.addr.eq(0xa0000020);yield a.ar.valid.eq(1)
            for _ in range(3):yield
            yield a.ar.valid.eq(0);yield b.stop.eq(1)
            for _ in range(4):
                self.assertEqual((yield t.ar.valid),1);yield
            yield t.ar.ready.eq(1)
            for _ in range(3):yield
            yield t.r.valid.eq(1);yield t.r.data.eq(0xabcdef);yield t.r.last.eq(1)
            yield
            for _ in range(6):
                self.assertEqual((yield a.r.valid),1)
                self.assertEqual((yield a.r.data),0xabcdef);yield
            yield a.r.ready.eq(1)
            for _ in range(2):yield
            yield t.r.valid.eq(0)
            yield
            self.assertEqual((yield b.idle),1)
            self.assertEqual((yield a.ar.ready),0)
        run_simulation(d,test())
if __name__=='__main__':unittest.main()
