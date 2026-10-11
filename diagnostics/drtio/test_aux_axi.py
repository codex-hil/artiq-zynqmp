"""AXI error completion and stalled response regression; LGPL-3.0-or-later."""
import unittest
from migen import Module
from migen.sim import run_simulation
from litex.soc.interconnect.axi import AXILiteInterface
from litex.soc.interconnect import wishbone
from aux_axi import CheckedAXILite2Wishbone
from aux_bus import AuxAddressRouter


class AuxAXITest(unittest.TestCase):
    def test_errors_and_recovery(self):
        d=Module()
        axi=AXILiteInterface(data_width=32,address_width=40)
        csr=wishbone.Interface(data_width=32,address_width=40,addressing='word')
        aux=wishbone.Interface(data_width=32,address_width=40,addressing='word')
        d.submodules.router=r=AuxAddressRouter(csr,aux)
        d.submodules.bridge=CheckedAXILite2Wishbone(axi,r.bus,base_address=0xa0000000)
        d.comb += [csr.ack.eq(csr.cyc & csr.stb),csr.dat_r.eq(0x12345678),
                   aux.ack.eq(aux.cyc & aux.stb),aux.dat_r.eq(0xabcdef01)]
        def wait(signal):
            for _ in range(40):
                if (yield signal):return
                yield
            self.fail('AXI transaction did not complete')
        def test():
            for offset,expected in ((0x4000,2),(0,0),(0x100010000,2),(0x10000,0)):
                yield axi.ar.addr.eq(0xa0000000+offset)
                yield axi.ar.valid.eq(1)
                yield from wait(axi.ar.ready)
                yield
                yield axi.ar.valid.eq(0)
                yield from wait(axi.r.valid)
                for _ in range(5):
                    self.assertEqual((yield axi.r.resp),expected)
                    self.assertEqual((yield axi.r.valid),1)
                    yield
                yield axi.r.ready.eq(1)
                yield
                yield axi.r.ready.eq(0)
                yield
                yield axi.aw.addr.eq(0xa0000000+offset)
                yield axi.aw.valid.eq(1)
                yield axi.w.data.eq(0x31415926)
                yield axi.w.strb.eq(15)
                yield axi.w.valid.eq(1)
                yield from wait(axi.w.ready)
                self.assertEqual((yield axi.aw.ready),1)
                yield
                yield axi.aw.valid.eq(0)
                yield axi.w.valid.eq(0)
                yield from wait(axi.b.valid)
                for _ in range(5):
                    self.assertEqual((yield axi.b.resp),expected)
                    yield
                yield axi.b.ready.eq(1)
                yield
                yield axi.b.ready.eq(0)
                yield
        run_simulation(d,test())
