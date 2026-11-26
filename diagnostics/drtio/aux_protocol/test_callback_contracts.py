#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Frozen callback-contract negative controls; never executes target firmware."""
import argparse,importlib.util,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--helpers',type=Path,required=True);a=p.parse_args()
spec=importlib.util.spec_from_file_location('contracts',Path(__file__).with_name('inspect-callback-contracts.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
text,frames=m.load_inputs(a.evidence);helpers=json.loads(a.helpers.read_text())
r=m.bind(text,dict(frames),helpers);assert len(r['sites'])==13;assert r['conditional_frame_sums']['mfc_poll']['conditional_sum_bytes']==352
assert r['complete_production_stack_bound_bytes'] is None

def refuse(t,f):
 try:m.bind(t,dict(f),helpers)
 except AssertionError:return
 raise AssertionError('Unsafe contract accepted')
# A changed call register cannot silently inherit the old role mapping.
line=next(l for l in text.splitlines() if '401a08:' in l)
refuse(text.replace(line,line.replace('blr\tx1','blr\tx4')),frames)
# Unknown target frame must remain a blocker, not silently count as zero.
f=dict(frames);del f['write_reg'];refuse(text,f)
# A mock callback reentering the foreground owner must be refused.
refuse(text.replace('0000000000400390 <read_reg>:', '0000000000400390 <read_reg>:\n  40038c: 94000000 bl 0x4022d0 <mfc_poll>'),frames)
print('CALLBACK_CONTRACT_BASELINE_AND_THREE_MUTANT_REFUSALS_PASS')
