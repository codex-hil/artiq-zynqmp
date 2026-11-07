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
    active_reset=False
    sequenced=False
    def test_ps_request_satellite_reply(self):
        d=Pair(now64=True)
        d.clock_domains.cd_ps=ClockDomain('ps')
        d.clock_domains.cd_sys=ClockDomain('sys')
        if self.active_reset:
            for name in ('rtio_rx','rio','rio_phy'):
                setattr(d.clock_domains,'cd_'+name,ClockDomain(name))
        d.submodules.aux=GenesysMasterAux(d.master,controller_type=GrayAuxController)
        d.submodules.peer=GrayAuxController(d.satellite.link_layer)
        d.submodules.csr=GenesysMasterCSR(d.time,d.ki,d.master,d.routing,aux=d.aux,ps_clock='ps')
        if self.sequenced:
            from migen import ClockDomainsRenamer, Signal
            from migen.genlib.cdc import MultiReg
            from aux_reset_control import AuxResetControl
            from aux_reset_domains import AuxResetDomains
            from master_axi_admission import MasterAXIAdmission
            d.clock_domains.cd_control=ClockDomain('control')
            d.submodules.reset_control=c=ClockDomainsRenamer('control')(AuxResetControl(5))
            d.submodules.reset_domains=r=AuxResetDomains(
                ('ps','sys','rtio_rx','rio','rio_phy'),control='control')
            d.comb += [r.request.eq(c.reset),c.domain_ready.eq(r.ready)]
            for index,name in enumerate(('ps','sys','rtio_rx','rio','rio_phy')):
                d.comb += getattr(d,'cd_'+name).rst.eq(r.reset_out[index])
            admitted_ps=Signal()
            d.specials+=MultiReg(c.admit,admitted_ps,'ps')
            d.submodules.admission=g=MasterAXIAdmission(d.csr.axi)
            d.comb += g.enable.eq(admitted_ps & ~r.reset_out[0])
            m=AXIMaster(g.axi)
        else:
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
        def release():
            yield c.request.eq(0)
            yield c.requester_abandoned.eq(0)
            for _ in range(12):yield
            yield c.requester_abandoned.eq(1)
            for _ in range(300):
                if (yield g.enable):return
                yield
            self.fail('Sequenced reset failed to admit PS')
        def requester():
            if self.sequenced:
                self.assertEqual((yield g.enable),0)
                for _ in range(24):yield
                yield from release()
            for _ in range(80):yield
            if self.active_reset:
                # Trigger a long frame; AXI B is already accepted before reset.
                for j in range(64):yield from m.write(0xa0010000+j*4,0xdead0000+j)
                yield from m.write(addr('aux_tx_length'),256)
                yield from m.write(addr('aux_tx'),1)
                for _ in range(300):
                    if (yield d.master.link_layer.tx_aux_frame):break
                    yield
                else:self.fail('No active TX to interrupt')
                for _ in range(8):yield
                self.assertEqual((yield d.master.link_layer.tx_aux_frame),1)
                # Whole modeled endpoint/control domains, input clocks remain live.
                if self.sequenced:
                    yield c.request.eq(1)
                    for _ in range(40):yield
                    self.assertEqual((yield g.enable),0)
                    self.assertEqual((yield r.ready),0)
                    yield from release()
                else:
                    domains=[d.cd_ps,d.cd_sys,d.cd_rtio_rx,d.cd_rio,d.cd_rio_phy]
                    for domain in domains:yield domain.rst.eq(1)
                    for _ in range(40):yield
                    for domain in domains:yield domain.rst.eq(0)
                for _ in range(100):yield
                self.assertEqual((yield from m.read(addr('aux_tx'))),0)
                self.assertEqual((yield from m.read(addr('aux_tx_length'))),0)
                self.assertEqual((yield from m.read(addr('aux_rx_present'))),0)
                self.assertEqual((yield d.peer.receiver.aux_rx_present.w),0)
                self.assertEqual(done['peer'],0)
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
        if self.sequenced:
            clocks['control']=10
            for name in ('ps','sys','rtio_rx','rio','rio_phy'):
                clocks['aux_release_'+name]=8 if name=='ps' else 14
        run_simulation(d,{'ps':requester(),'sys':[peer(),monitor()]},clocks,
                       special_overrides={AsyncResetSynchronizer:FunctionalReset})
        self.assertEqual(done['peer'],3)
        self.assertTrue(done['overlap'])

class ActiveResetAXILinkTests(AXILinkTests):
    active_reset=True

class SequencedResetAXILinkTests(ActiveResetAXILinkTests):
    sequenced=True

if __name__=='__main__':unittest.main()
