# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen import Module, ClockDomain
from migen.sim import Simulator
from migen.genlib.resetsync import AsyncResetSynchronizer
from aux_reset_control import AuxResetControl
from aux_reset_domains import AuxResetDomains
from test_master_ps_cdc import FunctionalReset

class DomainResetTests(unittest.TestCase):
    def test_coordinator_waits_stopped_domain_and_fresh_handshake(self):
        d=Module()
        for name in ('sys','a','b'):
            setattr(d.clock_domains,'cd_'+name,ClockDomain(name))
        d.submodules.control=c=AuxResetControl(2)
        d.submodules.domains=r=AuxResetDomains(('a','b'))
        d.comb += [r.request.eq(c.reset),c.domain_ready.eq(r.ready)]
        state={'stop':set(),'suppressed':0}
        def test():
            for _ in range(12):yield
            self.assertEqual((yield r.ready),0)
            yield c.request.eq(0)
            yield c.requester_abandoned.eq(0)
            for _ in range(4):yield
            # Stop B only after both reset acknowledgements have cleared.
            state['stop']={'b','aux_release_b'}
            yield c.requester_abandoned.eq(1)
            for _ in range(40):yield
            self.assertEqual((yield c.reset),0)
            self.assertEqual((yield r.ready),1)
            self.assertEqual((yield c.admit),0)
            self.assertGreater(state['suppressed'],0)
            state['stop']=set()
            for _ in range(40):yield
            self.assertEqual((yield r.ready),3)
            self.assertEqual((yield c.admit),1)
            yield c.request.eq(1)
            for _ in range(20):yield
            self.assertEqual((yield c.admit),0)
            self.assertEqual((yield r.ready),0)
            yield c.request.eq(0)
            for _ in range(20):yield
            self.assertEqual((yield c.reset),1) # stale abandonment1 refused
            yield c.requester_abandoned.eq(0)
            for _ in range(4):yield
            yield c.requester_abandoned.eq(1)
            for _ in range(40):yield
            self.assertEqual((yield c.admit),1)
        clocks={'sys':8,'a':10,'b':14,'aux_release_a':10,'aux_release_b':14}
        with Simulator(d,test(),clocks=clocks,
                       special_overrides={AsyncResetSynchronizer:FunctionalReset}) as sim:
            original=sim.time.tick
            def tick():
                dt,rising,falling=original()
                state['suppressed']+=len(rising & state['stop'])
                return dt,rising-state['stop'],falling-state['stop']
            sim.time.tick=tick
            sim.run()

    def test_invalid_domains(self):
        for domains in ((),('a','a'),('sys',)):
            with self.assertRaises(ValueError):AuxResetDomains(domains)

if __name__=='__main__':unittest.main()
