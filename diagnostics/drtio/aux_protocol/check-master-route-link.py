#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Audit diagnostic relocatable linkage; explicitly requires unbound panic hook."""
import argparse,json
from pathlib import Path

def inspect(header,undefined,defined):
    assert 'AArch64' in header and 'REL (Relocatable file)' in header
    symbols={line.split()[-1] for line in undefined.splitlines() if line.strip()}
    assert symbols=={'aux_master_panic'},symbols
    names={line.split()[-1] for line in defined.splitlines() if line.strip()}
    assert 'aux_master_panic' not in names,'Panic hook silently bound without runtime qualification'
    for name in ('gm_aux_candidate_bind','gm_aux_candidate_route_once','aux_master_leaf_encode','aux_master_routing_ack_decode'):
        assert name in names,name

p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);a=p.parse_args()
h=(a.evidence/'linked-header.txt').read_text();u=(a.evidence/'linked-undefined.txt').read_text();d=(a.evidence/'linked-defined.txt').read_text();inspect(h,u,d)
for hh,uu,dd in [(h,'',d+'\n0 T aux_master_panic\n'),(h,u+'\n U unexpected_runtime_symbol\n',d),(h.replace('AArch64','ARM'),u,d)]:
    try:inspect(hh,uu,dd)
    except AssertionError:pass
    else:raise AssertionError('Link contract mutant accepted')
print(json.dumps({'status':'DIAGNOSTIC_RELOCATABLE_LINK_CONTRACT_PASS_THREE_MUTANTS_REFUSED','remaining_undefined':['aux_master_panic'],'runtime_admitted':False,'hardware_admitted':False,'reason':'No reviewed panic execution context, independent recovery or firmware startup/memory binding'},indent=2))
