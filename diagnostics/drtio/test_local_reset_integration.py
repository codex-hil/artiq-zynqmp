# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate local-reset candidate in full fixed-clock digital integration."""
import json,os,unittest
from pathlib import Path
from migen import Module
from master_admission_registered import MasterAdmissionRegistered
from master_link_local_reset import MasterLinkLocalReset
from test_registered_admission_integration import AdmissionIntegrationTests
class RegisteredLocalFixture(Module):
 def __init__(self,codec,admit,reset_request,status):
  self.submodules.sample=s=MasterAdmissionRegistered(admit,reset_request)
  # Scoped test parent is GenesysMasterIntegration+grouped reset releases;
  # confirmation is not a production/physical reset qualification.
  self.submodules.boundary=b=MasterLinkLocalReset(codec,s.allowed,reset_request,status,parent_reset_contract_confirmed=True)
  self.allowed=b.allowed;self.gt_reset_request=b.gt_reset_request
class LocalIntegrationTests(unittest.TestCase):
 def test_two_phases_reset_reopen_and_faults(self):
  results=[]
  for phase in (0,3):
   h=AdmissionIntegrationTests()
   traces=h.exercise(True,tx_phase=phase,boundary_factory=RegisteredLocalFixture)
   self.assertEqual(len(h.last_openings),3)
   results.append({'phase':phase,'openings':h.last_openings,'sys_traces':traces,'control_traces':h.last_control_trace})
   print('LOCAL_RESET_INTEGRATION_PASS phase',phase,'fresh_openings',len(h.last_openings),flush=True)
  if os.environ.get('LOCAL_RESET_TRACE_OUTPUT'):Path(os.environ['LOCAL_RESET_TRACE_OUTPUT']).write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':unittest.main()
