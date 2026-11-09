# SPDX-License-Identifier: LGPL-3.0-or-later
"""One R/W concurrency and negative transfer-shape controls, no hardware proof."""
import unittest
from migen import Module
from migen.sim import run_simulation
from litex.soc.interconnect.axi import AXIInterface
from master_axi_drain import MasterAXIDrain

class ConcurrentTests(unittest.TestCase):
    def exercise(self,first):
        d=Module();t=AXIInterface(data_width=32,address_width=40,id_width=16)
        d.submodules.bridge=b=MasterAXIDrain(t);a=b.axi
        def cycles(n):
            for _ in range(n):yield
        def test():
            yield b.stop.eq(0)
            yield a.aw.addr.eq(0xa0000010);yield a.aw.id.eq(17);yield a.aw.size.eq(2)
            yield a.w.data.eq(68);yield a.w.last.eq(1);yield a.w.strb.eq(15)
            yield a.ar.addr.eq(0xa0000020);yield a.ar.id.eq(29);yield a.ar.size.eq(2)
            for n in ('aw','w','ar'):yield getattr(a,n).valid.eq(1)
            yield from cycles(2)
            for n in ('aw','w','ar'):yield getattr(a,n).valid.eq(0)
            yield b.stop.eq(1);yield from cycles(3)
            self.assertEqual((yield t.aw.id),17);self.assertEqual((yield t.ar.id),29)
            for n in ('aw','w','ar'):
                self.assertEqual((yield getattr(t,n).valid),1)
                yield getattr(t,n).ready.eq(1)
            yield from cycles(3)
            yield t.b.id.eq(17);yield t.b.resp.eq(2);yield t.b.valid.eq(1)
            yield t.r.id.eq(29);yield t.r.data.eq(0xabcdef);yield t.r.resp.eq(0)
            yield t.r.last.eq(1);yield t.r.valid.eq(1)
            yield from cycles(2)
            for _ in range(7):
                self.assertEqual((yield a.b.valid),1);self.assertEqual((yield a.b.id),17)
                self.assertEqual((yield a.b.resp),2)
                self.assertEqual((yield a.r.valid),1);self.assertEqual((yield a.r.id),29)
                self.assertEqual((yield a.r.data),0xabcdef)
                self.assertEqual((yield b.idle),0);yield
            second='r' if first=='b' else 'b'
            yield getattr(a,first).ready.eq(1);yield
            yield
            yield getattr(t,first).valid.eq(0);yield getattr(a,first).ready.eq(0)
            yield from cycles(3)
            self.assertEqual((yield b.idle),0)
            self.assertEqual((yield getattr(a,second).valid),1)
            yield getattr(a,second).ready.eq(1);yield
            yield
            yield getattr(t,second).valid.eq(0);yield from cycles(3)
            self.assertEqual((yield b.idle),1)
            for n in ('aw','w','ar'):self.assertEqual((yield getattr(a,n).ready),0)
        run_simulation(d,test())
    def test_b_drains_before_r(self):self.exercise('b')
    def test_r_drains_before_b(self):self.exercise('r')
    def test_unsupported_shapes_are_forwarded_not_rejected(self):
        # Negative controls: current candidate has a caller precondition only.
        for name,field,value in [('aw','len',1),('ar','len',1),('aw','size',1),
                                 ('ar','size',1),('aw','addr',3),('ar','addr',3),('w','last',0)]:
            with self.subTest(channel=name,field=field):
                d=Module();t=AXIInterface(data_width=32,address_width=40,id_width=16)
                d.submodules.bridge=b=MasterAXIDrain(t);a=b.axi
                def test():
                    yield b.stop.eq(0)
                    yield getattr(getattr(a,name),field).eq(value)
                    yield getattr(a,name).valid.eq(1)
                    for _ in range(3):yield
                    yield getattr(a,name).valid.eq(0)
                    yield
                    self.assertEqual((yield getattr(t,name).valid),1)
                    self.assertEqual((yield getattr(getattr(t,name),field)),value)
                run_simulation(d,test())
if __name__=='__main__':unittest.main()
