#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exhaustive combinational admission/reset audit at arbitrary Q cutpoints."""
import importlib.util,itertools,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('cones',HERE/'audit-reset-cdc-cones.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PREFIX='genesysmasterintegration_'
NAMES=[PREFIX+x for x in ('ingress_outputs_admit_reg/Q','ingress_outputs_reset_reg/Q','progress_fault_reg/Q','progress_fresh_reg[0]/Q','progress_fresh_reg[1]/Q')]+['xilinxmultiregimpl411_reg/Q']
def audit(n):
 expr=n.expression('xilinxmultiregimpl420_reg/D')
 assert m.variables(expr)==set(NAMES)
 for bits in itertools.product((0,1),repeat=6):
  admit,reset,fault,fresh0,fresh1,shape=bits
  expected=admit & (1-reset) & (1-fault) & (1-fresh0) & fresh1 & (1-shape)
  assert m.evaluate(expr,dict(zip(NAMES,bits)))==expected,bits
 reset=('var',PREFIX+'ingress_outputs_reset_reg/Q')
 assert n.expression('xilinxmultiregimpl430_reg/D')==reset
 assert n.expression('FDPE_28/PRE')==reset
 return expr
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('network',type=Path);a=p.parse_args()
 n=m.Network(a.network);fdse=[]
 # Q is an arbitrary variable for both FDSE and FDRE here. Alias only the
 # evaluator's cell-type view; do not infer or change set/reset behavior.
 for name,(ref,init) in list(n.cells.items()):
  if ref=='FDSE':fdse.append(name);n.cells[name]=('FDRE',init)
 expr=audit(n)
 cell=n.drivers[n.pins['xilinxmultiregimpl420_reg/D']].rsplit('/',1)[0]
 ref,init=n.cells[cell];n.cells[cell]=(ref,"8'h00")
 try:audit(n)
 except AssertionError:mutation='REFUSED'
 else:raise AssertionError('Changed admission LUT accepted')
 print(json.dumps({'status':'ADMISSION64_ASSIGNMENTS_AND_TWO_RESET_DIRECT_Q_PATHS_PASS','admission_expression':expr,'q_cutpoints':NAMES,'fdse_q_only_evaluator_aliases':fdse,'mutation':mutation,'findings':['Permit first-stage D is a combinational function of six control Q cutpoints, including progress and synchronized shape fault; source-function match does not remove CDC10 glitch risk','One registered reset Q directly drives both TX reset synchronizer PRE and requested-status first D; CDC11 fanout remains','Requested reset MultiReg INIT1 versus emitted INIT0 mismatch remains separately recorded'],'limits':['No timing/glitch/metastability proof','No sequential equivalence or FDSE set/reset proof','No netlist/default/HW modifications or waiver'],'next':'Separate registered-admission candidate before SYS MultiReg with explicit extra control cycle; test fault withdrawal and reset sequencing before considering adoption'},indent=2))
