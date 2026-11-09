# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen import Module,ClockDomain
from migen.sim import run_simulation
from litex.soc.interconnect.axi import AXIInterface
from master_axi_shape_guard import MasterAXIShapeGuard

class ShapeTests(unittest.TestCase):
    def test_nine_bad_shapes_not_accepted_or_forwarded_fault_sticky(self):
        cases=[('aw','len',1),('ar','len',1),('aw','size',1),('ar','size',1),
               ('aw','addr',3),('ar','addr',3),('w','last',0),('aw','lock',1),('ar','burst',2)]
        for name,field,value in cases:
            with self.subTest(channel=name,field=field):
                d=Module();d.clock_domains.cd_sys=ClockDomain('sys')
                t=AXIInterface(data_width=32,address_width=40,id_width=16)
                d.submodules.guard=g=MasterAXIShapeGuard(t);a=g.axi
                def test():
                    yield g.stop.eq(0)
                    for n in ('aw','ar'):
                        yield getattr(a,n).size.eq(2);yield getattr(a,n).burst.eq(1)
                    yield a.w.last.eq(1)
                    yield getattr(getattr(a,name),field).eq(value)
                    yield getattr(a,name).valid.eq(1);yield
                    for _ in range(5):
                        self.assertEqual((yield getattr(a,name).ready),0)
                        self.assertEqual((yield getattr(t,name).valid),0);yield
                    self.assertEqual((yield g.fault),1)
                    yield getattr(a,name).valid.eq(0)
                    for _ in range(8):yield
                    self.assertEqual((yield g.fault),1)
                    yield d.cd_sys.rst.eq(1)
                    for _ in range(3):yield
                    yield d.cd_sys.rst.eq(0);yield
                    self.assertEqual((yield g.fault),0)
                run_simulation(d,test())
    def test_fault_does_not_withdraw_pending_b_or_block_accepted_missing_half(self):
        d=Module();t=AXIInterface(data_width=32,address_width=40,id_width=16)
        d.submodules.guard=g=MasterAXIShapeGuard(t);a=g.axi
        def test():
            yield g.stop.eq(0);yield a.aw.size.eq(2);yield a.aw.id.eq(17);yield a.aw.addr.eq(0xa0000010)
            yield a.aw.valid.eq(1)
            for _ in range(3):yield
            yield a.aw.valid.eq(0)
            # Malformed independent AR faults after AW was accepted.
            yield a.ar.size.eq(1);yield a.ar.valid.eq(1)
            for _ in range(4):yield
            yield a.ar.valid.eq(0)
            self.assertEqual((yield g.fault),1)
            # Complementary valid W is still accepted for the old AW.
            yield a.w.data.eq(12);yield a.w.last.eq(1);yield a.w.valid.eq(1)
            yield
            self.assertEqual((yield a.w.ready),1)
            yield;yield a.w.valid.eq(0);yield
            self.assertEqual((yield t.aw.valid),1);self.assertEqual((yield t.w.valid),1)
            yield t.aw.ready.eq(1);yield t.w.ready.eq(1)
            for _ in range(3):yield
            yield t.b.valid.eq(1);yield t.b.id.eq(17)
            yield
            for _ in range(8):
                self.assertEqual((yield a.b.valid),1)
                self.assertEqual((yield a.b.id),17);yield
            yield a.b.ready.eq(1)
            for _ in range(2):yield
            yield t.b.valid.eq(0)
            yield
            self.assertEqual((yield g.idle),1)
            self.assertEqual((yield g.fault),1)
            self.assertEqual((yield a.aw.ready),0)
        run_simulation(d,test())
if __name__=='__main__':unittest.main()
