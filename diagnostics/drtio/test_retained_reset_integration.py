# SPDX-License-Identifier: LGPL-3.0-or-later
"""Scoped retained-release substitution in core/link and HPM recovery tests."""
import json,os,unittest
from pathlib import Path
from unittest.mock import patch
from aux_reset_domains_retained import AuxResetDomainsRetained
from test_local_reset_integration import RegisteredLocalFixture
from test_registered_admission_integration import AdmissionIntegrationTests
from test_grouped_registered_full_hpm import GroupedRegisteredFullHPMTests
class RetainedIntegrationTests(unittest.TestCase):
 def test_two_core_link_phases_fault_reset_reopen(self):
  results=[]
  for phase in (0,3):
   h=AdmissionIntegrationTests()
   with patch('test_grouped_registered_full_hpm.AuxResetDomainsGrouped',AuxResetDomainsRetained):
    traces=h.exercise(True,tx_phase=phase,boundary_factory=RegisteredLocalFixture)
   self.assertEqual(len(h.last_openings),3)
   results.append({'phase':phase,'openings':h.last_openings,'sys_traces':traces,'control_traces':h.last_control_trace})
   print('RETAINED_FULL_CORE_PASS phase',phase,'fresh_openings',len(h.last_openings),flush=True)
  if os.environ.get('RETAINED_TRACE_OUTPUT'):Path(os.environ['RETAINED_TRACE_OUTPUT']).write_text(json.dumps(results,indent=2)+'\n')
 def test_hpm_adapters_two_reset_episodes_exact_multireg(self):
  h=GroupedRegisteredFullHPMTests()
  with patch('test_grouped_registered_full_hpm.AuxResetDomainsGrouped',AuxResetDomainsRetained):
   h.test_guarded_actual_adapters_two_reset_episodes_exact_multireg()
if __name__=='__main__':unittest.main()
