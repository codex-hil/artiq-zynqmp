# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen import Module,ClockDomain
from migen.sim import Simulator
from master_rx_progress import MasterRXProgress

class ProgressTests(unittest.TestCase):
    def exercise(self,rx_period,phase=0,initial_stop=False):
        d=Module()
        d.clock_domains.cd_control=ClockDomain('control')
        d.clock_domains.cd_rx=ClockDomain('rx')
        d.submodules.monitor=m=MasterRXProgress(32,rx='rx')
        state={'stop':initial_stop,'suppressed':0}
        def wait(signal,value,limit=100):
            for _ in range(limit):
                if (yield signal)==value:return
                yield
            self.fail('bounded progress wait expired')
        def test():
            for _ in range(6):yield
            self.assertEqual((yield m.allowed),0)
            yield m.rearm.eq(0)
            if initial_stop:
                yield from wait(m.fault,1)
                self.assertEqual((yield m.allowed),0)
                state['stop']=False
                for _ in range(70):yield
                self.assertEqual((yield m.fault),1)
                self.assertEqual((yield m.allowed),0)
                yield m.rearm.eq(1)
                for _ in range(6):yield
                yield m.rearm.eq(0)
            yield from wait(m.allowed,1)
            for _ in range(180):
                self.assertEqual((yield m.allowed),1)
                self.assertEqual((yield m.fault),0)
                yield
            # Stop RX with a challenge in flight; control clock keeps running.
            state['stop']=True
            yield from wait(m.fault,1,70)
            self.assertGreater(state['suppressed'],0)
            self.assertEqual((yield m.allowed),0)
            state['stop']=False
            for _ in range(100):yield
            self.assertEqual((yield m.fault),1) # restart cannot clear fault
            self.assertEqual((yield m.allowed),0)
            # Explicit rearm held while RX stopped cannot admit stale ack.
            state['stop']=True
            yield m.rearm.eq(1)
            for _ in range(12):yield
            self.assertEqual((yield m.allowed),0)
            yield m.rearm.eq(0)
            for _ in range(20):
                self.assertEqual((yield m.allowed),0)
                yield
            state['stop']=False
            yield from wait(m.allowed,1)
            self.assertEqual((yield m.fault),0)
        with Simulator(d,{'control':test()},clocks={'control':8,'rx':(rx_period,phase)}) as sim:
            tick_original=sim.time.tick
            def tick():
                dt,rising,falling=tick_original()
                if state['stop']:
                    state['suppressed']+=len(rising & {'rx'})
                    rising-={'rx'};falling-={'rx'}
                return dt,rising,falling
            sim.time.tick=tick;sim.run()
    def test_equal_clocks(self):self.exercise(8)
    def test_fast_rx(self):self.exercise(4,1)
    def test_slow_rx(self):self.exercise(14,3)
    def test_rx_absent_at_start(self):self.exercise(10,1,True)
    def test_invalid(self):
        for n in (True,0,3,4.5):
            with self.assertRaises(ValueError):MasterRXProgress(n)
        with self.assertRaises(ValueError):MasterRXProgress(control='x',rx='x')

if __name__=='__main__':unittest.main()
