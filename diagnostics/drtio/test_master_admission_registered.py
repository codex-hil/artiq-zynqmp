# SPDX-License-Identifier: LGPL-3.0-or-later
"""Sampled admission latency and preserved independent reset wiring."""
import unittest
from types import SimpleNamespace
from migen import Module,Signal,ClockDomain
from migen.sim import run_simulation
from migen.genlib.cdc import MultiReg
from master_admission_registered import MasterAdmissionRegistered,MasterLinkBoundaryRegistered

class AdmissionRegisteredTests(unittest.TestCase):
    def test_all_control_conditions_and_sustained_fault_withdrawal(self):
        d=Module();d.clock_domains.cd_control=ClockDomain('control')
        admit,reset,fault,shape=Signal(),Signal(),Signal(),Signal()
        fresh=Signal(2);raw=Signal()
        d.comb+=raw.eq(admit & ~reset & ~fault & (fresh==2) & ~shape)
        d.submodules.sample=r=MasterAdmissionRegistered(raw,reset)
        def test():
            self.assertEqual((yield r.allowed),0)
            # Explicit opening/individual fault/reset/reopening episodes first;
            # then enumerate every source-register Boolean combination.
            vectors=[(1,0,0,2,0),(1,0,1,2,0),(1,0,0,2,0),
                     (1,0,0,2,1),(1,0,0,2,0),(1,1,0,2,0)]
            vectors += [(a,z,f,n,s) for a in (0,1) for z in (0,1)
                        for f in (0,1) for n in range(4) for s in (0,1)]
            for a,z,f,n,s in vectors:
                old=(yield r.allowed)
                yield admit.eq(a);yield reset.eq(z);yield fault.eq(f)
                yield fresh.eq(n);yield shape.eq(s)
                self.assertEqual((yield r.allowed),old)
                yield;yield
                self.assertEqual((yield r.allowed),a & (1-z) & (1-f) & int(n==2) & (1-s))
        run_simulation(d,{'control':test()},clocks={'control':10})

    def test_existing_sys_boundary_samples_registered_signal_reset_independent(self):
        codec=SimpleNamespace(**{n:Signal() for n in ('rx_reset','rx_reset_done','rx_clock_active','word_aligned')})
        status=SimpleNamespace(**{n:Signal() for n in ('reset_done','clock_active','aligned')})
        admit,reset=Signal(),Signal()
        d=MasterLinkBoundaryRegistered(codec,admit,reset,status)
        specials=list(d.boundary._fragment.specials)
        self.assertEqual(len(specials),5)
        self.assertTrue(all(isinstance(s,MultiReg) for s in specials))
        self.assertEqual(sum(s.i is d.sample.allowed for s in specials),1)
        self.assertEqual(sum(s.i is reset for s in specials),1)
        self.assertIs(d.gt_reset_request,reset)
        self.assertFalse(any(s.i is admit for s in specials))
if __name__=='__main__':unittest.main()
