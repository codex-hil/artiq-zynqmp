#!/usr/bin/env python3
"""Decode measured OCM EL1 registers, never authorize DDR writes; LGPL-3.0-or-later."""
import argparse,json,re
from pathlib import Path


def decode(text,layout):
    if layout.get('status')!='OCM_IMAGE_LAYOUT_PASS_EXECUTION_STATE_NOT_PROVEN':raise ValueError('Require checked OCM layout')
    levels=re.findall(r'REG CurrentEL=(0x[0-9a-fA-F]+) CNTFRQ=(\d+)',text)
    if len(levels)!=1 or int(levels[0][0],16)!=4 or int(levels[0][1])==0:raise ValueError('Missing/invalid EL1/timer report')
    rows=[]
    for line in text.splitlines():
        if line.startswith('REG_EL1 '):rows.extend(re.findall(r'(\w+)=(0x[0-9a-fA-F]+)',line))
    required={'SCTLR','TCR','TTBR0','TTBR1','MAIR','VBAR','SP','PC'}
    if len(rows)!=8 or {k for k,v in rows}!=required:raise ValueError('Missing/duplicate EL1 register')
    r={k:int(v,16) for k,v in rows}
    if any(v>=1<<64 for v in r.values()):raise ValueError('Oversized register value')
    code=[(int(s['start'],16),int(s['start'],16)+s['file_bytes']) for s in layout['load_segments'] if s.get('flags',0)&1]
    lo=int(layout['stack']['start'],16);hi=int(layout['stack']['end_exclusive'],16)
    if not any(a<=r['PC']<b for a,b in code) or not lo<=r['SP']<=hi or r['SP']%16 or not any(a<=r['VBAR']<b for a,b in code) or r['VBAR']%2048:
        raise ValueError('Live PC/SP/vector outside checked OCM layout')
    return dict(status='OCM_EL1_STATE_OBSERVED_NOT_DDR_AUTHORIZATION',hardware_executed=False,
        mmu=bool(r['SCTLR']&1),dcache=bool(r['SCTLR']&4),icache=bool(r['SCTLR']&(1<<12)),
        registers={k:hex(v) for k,v in r.items()},destructive_ddr_test_allowed=False,
        limits='Measured local CPU state only. Does not prove physical DDR geometry, parked other cores, inactive masters or whole-system cache quiescence.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--uart-log',required=True,type=Path);p.add_argument('--layout',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Use fresh output')
    r=decode(a.uart_log.read_text(),json.loads(a.layout.read_text()));a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))

if __name__=='__main__':main()
