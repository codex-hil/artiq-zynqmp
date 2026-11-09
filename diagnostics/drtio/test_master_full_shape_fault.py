# SPDX-License-Identifier: LGPL-3.0-or-later
# Test-local buffered drain integration; no cancellation or physical signoff.
import unittest
from migen import ClockDomain,Signal,ClockDomainsRenamer
from migen.genlib.cdc import MultiReg
from migen.sim import Simulator
from migen.genlib.resetsync import AsyncResetSynchronizer
from test_master_csr import Pair,CLOCKS,AXIMaster
from test_master_ps_cdc import FunctionalReset
from master_aux import GenesysMasterAux
from aux_controller_gray import GrayAuxController
from master_csr import GenesysMasterCSR
from master_dual_ingress import MasterDualIngress

from master_rx_progress import MasterRXProgress
from master_axi_shape_guard import MasterAXIShapeGuard

class FullShapeFaultTests(unittest.TestCase):
    def exercise(self,malformed):
        d=Pair(now64=True)
        domains=('ps','sys','rtio_rx','rio','rio_phy')
        for name in domains+('management','control'):
            setattr(d.clock_domains,'cd_'+name,ClockDomain(name))
        d.submodules.aux=GenesysMasterAux(d.master,controller_type=GrayAuxController)
        d.submodules.csr=GenesysMasterCSR(d.time,d.ki,d.master,d.routing,aux=d.aux,ps_clock='ps')
        shape_fault=Signal()
        d.submodules.ingress=g=MasterDualIngress(d.csr.axi,shape_fault=shape_fault)
        for index,name in enumerate(domains):d.comb+=getattr(d,'cd_'+name).rst.eq(g.reset_out[index])
        d.submodules.progress=p=MasterRXProgress(32)
        d.submodules.fault_gate=f=ClockDomainsRenamer('ps')(MasterAXIShapeGuard(g.target_axi))
        qualified=Signal()
        d.specials+=MultiReg(p.allowed,qualified,'ps')
        d.comb += [p.rearm.eq(g.coordinator.reset),
                   f.stop.eq(~qualified | g.reset_out[0]),shape_fault.eq(f.fault)]
        management=AXIMaster(g.management_axi);target=AXIMaster(f.axi)
        base=g.management.BASE;length=d.csr.registers['aux_aux_tx_length']['address']
        state={'start':False,'pending':False,'reopened':False,'done':False,'stop':False,'suppressed':0,'withdraw':False}
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
            for _ in range(100):
                if not (yield f.stop):break
                yield
            else:self.fail('Initial progress admission failed')
            state['start']=True
            for _ in range(2000):
                if state['pending']:break
                yield
            else:self.fail('Target never reached pending B')
            for _ in range(40):
                if (yield from management.read(base+12))==1:break
            else:self.fail('Shape fault not visible through HPM1')
            self.assertEqual((yield getattr(f.axi,malformed).ready),0)
            self.assertEqual((yield g.target_axi.w.valid),0)
            self.assertEqual((yield g.target_axi.aw.valid),0)
            self.assertEqual((yield d.aux.controller.transmitter.aux_tx_length.storage),0)
            self.assertEqual((yield from management.read(base)),g.management.IDENTITY)
            yield from management.write(base+4,1)
            yield from poll(5,1)
            for _ in range(20):yield
            self.assertEqual((yield from management.read(base+12)),0)
            yield from open_target()
            for _ in range(80):yield
            self.assertEqual((yield from management.read(base+12)),1)
            # Request remains malformed until requester explicitly withdraws it.
            yield from management.write(base+4,1)
            yield from poll(5,1)
            state['withdraw']=True
            for _ in range(30):yield
            yield from open_target()
            for _ in range(100):
                if not (yield f.stop):break
                yield
            else:self.fail('Progress did not requalify')
            self.assertEqual((yield from management.read(base+12)),0)
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
            a=f.axi
            yield a.aw.addr.eq(length);yield a.aw.len.eq(0)
            if malformed=='w':
                yield a.aw.size.eq(2);yield a.aw.burst.eq(1);yield a.aw.id.eq(0x1234)
                yield from target.handshake(a.aw)
                for _ in range(20):yield
                self.assertEqual((yield f.idle),0)
                self.assertEqual((yield a.b.valid),0)
                yield a.w.data.eq(68);yield a.w.strb.eq(15);yield a.w.last.eq(0)
                yield a.w.valid.eq(1)
            else:
                yield a.aw.size.eq(1);yield a.aw.valid.eq(1)
            for _ in range(15):yield
            self.assertEqual((yield getattr(a,malformed).ready),0)
            state['pending']=True
            for _ in range(3000):
                if state['withdraw']:break
                yield
            else:self.fail('No abandonment request')
            yield getattr(a,malformed).valid.eq(0)
            yield a.aw.size.eq(2);yield a.w.last.eq(1)
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
            self.assertEqual((yield f.fault),0)
            state['done']=True
        clocks={name:14 for name in CLOCKS};clocks.update(ps=8,management=8,control=10)
        for name in domains:clocks['aux_release_'+name]=clocks[name]
        for name,crossing in d.csr.ps_cdc.crossings.items():
            periods=(14,8) if name in ('b','r') else (8,14)
            for domain,period in zip(crossing._fragment.clock_domains,periods):clocks[domain.name]=period
        with Simulator(d,{'ps':requester(),'management':manager()},clocks=clocks,
                       special_overrides={AsyncResetSynchronizer:FunctionalReset}) as sim:
            original=sim.time.tick
            stopped={'rtio_rx','aux_release_rtio_rx'}
            def tick():
                dt,rising,falling=original()
                if state['stop']:
                    state['suppressed']+=len(rising & stopped)
                    rising-=stopped;falling-=stopped
                return dt,rising,falling
            sim.time.tick=tick;sim.run()
        self.assertTrue(state['done'])

    def test_malformed_aw_full_hpm_status_reset_and_fresh_write(self):self.exercise('aw')
    def test_bad_wlast_after_accepted_aw_full_hpm_recovery(self):self.exercise('w')

if __name__=='__main__':unittest.main()
