# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen.genlib.resetsync import AsyncResetSynchronizer
from aux_reset_domains_grouped import AuxResetDomainsGrouped

class GroupedTests(unittest.TestCase):
    def test_explicit_preconditions_required(self):
        for clock,policy in ((False,False),(True,False),(False,True),(1,True),(True,1)):
            with self.assertRaises(ValueError):
                AuxResetDomainsGrouped(shared_tx_clock_confirmed=clock,shared_reset_policy_confirmed=policy)
    def test_fixed_groups_and_three_reset_synchronizers(self):
        g=AuxResetDomainsGrouped(shared_tx_clock_confirmed=True,shared_reset_policy_confirmed=True)
        self.assertEqual(g.group_indices,(0,1,2,1,1))
        f=g.get_fragment()
        self.assertEqual(sum(isinstance(x,AsyncResetSynchronizer) for x in f.specials),3)
        self.assertEqual({cd.name for cd in f.clock_domains},{'aux_release_ps','aux_release_sys','aux_release_rtio_rx'})
if __name__=='__main__':unittest.main()
