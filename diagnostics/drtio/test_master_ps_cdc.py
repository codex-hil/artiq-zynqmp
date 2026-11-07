# SPDX-License-Identifier: LGPL-3.0-or-later
"""Construction checks only; no dynamic/reset/clock-stop qualification."""
import unittest
from migen import ClockDomain, Module
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.soc.interconnect.axi import AXILiteInterface
from master_ps_cdc import GenesysMasterPSCDC


class Construction(unittest.TestCase):
    def test_five_channels_with_both_reset_synchronizers(self):
        top = Module()
        top.clock_domains.cd_sys = ClockDomain('sys')
        top.clock_domains.cd_master = ClockDomain('master')
        cdc = GenesysMasterPSCDC(AXILiteInterface(), AXILiteInterface())
        top.submodules.cdc = cdc
        self.assertEqual(set(cdc.crossings), {'aw', 'w', 'b', 'ar', 'r'})
        # Every maintained stream crossing must own two common-reset domains.
        for crossing in cdc.crossings.values():
            fragment = crossing.get_fragment()
            self.assertEqual(len(fragment.clock_domains), 2)
            self.assertEqual(sum(isinstance(s, AsyncResetSynchronizer)
                                 for s in fragment.specials), 2)

    def test_invalid_interfaces_refused(self):
        cases = [
            (AXILiteInterface(), AXILiteInterface(), {'master_clock': 'sys'}),
            (AXILiteInterface(data_width=64), AXILiteInterface(), {}),
            (AXILiteInterface(), AXILiteInterface(address_width=40), {}),
            (AXILiteInterface(mode='r'), AXILiteInterface(), {})]
        for ps, master, options in cases:
            with self.subTest(options=options), self.assertRaises(ValueError):
                GenesysMasterPSCDC(ps, master, **options)

if __name__ == '__main__':
    unittest.main()
