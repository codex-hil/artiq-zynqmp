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
from master_axi_drain import MasterAXIDrain

class ProgressAXIDrainTests(unittest.TestCase):
    def test_progress_fault_with_unaccepted_b_and_independent_management(self):
        d=Pair(now64=True)
        domains=('ps','sys','rtio_rx','rio','rio_phy')
        for name in domains+('management','control'):
            setattr(d.clock_domains,'cd_'+name,ClockDomain(name))
        d.submodules.aux=GenesysMasterAux(d.master,controller_type=GrayAuxController)
        d.submodules.csr=GenesysMasterCSR(d.time,d.ki,d.master,d.routing,aux=d.aux,ps_clock='ps')
        d.submodules.ingress=g=MasterDualIngress(d.csr.axi)
        for index,name in enumerate(domains):d.comb+=getattr(d,'cd_'+name).rst.eq(g.reset_out[index])
        d.submodules.progress=p=MasterRXProgress(32)
        d.submodules.fault_gate=f=ClockDomainsRenamer('ps')(MasterAXIDrain(g.target_axi))
        qualified=Signal()
        d.specials+=MultiReg(p.allowed,qualified,'ps')
        d.comb += [p.rearm.eq(g.coordinator.reset),
                   f.stop.eq(~qualified | g.reset_out[0])]
        management=AXIMaster(g.management_axi);target=AXIMaster(f.axi)
        base=g.management.BASE;length=d.csr.registers['aux_aux_tx_length']['address']
        state={'start':False,'pending':False,'reopened':False,'done':False,'stop':False,'suppressed':0}
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
            self.assertEqual((yield f.axi.b.valid),1)
            self.assertEqual((yield f.axi.b.ready),0)
            state['stop']=True
            for _ in range(100):
                if (yield p.fault) and (yield f.stop):break
                yield
            else:self.fail('RX fault did not close gate')
            self.assertGreater(state['suppressed'],0)
            self.assertEqual((yield g.target_axi.b.valid),1) # pending response retained by drain
            for _ in range(12):
                self.assertEqual((yield f.axi.b.valid),1)
                self.assertEqual((yield f.axi.b.id),0x1234)
                self.assertEqual((yield f.axi.b.resp),0)
                self.assertEqual((yield f.axi.aw.ready),0)
                self.assertEqual((yield f.axi.w.ready),0)
                self.assertEqual((yield f.axi.ar.ready),0)
                yield
            # Previously committed length is retained: missing B is not rollback.
            self.assertEqual((yield d.aux.controller.transmitter.aux_tx_length.storage),17)
            self.assertEqual((yield from management.read(base)),g.management.IDENTITY)
            state['stop']=False
            for _ in range(80):yield
            self.assertEqual((yield p.fault),1)
            self.assertEqual((yield f.stop),1)
            # Explicit abandonment/reset recovery through independent HPM1.

            yield from management.write(base+4,1)
            yield from poll(5,1)
            self.assertEqual((yield from management.read(base)),g.management.IDENTITY)
            yield from open_target()
            for _ in range(100):
                if not (yield f.stop):break
                yield
            else:self.fail('Fresh progress recovery failed')
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
            yield a.aw.addr.eq(length);yield a.aw.size.eq(2);yield a.aw.len.eq(0)
            yield a.aw.burst.eq(1);yield a.aw.id.eq(0x1234)
            yield from target.handshake(a.aw)
            yield a.w.data.eq(68);yield a.w.strb.eq(15);yield a.w.last.eq(1)
            yield from target.handshake(a.w)
            for _ in range(300):
                if (yield a.b.valid):break
                yield
            else:
                snapshot=[]
                for bus in (f.axi,g.target_axi,d.csr.axi):
                    snapshot.append([(yield bus.aw.valid),(yield bus.aw.ready),(yield bus.w.valid),(yield bus.w.ready),(yield bus.b.valid)])
                self.fail('No target completion '+str(snapshot)+' storage '+str((yield d.aux.controller.transmitter.aux_tx_length.storage)))
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

if __name__=='__main__':unittest.main()
