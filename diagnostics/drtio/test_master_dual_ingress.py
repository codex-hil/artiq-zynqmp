# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen import ClockDomain
from migen.sim import run_simulation
from migen.genlib.resetsync import AsyncResetSynchronizer
from test_master_csr import Pair,CLOCKS,AXIMaster
from test_master_ps_cdc import FunctionalReset
from master_aux import GenesysMasterAux
from aux_controller_gray import GrayAuxController
from master_csr import GenesysMasterCSR
from master_dual_ingress import MasterDualIngress

class DualIngressTests(unittest.TestCase):
    def test_management_reset_while_target_b_unaccepted(self):
        d=Pair(now64=True)
        domains=('ps','sys','rtio_rx','rio','rio_phy')
        for name in domains+('management','control'):
            setattr(d.clock_domains,'cd_'+name,ClockDomain(name))
        d.submodules.aux=GenesysMasterAux(d.master,controller_type=GrayAuxController)
        d.submodules.csr=GenesysMasterCSR(d.time,d.ki,d.master,d.routing,aux=d.aux,ps_clock='ps')
        d.submodules.ingress=g=MasterDualIngress(d.csr.axi)
        for index,name in enumerate(domains):d.comb+=getattr(d,'cd_'+name).rst.eq(g.reset_out[index])
        management=AXIMaster(g.management_axi);target=AXIMaster(g.target_axi)
        base=g.management.BASE;length=d.csr.registers['aux_aux_tx_length']['address']
        state={'start':False,'pending':False,'reopened':False,'done':False}
        def poll(mask,value):
            for _ in range(100):
                status=yield from management.read(base+8)
                if status&mask==value:return
            self.fail('Management polling timeout')
        def open_target():
            yield from management.write(base+4,0)
            yield from poll(3,3)
            yield from management.write(base+4,2)
            yield from poll(5,4)
        def manager():
            self.assertEqual((yield from management.read(base)),g.management.IDENTITY)
            yield from open_target()
            state['start']=True
            for _ in range(2000):
                if state['pending']:break
                yield
            else:self.fail('Target never reached pending B')
            self.assertEqual((yield g.target_axi.b.valid),1)
            self.assertEqual((yield g.target_axi.b.ready),0)
            # Independent HPM1 AW must complete despite outstanding HPM0 B.
            yield from management.write(base+4,1)
            yield from poll(5,1)
            self.assertEqual((yield from management.read(base)),g.management.IDENTITY)
            yield from open_target()
            state['reopened']=True
            for _ in range(2000):
                if state['done']:return
                yield
            self.fail('Target did not recover')
        def requester():
            for _ in range(2000):
                if state['start']:break
                yield
            else:self.fail('No initial admission')
            a=g.target_axi
            yield a.aw.addr.eq(length);yield a.aw.size.eq(2);yield a.aw.len.eq(0)
            yield a.aw.burst.eq(1);yield a.aw.id.eq(0x1234)
            yield from target.handshake(a.aw)
            yield a.w.data.eq(68);yield a.w.strb.eq(15);yield a.w.last.eq(1)
            yield from target.handshake(a.w)
            for _ in range(300):
                if (yield a.b.valid):break
                yield
            else:self.fail('No target completion')
            self.assertEqual((yield d.aux.controller.transmitter.aux_tx_length.storage),17)
            state['pending']=True
            for _ in range(3000):
                if state['reopened']:break
                yield
            else:self.fail('Management could not reopen')
            for _ in range(30):
                self.assertEqual((yield a.b.valid),0)
                yield
            self.assertEqual((yield from target.read(length)),0)
            yield from target.write(length,12)
            self.assertEqual((yield from target.read(length)),12)
            state['done']=True
        clocks={name:14 for name in CLOCKS};clocks.update(ps=8,management=8,control=10)
        for name in domains:clocks['aux_release_'+name]=clocks[name]
        for name,crossing in d.csr.ps_cdc.crossings.items():
            periods=(14,8) if name in ('b','r') else (8,14)
            for domain,period in zip(crossing._fragment.clock_domains,periods):clocks[domain.name]=period
        run_simulation(d,{'ps':requester(),'management':manager()},clocks,
                       special_overrides={AsyncResetSynchronizer:FunctionalReset})
        self.assertTrue(state['done'])

if __name__=='__main__':unittest.main()
