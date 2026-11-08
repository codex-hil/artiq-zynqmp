# SPDX-License-Identifier: LGPL-3.0-or-later
"""Reset/boundary composition with suppressed RX edges, not physical CDC proof."""
import unittest
from types import SimpleNamespace
from migen import Module, ClockDomain, Signal, ClockDomainsRenamer
from migen.sim import Simulator
from migen.genlib.resetsync import AsyncResetSynchronizer
from aux_reset_control import AuxResetControl
from aux_reset_domains import AuxResetDomains
from master_link_boundary import MasterLinkBoundary
from test_master_ps_cdc import FunctionalReset
from master_rx_progress import MasterRXProgress

class ProgressResetCompositionTests(unittest.TestCase):
    def test_progress_fault_blocks_until_explicit_reset_and_fresh_rx(self):
        d=Module()
        for name in ('control','sys','rx'):
            setattr(d.clock_domains,'cd_'+name,ClockDomain(name))
        d.submodules.control=c=ClockDomainsRenamer('control')(AuxResetControl(2))
        d.submodules.domains=r=AuxResetDomains(('sys','rx'),control='control')
        d.comb += [r.request.eq(c.reset),c.domain_ready.eq(r.ready),
                   d.cd_sys.rst.eq(r.reset_out[0]),d.cd_rx.rst.eq(r.reset_out[1])]
        codec=SimpleNamespace(**{n:Signal() for n in
            ('rx_reset','rx_reset_done','rx_clock_active','word_aligned')})
        status=SimpleNamespace(**{n:Signal(reset=1) for n in
            ('reset_done','clock_active','aligned')})
        d.submodules.progress=p=MasterRXProgress(32,rx='rx')
        admitted=Signal()
        # Fault closes admission only: it must not cause its own rearm/reset.
        d.comb += [p.rearm.eq(c.reset),admitted.eq(c.admit & p.allowed)]
        d.submodules.boundary=b=MasterLinkBoundary(codec,admitted,c.reset,status)
        state={'stop':False,'suppressed':0}
        stopped={'rx','aux_release_rx'}
        def wait(signal,value,limit=80):
            for _ in range(limit):
                if (yield signal)==value:return
                yield
            self.fail('bounded wait expired')
        def test():
            for _ in range(12):yield
            yield c.request.eq(0)
            yield c.requester_abandoned.eq(0)
            for _ in range(4):yield
            yield c.requester_abandoned.eq(1)
            yield from wait(c.admit,1)
            yield from wait(b.allowed,1)
            self.assertEqual((yield p.allowed),1)
            state['stop']=True
            for _ in range(32):yield
            self.assertGreater(state['suppressed'],0)
            # Stale status and release acks are still high, but progress fails.
            self.assertEqual((yield c.admit),1)
            yield from wait(p.fault,1)
            yield from wait(b.allowed,0)
            self.assertEqual((yield admitted),0)
            self.assertEqual((yield codec.rx_reset),1)
            state['stop']=False
            for _ in range(80):yield
            self.assertEqual((yield p.fault),1)
            self.assertEqual((yield admitted),0)
            self.assertEqual((yield b.allowed),0)
            # Stop RX again before management recovery; stale high status persists.
            state['stop']=True
            # Independent management explicitly requests reset; no auto retry.
            yield c.request.eq(1)
            yield from wait(c.admit,0)
            yield from wait(b.allowed,0)
            self.assertEqual((yield codec.rx_reset),1)
            for _ in range(12):yield
            yield c.request.eq(0)
            yield c.requester_abandoned.eq(0)
            for _ in range(4):yield
            yield c.requester_abandoned.eq(1)
            # Functional simulation retains stale RX ack until an RX edge.
            for _ in range(24):
                self.assertEqual((yield c.admit),0)
                self.assertEqual((yield b.allowed),0)
                self.assertEqual((yield c.reset),1)
                yield
            state['stop']=False
            yield from wait(r.ready,0)
            yield from wait(c.admit,1)
            yield from wait(p.allowed,1)
            yield from wait(b.allowed,1)
            self.assertEqual((yield codec.rx_reset),0)
        clocks={'control':8,'sys':10,'rx':14,'aux_release_sys':10,'aux_release_rx':14}
        with Simulator(d,{'control':test()},clocks=clocks,
                       special_overrides={AsyncResetSynchronizer:FunctionalReset}) as sim:
            original=sim.time.tick
            def tick():
                dt,rising,falling=original()
                if state['stop']:
                    state['suppressed']+=len(rising & stopped)
                    rising-=stopped;falling-=stopped
                return dt,rising,falling
            sim.time.tick=tick
            sim.run()

if __name__=='__main__':unittest.main()
