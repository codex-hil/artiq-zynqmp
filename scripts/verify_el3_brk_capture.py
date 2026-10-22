#!/usr/bin/env python3
"""Verify supplied deliberate BRK capture, not normal success; LGPL-3.0-or-later."""
import argparse
import json
import re
from pathlib import Path


def verify(text):
    names={'x'+str(i) for i in range(10)}|{'x'+str(i) for i in range(14,22)}
    pairs=re.findall(r'^EXCEPTION_REGISTER (x\d+) (\d+)$',text,re.M)
    if len(pairs)!=len(names) or {k for k,v in pairs}!=names:
        raise ValueError('Incomplete/duplicate BRK register capture')
    regs={k:int(v) for k,v in pairs}
    if any(v>=1<<64 for v in regs.values()):raise ValueError('Oversized register')
    for name,value in {'x14':4,'x15':0xf3,'x16':12,'x17':0xf2000053,'x19':0xfffc884c}.items():
        if regs[name]!=value:raise ValueError('Unexpected BRK '+name)
    states=re.findall(r'^EXCEPTION_ENTRY_STATE (.+)$',text,re.M)
    if len(states)!=1:raise ValueError('Missing/duplicate entry state')
    cells=states[0].split()
    expected={'pc','currentel','sctlr_el3','daif','mpidr_el1','cpsr'}
    if len(cells)!=12 or set(cells[::2])!=expected or not all(v.isascii() and v.isdecimal() for v in cells[1::2]):
        raise ValueError('Malformed entry state')
    state={cells[i]:int(cells[i+1]) for i in range(0,12,2)}
    if any(v>=1<<64 for v in state.values()):raise ValueError('Oversized entry state')
    if state['currentel']!=12 or state['cpsr']&31!=13 or state['sctlr_el3']&0x1005 or state['mpidr_el1']&255:
        raise ValueError('Invalid original entry')
    if state['daif']!=state['cpsr']&0x3c0 or state['daif']&0x2c0!=0x2c0:
        raise ValueError('Original exception masks invalid')
    if regs['x20']&31!=13 or regs['x20']&0x3c0!=state['daif']:
        raise ValueError('Saved original PSTATE mismatch')
    for name,value in {'EXCEPTION_ARMED_VBAR':0xfffc8000,'EXCEPTION_STOP_PC':0xfffc8878}.items():
        if re.findall(r'^'+name+r' (\d+)$',text,re.M)!=[str(value)]:raise ValueError('Wrong '+name)
    if text.splitlines().count('EXPECTED_BRK_TRANSPORT_CAPTURED')!=1 or 'EXCEPTION_OBSERVER_NORMAL_COMPLETE' in text:
        raise ValueError('Wrong completion class')
    return dict(status='EXPECTED_BRK_CAPTURE_RESTORE_REQUIRED',hardware_executed=False,
                registers=regs,entry_state=state,normal_observation_pass=False,
                destructive_test_allowed=False,
                limits='Supplied synchronous BRK result only, not provenance, completed restoration, asynchronous SError or DDR integrity. FAR is raw, not a valid BRK fault address claim.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('log',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.log.read_text()),indent=2))
