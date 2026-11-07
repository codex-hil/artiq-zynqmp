# SPDX-License-Identifier: LGPL-3.0-or-later
"""Full AXI/CDC/native encoded AUX request-reply model, no hardware."""
import unittest
from migen import ClockDomain, passive
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.sim import run_simulation
from test_master_csr import Pair, CLOCKS, AXIMaster
from test_master_ps_cdc import FunctionalReset
from master_aux import GenesysMasterAux
from master_csr import GenesysMasterCSR
from aux_controller_gray import GrayAuxController

class AXILinkTests(unittest.TestCase):
    def test_ps_request_satellite_reply(self):
        d=Pair(now64=True)
        d.clock_domains.cd_ps=ClockDomain('ps')
        d.clock_domains.cd_sys=ClockDomain('sys')
        d.submodules.aux=GenesysMasterAux(d.master,controller_type=GrayAuxController)
        d.submodules.peer=GrayAuxController(d.satellite.link_layer)
        d.submodules.csr=GenesysMasterCSR(d.time,d.ki,d.master,d.routing,aux=d.aux,ps_clock='ps')
        m=AXIMaster(d.csr.axi)
        regs=d.csr.registers
        addr=lambda name:regs['aux_'+name]['address']
        packets=[[0x12340000+i*256+j for j in range(size)] for i,size in enumerate((1,3,17))]
        done={'peer':0,'overlap':False}
        @passive
        def peer():
            for index,words in enumerate(packets):
                for _ in range(8000):
                    if (yield d.peer.receiver.aux_rx_present.w):break
                    yield
                else:self.fail('Peer RX timeout')
                slot=yield from d.peer.receiver.aux_read_pointer.read()
                self.assertEqual(slot,index)
                actual=[]
                for j in range(len(words)):
                    actual.append((yield from d.peer.bus.read(2048+slot*256+j)))
                self.assertEqual(actual,words)
                yield from d.peer.receiver.aux_rx_present.write(1)
                for j,word in enumerate(words):
                    yield from d.peer.bus.write(j,word^0x55aa55aa)
                yield from d.peer.transmitter.aux_tx_length.write(len(words)*4)
                yield from d.peer.transmitter.aux_tx.write(1)
                done['peer']+=1
                for _ in range(1000):
                    if not (yield d.peer.transmitter.aux_tx.w):break
                    yield
        @passive
        def monitor():
            while True:
                axi=d.csr.axi
                ps_active=(yield axi.ar.valid) or (yield axi.r.ready) or (yield axi.aw.valid) or (yield axi.w.valid)
                if ps_active and ((yield d.master.link_layer.tx_aux_frame) or
                                  (yield d.satellite.link_layer.tx_aux_frame)):
                    done['overlap']=True
                yield
        def requester():
            for _ in range(80):yield
            for index,words in enumerate(packets):
                for j,word in enumerate(words):yield from m.write(0xa0010000+j*4,word)
                yield from m.write(addr('aux_tx_length'),len(words)*4)
                self.assertEqual((yield from m.read(addr('aux_tx_length'))),len(words)*4)
                yield from m.write(addr('aux_tx'),1)
                for _ in range(100):
                    if (yield from m.read(addr('aux_rx_present'))):break
                else:self.fail('PS RX timeout')
                slot=yield from m.read(addr('aux_read_pointer'))
                self.assertEqual(slot,index)
                actual=[]
                for j in range(len(words)):
                    actual.append((yield from m.read(0xa0012000+slot*1024+j*4)))
                self.assertEqual(actual,[word^0x55aa55aa for word in words])
                self.assertEqual((yield from m.read(addr('aux_rx_error'))),0)
                yield from m.write(addr('aux_rx_present'),1)
            self.assertEqual((yield from m.read(addr('aux_rx_present'))),0)
        clocks={key:14 for key in CLOCKS};clocks['ps']=8
        for name,crossing in d.csr.ps_cdc.crossings.items():
            periods=(14,8) if name in ('b','r') else (8,14)
            for domain,period in zip(crossing._fragment.clock_domains,periods):clocks[domain.name]=period
        run_simulation(d,{'ps':requester(),'sys':[peer(),monitor()]},clocks,
                       special_overrides={AsyncResetSynchronizer:FunctionalReset})
        self.assertEqual(done['peer'],3)
        self.assertTrue(done['overlap'])

if __name__=='__main__':unittest.main()
