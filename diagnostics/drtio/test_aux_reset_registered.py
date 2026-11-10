# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from types import SimpleNamespace
from migen import Module,ClockDomain,Signal
from migen.sim import run_simulation
from aux_reset_registered import AuxResetRegistered

class RegisteredTests(unittest.TestCase):
    def test_one_control_edge_and_reset_dominates_statuses(self):
        d=Module();d.clock_domains.cd_control=ClockDomain('control')
        c=SimpleNamespace(**{n:Signal() for n in ('reset','admit','abandonment_ready','request','requester_abandoned')})
        d.submodules.outputs=r=AuxResetRegistered(c)
        self.assertIs(r.request,c.request);self.assertIs(r.requester_abandoned,c.requester_abandoned)
        def test():
            self.assertEqual((yield r.reset),1)
            self.assertEqual((yield r.admit),0)
            for reset,admit,ready in ((1,1,1),(0,1,1),(1,0,0),(0,0,1)):
                previous=((yield r.reset),(yield r.admit),(yield r.abandonment_ready))
                yield c.reset.eq(reset);yield c.admit.eq(admit);yield c.abandonment_ready.eq(ready)
                self.assertEqual(((yield r.reset),(yield r.admit),(yield r.abandonment_ready)),previous)
                yield;yield
                self.assertEqual((yield r.reset),reset)
                self.assertEqual((yield r.admit),admit & (1-reset))
                self.assertEqual((yield r.abandonment_ready),ready & reset)
        run_simulation(d,{'control':test()},clocks={'control':10})
if __name__=='__main__':unittest.main()
