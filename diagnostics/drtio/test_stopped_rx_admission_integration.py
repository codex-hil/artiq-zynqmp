# SPDX-License-Identifier: LGPL-3.0-or-later
"""Full-core stopped-RX diagnostic with stale high vendor status; functional only."""
import unittest
from test_registered_admission_integration import AdmissionIntegrationTests
class StoppedRXAdmissionTests(unittest.TestCase):
 def test_registered_stopped_rx_stale_status(self):
  for phase in (0,3):
   fixture=AdmissionIntegrationTests()
   traces=fixture.exercise(True,tx_phase=phase,stopped_rx=True)
   self.assertEqual(traces['progress_fault'][-1]['link_allowed'],0)
   print('STOPPED_RX_FULL_CORE_PASS phase',phase,'openings',len(fixture.last_openings))
 def test_management_reset_with_rx_still_stopped(self):
  for phase in (0,3):
   fixture=AdmissionIntegrationTests()
   fixture.exercise(True,tx_phase=phase,stopped_rx=True,reset_while_stopped=True)
   self.assertEqual(len(fixture.last_openings),3)
if __name__=='__main__':unittest.main()
