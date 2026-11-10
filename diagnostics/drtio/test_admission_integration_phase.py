# SPDX-License-Identifier: LGPL-3.0-or-later
"""Bounded extra full-integration phase/trigger cases; no physical latency bound."""
import json,os,unittest
from pathlib import Path
from test_registered_admission_integration import AdmissionIntegrationTests
class PhaseTests(unittest.TestCase):
 def test_two_phase_trigger_pairs(self):
  result=[]
  for phase,delay in ((0,1),(3,0)):
   for registered in (False,True):
    helper=AdmissionIntegrationTests()
    traces=helper.exercise(registered,tx_phase=phase,trigger_delay=delay)
    control=helper.last_control_trace
    metrics={}
    for event,t in traces.items():
     raw=next(i for i,x in enumerate(t) if not x['raw_admit'])
     closed=next(i for i,x in enumerate(t) if not x['link_allowed'])
     metrics[event]={'first_raw_sys':raw,'first_closed_sys':closed,'delta_sys_samples':closed-raw}
     if registered:
      c=control[event]
      # Sampled before synchronous assignments settle: compare the first
      # sustained raw withdrawal with the register on subsequent edges.
      cr=next(i for i,x in enumerate(c) if not x['raw_admit'])
      cq=next(i for i,x in enumerate(c) if not x['registered_admit'])
      self.assertIn(cq-cr,(0,1))
      metrics[event]['raw_to_registered_control_samples']=cq-cr
    result.append(dict(tx_phase=phase,trigger_delay=delay,registered=registered,metrics=metrics,sys_traces=traces,control_traces=control))
    print('PHASE_CASE',phase,delay,registered,json.dumps(metrics),flush=True)
  if os.environ.get('ADMISSION_PHASE_OUTPUT'):Path(os.environ['ADMISSION_PHASE_OUTPUT']).write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':unittest.main()
