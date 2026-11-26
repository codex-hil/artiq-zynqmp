#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Fail-closed inventory controls: callbacks/tails/missing metadata/cycles."""
import importlib.util
from pathlib import Path
p=Path(__file__).with_name('inspect-caller-callgraph.py')
spec=importlib.util.spec_from_file_location('audit',p);audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
fixture='''0000000000400000 <root>:
  400000: 94000004 bl 0x400010 <child>
  400004: d63f0060 blr x3
  400008: 14000006 b 0x400020 <tail>
0000000000400010 <child>:
  400010: 94000000 bl 0x400010 <child>
  400014: 54000060 b.eq 0x400020 <tail>
0000000000400020 <tail>:
  400020: d65f03c0 ret
'''
r=audit.inspect(fixture,{'root':128,'child':32},['root'])['root']
assert set(r['reachable_functions'])=={'root','child','tail'}
assert r['missing_frame_metadata']==['tail']
assert r['unresolved_indirect_sites']['root'][0]['instruction']=='blr x3'
assert r['reachable_functions']['child']['calls']==['child']
assert r['reachable_functions']['child']['tail_branches']==['tail']
assert r['complete_stack_bound_bytes'] is None
try:audit.inspect(fixture,{},['absent'])
except ValueError:pass
else:raise AssertionError('missing root accepted')
try:audit.inspect('0000000000400000 <root>:\n  400000: 94000000 bl 0x500000',{},['root'])
except ValueError:pass
else:raise AssertionError('unresolved direct edge accepted')
print('CALLGRAPH_INVENTORY_CONTROLS_PASS')
