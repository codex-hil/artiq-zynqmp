#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Bounded common-reset LUT audit; no sequential or physical CDC signoff."""
import importlib.util,itertools,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('cones',HERE/'audit-reset-cdc-cones.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def audit(network,top):
 # Network capture omits ports. Bind only this exact top-level input; refuse
 # all other missing drivers rather than inventing unknown-net values.
 assert 'input pl_resetn0' in top
 network.driver('pl_resetn0','PORT/pl_resetn0')
 names=('FDPE_27/Q','FDPE_29/Q','PORT/pl_resetn0');checks=[]
 for i in range(6,26,2):
  pin=f'FDPE_{i}/PRE';expr=network.expression(pin)
  assert m.variables(expr)==set(names),(pin,m.variables(expr))
  for bits in itertools.product((0,1),repeat=3):
   values=dict(zip(names,bits));expected=bits[0] | bits[1] | (1-bits[2])
   assert m.evaluate(expr,values)==expected,(pin,bits)
  checks.append({'endpoint':pin,'assignments':8,'function':'PS_release_reset OR TX_release_reset OR NOT pl_resetn0'})
 return checks
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('rtl',type=Path);a=p.parse_args()
 n=m.Network(a.capture/'network.tsv');checks=audit(n,a.rtl.read_text())
 # Alter the actual shared LUT INIT; audit must refuse its changed function.
 mutated=m.Network(a.capture/'network.tsv')
 mutated.driver('pl_resetn0','PORT/pl_resetn0')
 cone=n.expression('FDPE_6/PRE');lutcell=n.drivers[n.pins['FDPE_6/PRE']].rsplit('/',1)[0]
 ref,init=mutated.cells[lutcell];assert ref.startswith('LUT');mutated.cells[lutcell]=(ref,"8'h00")
 try:
  expression=mutated.expression('FDPE_6/PRE')
  assert all(m.evaluate(expression,dict(zip(('FDPE_27/Q','FDPE_29/Q','PORT/pl_resetn0'),bits)))==(bits[0]|bits[1]|(1-bits[2])) for bits in itertools.product((0,1),repeat=3))
 except AssertionError:mutation='REFUSED'
 else:raise AssertionError('Changed LUT accepted')
 print(json.dumps({'status':'TEN_CSR_PRE_LUT_TRUTH_TABLES_PASS','checks':checks,'changed_lut_mutant':mutation,'external_input_binding':'Exact top-level pl_resetn0 input and identically named captured net; other missing nets refused','limits':['Arbitrary Q cutpoints, not sequential equivalence','Stopped TX with TX release reset high keeps common PRE high even after PS release, by Boolean identity only','No new stopped-clock simulation or physical reset/CDC timing credit'],'next':'Exercise actual LiteX with_common_rst FIFO reset assertion/release with stopped PS/TX clocks and vendor FDPE lowering'},indent=2))
