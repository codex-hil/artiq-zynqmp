# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen.sim import run_simulation
from aux_reset_control import AuxResetControl

class ResetControlTests(unittest.TestCase):
    def test_stale_ready_abandonment_and_stopped_domain(self):
        d=AuxResetControl(3)
        def test():
            yield d.domain_ready.eq(7)
            yield d.requester_abandoned.eq(1)
            yield d.request.eq(0)
            for _ in range(5):
                self.assertEqual((yield d.admit),0)
                self.assertEqual((yield d.reset),1)
                yield
            # Stale high abandonment cannot release, even after ready goes low.
            yield d.domain_ready.eq(0)
            for _ in range(5):yield
            self.assertEqual((yield d.reset),1)
            yield d.requester_abandoned.eq(0)
            for _ in range(3):yield
            yield d.requester_abandoned.eq(1)
            for _ in range(4):yield
            self.assertEqual((yield d.reset),0)
            self.assertEqual((yield d.admit),0)
            # Missing restart acknowledgement blocks admission indefinitely.
            yield d.domain_ready.eq(3)
            for _ in range(20):
                self.assertEqual((yield d.admit),0)
                yield
            yield d.domain_ready.eq(7)
            for _ in range(3):yield
            self.assertEqual((yield d.admit),1)
            yield d.domain_ready.eq(3)
            yield
            self.assertEqual((yield d.admit),0)
            yield d.domain_ready.eq(7)
            yield
            yield d.request.eq(1)
            yield
            self.assertEqual((yield d.admit),0)
            self.assertEqual((yield d.reset),1)
            yield
            yield d.request.eq(0)
            yield d.domain_ready.eq(0)
            for _ in range(8):yield
            # Previous episode's abandonment high cannot authorize this reset.
            self.assertEqual((yield d.reset),1)
        run_simulation(d,test())

    def test_invalid_domain_count(self):
        for count in (0,-1,True,1.5):
            with self.assertRaises(ValueError):AuxResetControl(count)

if __name__=='__main__':unittest.main()
