#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Narrow source-policy and emitted FDPE topology audit, not equivalence proof."""
import ast,copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def audit(sources,endpoints):
 def require(file,statement):
  tree=ast.parse(sources[file]);expected=ast.dump(ast.parse(statement).body[0],include_attributes=False)
  assert any(ast.dump(n,include_attributes=False)==expected for n in ast.walk(tree)),(file,statement)
 require('aux_reset_domains_grouped.py','self.group_indices = (0, 1, 2, 1, 1)')
 require('aux_reset_registered.py','sync += [self.reset.eq(coordinator.reset), self.admit.eq(coordinator.admit & ~coordinator.reset), self.abandonment_ready.eq(coordinator.abandonment_ready & coordinator.reset)]')
 require('master_dual_ingress.py','self.comb += [r.request.eq(c.reset), c.domain_ready.eq(r.ready)]')
 require('master_integration.py',"self.comb += getattr(self, 'cd_' + name).rst.eq(g.reset_out[index] | ~ps.outputs['pl_resetn0'])")
 rows=endpoints['reset_synchronizers'];groups=[r for r in rows if r['domain'].startswith('aux_release_')]
 assert sorted(r['domain'] for r in groups)==['aux_release_ps','aux_release_rtio_rx','aux_release_sys']
 assert len({r['asynchronous_assert_expression'] for r in groups})==1
 for r in rows:
  a,b=r['cells'];assert a['primitive']==b['primitive']=='FDPE'
  assert a['parameters']['INIT']==b['parameters']['INIT']==1
  assert a['pins']['C']==b['pins']['C'] and a['pins']['PRE']==b['pins']['PRE']
  assert a['pins']['D']=="1'd0" and b['pins']['D']==a['pins']['Q']
  assert b['pins']['Q']==r['reset_output']
 for name in ('management','control'):
  r=next(r for r in rows if r['domain']==name)
  assert r['asynchronous_assert_expression']=='(~pl_resetn0)'
 return {'physical_release_groups':3,'logical_mapping':[0,1,2,1,1],'fdpe_pairs_checked':len(rows)}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('endpoints',type=Path);a=p.parse_args()
 sources={n:(ROOT/'diagnostics/drtio'/n).read_text() for n in ('aux_reset_domains_grouped.py','aux_reset_registered.py','master_dual_ingress.py','master_integration.py')}
 e=json.loads(a.endpoints.read_text());result=audit(sources,e)
 mutants=[]
 for file,old,new in [('aux_reset_domains_grouped.py','(0,1,2,1,1)','(0,1,2,2,1)'),('aux_reset_registered.py','coordinator.admit & ~coordinator.reset','coordinator.admit'),('master_integration.py',"g.reset_out[index] | ~ps.outputs['pl_resetn0']",'g.reset_out[index]')]:
  m=dict(sources);assert old in m[file];m[file]=m[file].replace(old,new)
  try:audit(m,e)
  except AssertionError:mutants.append(file)
  else:raise AssertionError('Mutation accepted: '+file)
 result.update(status='NARROW_POLICY_AUDIT_PASS',mutations_refused=mutants,source_sha256={n:hashlib.sha256(s.encode()).hexdigest() for n,s in sources.items()},limits=['Source statements and emitted topology only, not sequential equivalence','Registered outputs delay raw coordinator by one control edge; previous full-HPM tests cover bounded command sequences only','Physical timing/CDC and arbitrary requester behavior remain unqualified'])
 print(json.dumps(result,indent=2))
