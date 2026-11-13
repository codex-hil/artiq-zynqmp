# SPDX-License-Identifier: LGPL-3.0-or-later
"""Actual upstream stats trigger pipeline; no GT or admission timing proof."""
import unittest
from types import SimpleNamespace
from migen import Module,Signal,ClockDomain
from migen.genlib.cdc import GrayCounter
from migen.sim import run_simulation
from artiq.gateware.drtio.link_layer import LinkLayerStats
class StatsWithdrawalTests(unittest.TestCase):
 def test_registered_frame_trigger_has_tail_after_permission_withdrawal(self):
  d=Module();d.clock_domains.cd_sys=ClockDomain('sys');d.clock_domains.cd_rtio_rx=ClockDomain('rtio_rx')
  ll=SimpleNamespace(rx_aux_frame_perm=Signal(),rx_aux_data=Signal(16),rx_rt_frame_perm=Signal())
  d.submodules.stats=s=LinkLayerStats(ll,'rtio_rx')
  counters=[child for name,child in s._submodules if isinstance(child,GrayCounter)]
  self.assertEqual(len(counters),4);observed=[]
  def test():
   yield ll.rx_aux_frame_perm.eq(1)
   for _ in range(8):yield
   before=(yield counters[0].q_binary)
   yield ll.rx_aux_frame_perm.eq(0)
   for _ in range(7):
    yield
    observed.append((yield counters[0].q_binary))
   self.assertGreater(observed[0],before)
   self.assertEqual(len(set(observed[-3:])),1)
   self.assertTrue(all(b-a in (0,1) for a,b in zip([before]+observed,observed)))
   self.assertEqual((yield counters[2].q_binary),0)
   print('ACTUAL_STATS_WITHDRAWAL before',before,'samples',observed,flush=True)
  run_simulation(d,{'rtio_rx':test()},clocks={'sys':8,'rtio_rx':18})
 def test_full_hpm_csr_can_advance_before_physical_link_ready(self):
  from unittest.mock import patch
  from test_grouped_registered_full_hpm import RegisteredCoordinatorFixture,grouped_fixture
  from test_master_integration import IntegrationTests
  from aux_reset_domains_retained import AuxResetDomainsRetained
  with patch('master_dual_ingress.AuxResetControl',RegisteredCoordinatorFixture),patch('master_dual_ingress.AuxResetDomains',side_effect=grouped_fixture),patch('test_grouped_registered_full_hpm.AuxResetDomainsGrouped',AuxResetDomainsRetained):
   IntegrationTests.exercise_two_hpm_roundtrip(self,True,True,not_ready_link=True)
  print('HPM_CSR12_68_WITH_RX_READY0_PASS modeled_clocks_running',flush=True)
if __name__=='__main__':unittest.main()
