# SPDX-License-Identifier: LGPL-3.0-or-later
"""Registered Gray source encoding only, not multi-bit physical CDC proof."""
import unittest
from migen.genlib.cdc import GrayCounter
from migen.sim import run_simulation

class Gray64Tests(unittest.TestCase):
    def exercise(self,start):
        d=GrayCounter(64)
        d.q_binary.reset=start;d.q.reset=start^(start>>1)
        def test():
            prior=None
            for index in range(32):
                binary=(yield d.q_binary);gray=(yield d.q)
                self.assertEqual(gray,binary^(binary>>1))
                if prior is not None:self.assertLessEqual((gray^prior).bit_count(),1)
                prior=gray
                yield d.ce.eq(index%4!=0)
                yield
            if start:self.assertLess((yield d.q_binary),32)
        run_simulation(d,test())
    def test_zero_and_pauses(self):self.exercise(0)
    def test_wrap_and_pauses(self):self.exercise((1<<64)-3)
if __name__=='__main__':unittest.main()
