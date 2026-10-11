"""PS aperture decode and no-alias negative controls; LGPL-3.0-or-later."""
import unittest
from migen import Module
from migen.sim import run_simulation
from litex.soc.interconnect import wishbone as lx
from misoc.interconnect import wishbone as ms
from aux_bus import AuxAddressRouter, AUX_OFFSET, AUX_BYTES, CSR_BYTES


class AuxBusTest(unittest.TestCase):
    def test_routes_boundaries_and_rejects_aliases(self):
        d = Module()
        csr, aux = lx.Interface(data_width=32, address_width=40, addressing='word'), ms.Interface()
        d.submodules.router = r = AuxAddressRouter(csr, aux)
        d.comb += [csr.ack.eq(csr.cyc & csr.stb), csr.dat_r.eq(0xc5c5),
                   aux.ack.eq(aux.cyc & aux.stb), aux.dat_r.eq(0xa0a0)]

        def test():
            for address, target in [(0,'csr'), (CSR_BYTES-4,'csr'),
                                    (AUX_OFFSET,'aux'),
                                    (AUX_OFFSET+AUX_BYTES-4,'aux'),
                                    (CSR_BYTES,None), (AUX_OFFSET-4,None),
                                    (AUX_OFFSET+AUX_BYTES,None),
                                    (0x100000000+AUX_OFFSET,None)]:
                for write in (0,1):
                    yield r.bus.adr.eq(address//4)
                    yield r.bus.we.eq(write)
                    yield r.bus.dat_w.eq(0x12345678)
                    yield r.bus.sel.eq(5)
                    yield r.bus.cyc.eq(1)
                    yield r.bus.stb.eq(1)
                    yield
                    self.assertEqual((yield r.bus.err), target is None)
                    self.assertEqual((yield r.bus.ack), target is not None)
                    self.assertEqual((yield csr.cyc), target == 'csr')
                    self.assertEqual((yield aux.cyc), target == 'aux')
                    if target:
                        s = csr if target == 'csr' else aux
                        self.assertEqual((yield s.we),write)
                        self.assertEqual((yield s.dat_w),0x12345678)
                        self.assertEqual((yield s.sel),5)
                        self.assertEqual((yield s.adr),
                                         (address-(AUX_OFFSET if target=='aux' else 0))//4)
                    yield r.bus.cyc.eq(0)
                    yield r.bus.stb.eq(0)
                    yield
                    self.assertEqual((yield r.bus.err),0)
                    self.assertEqual((yield r.bus.ack),0)
        run_simulation(d,test())

    def test_upstream_aux_sram_roundtrip(self):
        from aux_endpoint import AuxEndpoint
        d = Module()
        d.submodules.endpoint = e = AuxEndpoint()
        csr = lx.Interface(data_width=32, address_width=40, addressing='word')
        d.submodules.router = r = AuxAddressRouter(csr, e.aux.bus)
        # No link transmission: this validates actual PS-side SRAM accesses.
        d.comb += [csr.ack.eq(csr.cyc & csr.stb), csr.dat_r.eq(0xc5c5)]
        def test():
            for index, data in ((0,0x12345678),(1,0xa5a55a5a),(255,0xc001cafe)):
                yield from r.bus.write(AUX_OFFSET//4+index,data)
            for index, data in ((0,0x12345678),(1,0xa5a55a5a),(255,0xc001cafe)):
                self.assertEqual((yield from r.bus.read(AUX_OFFSET//4+index)),data)
            self.assertEqual((yield from r.bus.read(0)),0xc5c5)
            self.assertEqual((yield from r.bus.read((AUX_OFFSET+8192)//4)),0)
        run_simulation(d, test(), clocks={'sys':8,'gth_tx':10,'rtio_rx':12})
