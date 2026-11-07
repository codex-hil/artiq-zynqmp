# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen.sim import run_simulation
from test_master_csr import AXIMaster, Pair, CLOCKS
from master_csr import GenesysMasterCSR
from master_aux import GenesysMasterAux
from aux_controller_gray import GrayAuxController

class AuxMapTests(unittest.TestCase):
    def test_profile_aux_csrs_and_sram_axi(self):
        d=Pair(now64=True)
        d.submodules.aux=GenesysMasterAux(d.master,controller_type=GrayAuxController)
        d.submodules.csr=GenesysMasterCSR(d.time,d.ki,d.master,d.routing,aux=d.aux)
        m=AXIMaster(d.csr.axi)
        reg=d.csr.registers
        self.assertEqual(reg['aux_aux_tx_length']['address'],0xa0002000)
        self.assertEqual(reg['aux_aux_read_pointer']['address'],0xa0002010)
        def test():
            self.assertEqual((yield from m.read(reg['profile_identity']['address'])),GenesysMasterCSR.IDENTITY)
            self.assertEqual((yield from m.read(reg['aux_aux_rx_present']['address'])),0)
            self.assertEqual((yield from m.read(reg['aux_aux_rx_error']['address'])),0)
            yield from m.write(0xa0010000,0x12345678)
            self.assertEqual((yield from m.read(0xa0010000)),0x12345678)
            yield from m.write(0xa00103fc,0xabcdef01)
            self.assertEqual((yield from m.read(0xa00103fc)),0xabcdef01)
            self.assertEqual((yield from m.read(reg['aux_aux_tx_length']['address'])),0)
            self.assertEqual((yield from m.read(reg['profile_identity']['address'])),GenesysMasterCSR.IDENTITY)
            for length in (0,4,12,68,256,1020,1024):
                yield from m.write(reg['aux_aux_tx_length']['address'],length)
                self.assertEqual((yield from m.read(reg['aux_aux_tx_length']['address'])),length)
                self.assertEqual((yield d.aux.controller.transmitter.aux_tx_length.storage),length//4)
            self.assertEqual((yield from m.read(reg['aux_aux_tx']['address'])),0)
            a=d.csr.axi
            for address in (0x9ffffffc,0xa0002800,0xa0004000,0xa0014000,0x1a0010000):
                yield a.ar.addr.eq(address)
                yield a.ar.size.eq(2)
                yield a.ar.len.eq(0)
                yield a.ar.burst.eq(1)
                yield a.ar.id.eq(0x4321)
                yield from m.handshake(a.ar)
                for _ in range(100):
                    if (yield a.r.valid):break
                    yield
                else:self.fail('AUX map hole did not complete')
                self.assertEqual((yield a.r.resp),2)
                self.assertEqual((yield a.r.id),0x4321)
                yield a.r.ready.eq(1)
                yield
                yield a.r.ready.eq(0)
                yield
                self.assertEqual((yield from m.read(0xa0010000)),0x12345678)
        run_simulation(d,test(),CLOCKS)

if __name__=='__main__':unittest.main()
