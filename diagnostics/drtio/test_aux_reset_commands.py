# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen import Module, ClockDomain, ClockDomainsRenamer
from migen.sim import run_simulation
from migen.genlib.resetsync import AsyncResetSynchronizer
from aux_reset_control import AuxResetControl
from aux_reset_domains import AuxResetDomains
from aux_reset_commands import AuxResetCommands
from test_master_ps_cdc import FunctionalReset

class CommandTests(unittest.TestCase):
    def test_two_episodes_with_stale_abandonment(self):
        d=Module()
        for name in ('management','control','a','b'):
            setattr(d.clock_domains,'cd_'+name,ClockDomain(name))
        d.submodules.control=c=ClockDomainsRenamer('control')(AuxResetControl(2))
        d.submodules.domains=r=AuxResetDomains(('a','b'),control='control')
        d.submodules.commands=h=AuxResetCommands(c)
        d.comb += [r.request.eq(c.reset),c.domain_ready.eq(r.ready)]
        def wait(signal,value):
            for _ in range(160):
                if (yield signal)==value:return
                yield
            self.fail('Bounded management handshake timeout')
        def test():
            # Stale high cannot count as a fresh abandonment acknowledgement.
            yield h.abandoned.eq(1)
            for _ in range(12):yield
            yield h.request.eq(0)
            for _ in range(20):yield
            self.assertEqual((yield h.reset_status),1)
            self.assertEqual((yield h.abandonment_ready),0)
            self.assertEqual((yield h.admit),0)
            for episode in range(2):
                if episode:
                    yield h.request.eq(1)
                    yield from wait(h.admit,0)
                    yield from wait(h.reset_status,1)
                    # Ensure old status_ready has withdrawn before next command.
                    yield from wait(h.abandonment_ready,0)
                    yield h.request.eq(0)
                yield h.abandoned.eq(0)
                yield from wait(h.abandonment_ready,1)
                self.assertEqual((yield h.reset_status),1)
                yield h.abandoned.eq(1)
                yield from wait(h.reset_status,0)
                yield from wait(h.admit,1)
                self.assertEqual((yield r.ready),3)
        run_simulation(d,{'management':test()},
            clocks={'management':8,'control':14,'a':10,'b':22,
                    'aux_release_a':10,'aux_release_b':22},
            special_overrides={AsyncResetSynchronizer:FunctionalReset})

if __name__=='__main__':unittest.main()
