#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact retained PRE truth tables at Q cutpoints, not timing qualification."""
import argparse,importlib.util,itertools,json
from pathlib import Path
p=Path(__file__).with_name('audit-reset-cdc-cones.py');spec=importlib.util.spec_from_file_location('cones',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
NAMES=('genesysmasterintegration_ingress_outputs_reset_reg/Q','FDPE_5/Q')
def audit(n):
 checks=[]
 for pin in ('FDPE_26/PRE','FDPE_28/PRE','FDPE_30/PRE'):
  expr=n.expression(pin);assert m.variables(expr)==set(NAMES)
  for bits in itertools.product((0,1),repeat=2):assert m.evaluate(expr,dict(zip(NAMES,bits)))==(bits[0]|bits[1])
  checks.append({'endpoint':pin,'expression':expr,'assignments':4})
 return checks
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('network',type=Path);a=p.parse_args();n=m.Network(a.network)
 coord='genesysmasterintegration_ingress_outputs_reset_reg'
 assert n.cells[coord]==('FDSE',"1'b1")
 assert n.cells['FDPE_5']==('FDPE',"1'b1")
 assert n.pins[coord+'/S']==n.pins['FDPE_5/Q']
 assert n.pins[coord+'/C']==n.pins['FDPE_5/C']
 assert n.expression(coord+'/CE')==n.expression('FDPE_5/CE')==('const',1)
 # FDSE Q is an arbitrary cutpoint here, same as FDRE Q. No set/reset
 # semantics are inferred by this evaluator-only type alias.
 fdse=[]
 for cell,(ref,init) in list(n.cells.items()):
  if ref=='FDSE':fdse.append(cell);n.cells[cell]=('FDRE',init)
 checks=audit(n)
 cell=n.drivers[n.pins['FDPE_28/PRE']].rsplit('/',1)[0];ref,init=n.cells[cell];assert ref.startswith('LUT');n.cells[cell]=(ref,"4'h0")
 try:audit(n)
 except AssertionError:pass
 else:raise AssertionError('Changed LUT accepted')
 print(json.dumps({'status':'THREE_RETAINED_PRE_FOUR_ASSIGNMENTS_EACH_PASS_MUTANT_REFUSED','checks':checks,'q_cutpoints':NAMES,'fdse_q_only_evaluator_aliases':fdse,'mapped_handover_pins':'Coordinator FDSE INIT1/CE1/S=control FDPE5 Q; both C same pl_clk0. Discrete same-edge sampling sets coordinator before control reset drops; physical timing still open','ownership_handover':{'required_overlap_sequence_coordinator_control':[[0,1],[1,1],[1,0]],'or_levels':[1,1,1],'missing_overlap_counterexample':[[0,1],[0,0],[1,0]],'unsafe_or_levels':[1,0,1]},'limits':['Boolean Q-cutpoint audit only, not sequential ownership proof','Does not dismiss CDC10 or prove glitch-free physical timing','Prior isolated FDPE handover simulation is separate from full netlist timing'],'next':'Map control reset release and registered coordinator reset set/reset pins in full DCP, then inspect handover invariant without broad timing exceptions'},indent=2))
