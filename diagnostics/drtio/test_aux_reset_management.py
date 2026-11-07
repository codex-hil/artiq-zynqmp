# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen import Module,ClockDomain,ClockDomainsRenamer
from migen.sim import run_simulation
from migen.genlib.resetsync import AsyncResetSynchronizer
from aux_reset_control import AuxResetControl
from aux_reset_domains import AuxResetDomains
from aux_reset_management import AuxResetManagement
from test_master_ps_cdc import FunctionalReset

class ManagementTests(unittest.TestCase):
    def test_mmio_handshake_and_rejected_writes(self):
        d=Module()
        for name in ('management','control','target'):
            setattr(d.clock_domains,'cd_'+name,ClockDomain(name))
        d.submodules.control=c=ClockDomainsRenamer('control')(AuxResetControl(1))
        d.submodules.domains=r=AuxResetDomains(('target',),control='control')
        d.submodules.management=m=AuxResetManagement(c)
        d.comb += [r.request.eq(c.reset),c.domain_ready.eq(r.ready)]
        a=m.axi
        def wait(signal):
            for _ in range(120):
                if (yield signal):return
                yield
            self.fail('Management AXI timeout')
        def read(address,resp=0):
            yield a.ar.addr.eq(address)
            yield a.ar.valid.eq(1)
            yield from wait(a.ar.ready)
            yield
            yield a.ar.valid.eq(0)
            yield from wait(a.r.valid)
            self.assertEqual((yield a.r.resp),resp)
            result=(yield a.r.data)
            yield a.r.ready.eq(1)
            yield
            yield a.r.ready.eq(0)
            yield
            return result
        def write(value,address=m.BASE+4,strb=15,resp=0):
            yield a.aw.addr.eq(address)
            yield a.aw.valid.eq(1)
            yield a.w.data.eq(value)
            yield a.w.strb.eq(strb)
            yield a.w.valid.eq(1)
            yield from wait(a.w.ready)
            self.assertEqual((yield a.aw.ready),1)
            yield
            yield a.aw.valid.eq(0)
            yield a.w.valid.eq(0)
            yield from wait(a.b.valid)
            self.assertEqual((yield a.b.resp),resp)
            yield a.b.ready.eq(1)
            yield
            yield a.b.ready.eq(0)
            yield
        def poll(mask,value):
            for _ in range(40):
                status=yield from read(m.BASE+8)
                if status&mask==value:return
            self.fail('Management status timeout')
        def test():
            self.assertEqual((yield from read(m.BASE)),m.IDENTITY)
            self.assertEqual((yield from read(m.BASE+4)),1)
            for address in (m.BASE-4,m.BASE+12,m.BASE+(1<<32)):
                yield from read(address,2)
            for value,address,strb in ((0,m.BASE,15),(0,m.BASE+8,15),
                                      (0,m.BASE+12,15),(4,m.BASE+4,15),(0,m.BASE+4,1)):
                yield from write(value,address,strb,2)
                self.assertEqual((yield from read(m.BASE+4)),1)
            for _ in range(2):
                yield from write(0)
                yield from poll(3,3) # reset held and fresh abandonment requested
                yield from write(2)
                yield from poll(5,4) # admitted/reset released
                yield from write(1)
                yield from poll(5,1) # management stays accessible during reset
                self.assertEqual((yield from read(m.BASE)),m.IDENTITY)
        run_simulation(d,{'management':test()},
            clocks={'management':8,'control':14,'target':22,'aux_release_target':22},
            special_overrides={AsyncResetSynchronizer:FunctionalReset})

if __name__=='__main__':unittest.main()
