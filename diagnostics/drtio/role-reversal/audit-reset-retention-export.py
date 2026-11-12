#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Narrow emitted-text delta audit; not formal or physical equivalence."""
import argparse,hashlib,json
from pathlib import Path
NAMES=('request0','request1','ready1','reset_out1','count0','count1','count2','local_ready0','local_ready1','local_ready2')
def audit(base,candidate):
 for name in NAMES:candidate=candidate.replace('__main___releases_'+name,'__main___'+name)
 declaration='wire __main___retention_request;\n'
 assignment='assign __main___retention_request = (coordinator_reset | control_reset);\n'
 wiring='assign __main___request0 = __main___retention_request;'
 assert candidate.count(declaration)==candidate.count(assignment)==candidate.count(wiring)==1
 candidate=candidate.replace(declaration,'').replace(assignment,'').replace(wiring,'assign __main___request0 = coordinator_reset;')
 assert candidate==base,'Other RTL difference refused'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);a=p.parse_args()
 b,c=a.baseline.read_text(),a.candidate.read_text();audit(b,c)
 for old,new in [('coordinator_reset | control_reset','coordinator_reset & control_reset'),('permit & (~sys_reset)','permit | (~sys_reset)')]:
  assert old in c
  try:audit(b,c.replace(old,new))
  except AssertionError:pass
  else:raise AssertionError('Mutation accepted')
 print(json.dumps({'status':'NARROW_RETENTION_RTL_DELTA_PASS_TWO_MUTANTS_REFUSED','delta':'Release request gains OR synchronized control reset; ten explicitly listed names change; all other RTL byte identical after normalization','baseline_sha256':hashlib.sha256(a.baseline.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),'limits':['Text correspondence not sequential/physical equivalence','Vendor FDPE stopped-control retention/restart simulation pending']},indent=2))
