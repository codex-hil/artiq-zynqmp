"""Full AXI CSR/SRAM integration; functional reset model, LGPL-3.0-or-later."""
import unittest
from migen import Module
from migen.sim import run_simulation
from migen.genlib.resetsync import AsyncResetSynchronizer
from aux_ps import AuxPS


class FunctionalReset:
    # RTL simulation only: assertion/deassertion timing is not qualified here.
    @staticmethod
    def lower(special):
        m=Module()
        m.comb += special.cd.rst.eq(special.async_reset)
        return m


class AuxPSTest(unittest.TestCase):
    def test_full_axi_csr_sram_errors_and_reset(self):
        d=Module()
        d.submodules.ps=p=AuxPS()
        a=p.axi
        regs=p.memory_map()['registers']
        def wait(signal):
            for _ in range(100):
                if (yield signal):return
                yield
            self.fail('Full AXI did not complete')
        def read(address,expected_resp=0):
            yield a.ar.addr.eq(address)
            yield a.ar.id.eq(7)
            yield a.ar.len.eq(0)
            yield a.ar.size.eq(2)
            yield a.ar.burst.eq(1)
            yield a.ar.valid.eq(1)
            yield from wait(a.ar.ready)
            yield
            yield a.ar.valid.eq(0)
            yield from wait(a.r.valid)
            self.assertEqual((yield a.r.resp),expected_resp)
            self.assertEqual((yield a.r.id),7)
            self.assertEqual((yield a.r.last),1)
            data=(yield a.r.data)
            yield a.r.ready.eq(1)
            yield
            yield a.r.ready.eq(0)
            yield
            return data
        def write(address,value,expected_resp=0):
            yield a.aw.addr.eq(address)
            yield a.aw.id.eq(5)
            yield a.aw.len.eq(0)
            yield a.aw.size.eq(2)
            yield a.aw.burst.eq(1)
            yield a.aw.valid.eq(1)
            yield from wait(a.aw.ready)
            yield
            yield a.aw.valid.eq(0)
            yield a.w.data.eq(value)
            yield a.w.strb.eq(15)
            yield a.w.last.eq(1)
            yield a.w.valid.eq(1)
            yield from wait(a.w.ready)
            yield
            yield a.w.valid.eq(0)
            yield from wait(a.b.valid)
            self.assertEqual((yield a.b.resp),expected_resp)
            self.assertEqual((yield a.b.id),5)
            yield a.b.ready.eq(1)
            yield
            yield a.b.ready.eq(0)
            yield
        def test():
            self.assertEqual((yield from read(regs['in_reset']['address'])),1)
            yield p.reset.eq(0)
            for _ in range(10):yield
            base=p.memory_map()['aux_sram']['base']
            for i,value in ((0,0x12345678),(255,0xcafef00d)):
                yield from write(base+4*i,value)
                self.assertEqual((yield from read(base+4*i)),value)
            yield from write(regs['aux_tx_length']['address'],68)
            self.assertEqual((yield from read(regs['aux_tx_length']['address'])),68)
            yield from read(p.BASE+0x4000,2)
            yield from write(p.BASE+0x14000,123,2)
            yield from read(p.BASE+0x100010000,2)
            self.assertEqual((yield from read(base)),0x12345678)
            yield p.reset.eq(1)
            for _ in range(10):yield
            self.assertEqual((yield from read(regs['in_reset']['address'])),1)
            self.assertEqual((yield from read(regs['aux_tx_length']['address'])),0)
            yield p.reset.eq(0)
            for _ in range(10):yield
            self.assertEqual((yield from read(regs['in_reset']['address'])),0)
            yield from write(regs['aux_tx_length']['address'],4)
            self.assertEqual((yield from read(regs['aux_tx_length']['address'])),4)
        run_simulation(d,test(),clocks={'sys':8,'gth_tx':10,'gth_rx':12,
            'aux_sys':8,'aux_tx':10,'aux_rx':12},
            special_overrides={AsyncResetSynchronizer:FunctionalReset})
