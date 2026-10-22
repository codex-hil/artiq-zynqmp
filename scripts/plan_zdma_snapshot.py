#!/usr/bin/env python3
"""Plan PS ZDMA status reads offline, never quiescence admission; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import re
from pathlib import Path

BASES=tuple(0xfd500000+i*0x10000 for i in range(8))+tuple(0xffa80000+i*0x10000 for i in range(8))
OFFSETS={'status':0x11c,'control2':0x200}


def macro(text,name):
    rows=re.findall(r'^#define\s+'+re.escape(name)+r'\s+\(?((?:0[xX][0-9a-fA-F]+)|(?:[0-9]+))[uU]?\)?\s*(?:/\*.*)?$',text,re.M)
    if len(rows)!=1:raise ValueError('Missing/ambiguous numeric macro '+name)
    return int(rows[0],0)


def plan(parameters,header):
    if macro(parameters,'XPAR_XZDMA_NUM_INSTANCES')!=16:raise ValueError('Expected all16PS channels')
    found=tuple(macro(parameters,f'XPAR_XZDMA_{i}_BASEADDR') for i in range(16))
    if found!=BASES:raise ValueError('Unexpected channel layout')
    for name,value in [('XZDMA_CH_STS_OFFSET',0x11c),('XZDMA_CH_CTRL2_OFFSET',0x200),('XZDMA_STS_ALL_MASK',3),('XZDMA_CH_CTRL2_EN_MASK',1)]:
        if macro(header,name)!=value:raise ValueError('Changed register semantics '+name)
    return dict(status='OFFLINE_ZDMA_READ_PLAN_NOT_EXECUTED',hardware_executed=False,
                registers=[dict(channel=i,register=name,address=hex(base+offset),width_bits=32) for i,base in enumerate(BASES) for name,offset in OFFSETS.items()],
                destructive_test_allowed=False,
                limits='CH_STS and CH_CTRL2 only; no ISR/interrupt/descriptor/control writes. No proof of accessibility, current ownership or other masters. Even quiet fields do not admit DDR tests.')


def decode(samples):
    addresses={base+offset for base in BASES for offset in OFFSETS.values()}
    if not isinstance(samples,list) or len(samples)!=2:raise ValueError('Require two complete observations')
    for sample in samples:
        if not isinstance(sample,dict) or set(sample)!=addresses:raise ValueError('Unexpected/missing register set')
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in sample.values()):raise ValueError('Invalid32-bit register')
    rows=[]
    for i,base in enumerate(BASES):
        statuses=[s[base+0x11c] for s in samples];controls=[s[base+0x200] for s in samples]
        rows.append(dict(channel=i,status_raw=statuses,control2_raw=controls,
                         state=[v&3 for v in statuses],enabled=[bool(v&1) for v in controls],
                         quiet_fields_observed=statuses[0]==statuses[1] and (statuses[0]&3)==0 and controls==[0,0]))
    return dict(status='SUPPLIED_ZDMA_FIELDS_DECODED_NOT_OWNERSHIP',hardware_executed=False,
                channels=rows,all_quiet_fields=all(r['quiet_fields_observed'] for r in rows),destructive_test_allowed=False,
                limits='Supplied-data interpretation only. Sampling quiet/disabled fields does not establish bus drain, reset ordering, exclusive ownership or physical-device provenance.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('parameters','header','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=plan(a.parameters.read_text(),a.header.read_text())
    r['input_sha256']={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (a.parameters,a.header)}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
