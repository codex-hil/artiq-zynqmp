#!/usr/bin/env python3
"""Offline CSU DMA status plan/decoder, not ownership; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
from pathlib import Path
from plan_zdma_snapshot import macro

ADDRESSES=(0xffc80008,0xffc80808)


def plan(parameters,header):
    checks=[(parameters,'XPAR_XCSUDMA_NUM_INSTANCES',1),(parameters,'XPAR_XCSUDMA_0_BASEADDR',0xffc80000),
            (header,'XCSUDMA_STS_OFFSET',8),(header,'XCSUDMA_OFFSET_DIFF',0x800),
            (header,'XCSUDMA_STS_BUSY_MASK',1),(header,'XCUSDMA_STS_OUTSTDG_MASK',0x1e),
            (header,'XCUSDMA_STS_OUTSTDG_SHIFT',1),(header,'XCSUDMA_STS_FIFO_LEVEL_MASK',0x1fe0),
            (header,'XCSUDMA_STS_FIFO_LEVEL_SHIFT',5),(header,'XCSUDMA_STS_DONE_CNT_MASK',0xe000),
            (header,'XCSUDMA_STS_DONE_CNT_SHIFT',13)]
    for text,name,value in checks:
        if macro(text,name)!=value:raise ValueError('Changed CSU layout/field '+name)
    return dict(status='OFFLINE_CSU_STATUS_PLAN_NOT_EXECUTED',hardware_executed=False,
                addresses=[hex(a) for a in ADDRESSES],samples=2,width_bits=32,
                destructive_test_allowed=False,
                limits='STS only. No SIZE/start/reset/interrupt acknowledge writes. Done count is not an error-free-transfer claim; no live ownership proven.')


def decode(samples):
    if not isinstance(samples,list) or len(samples)!=2:raise ValueError('Two samples required')
    for s in samples:
        if not isinstance(s,dict) or set(s)!=set(ADDRESSES) or any(type(v) is not int or not 0<=v<=0xffffffff for v in s.values()):
            raise ValueError('Exact complete32-bit CSU status set required')
    rows=[]
    for channel,a in enumerate(ADDRESSES):
        raw=[s[a] for s in samples]
        rows.append(dict(channel=channel,address=hex(a),raw=raw,busy=[bool(v&1) for v in raw],
                         outstanding=[(v&0x1e)>>1 for v in raw],fifo_level=[(v&0x1fe0)>>5 for v in raw],
                         unacknowledged_done=[(v&0xe000)>>13 for v in raw],unknown_bits=[v&0xffff0000 for v in raw],
                         quiet_fields_observed=raw[0]==raw[1] and raw[0]&0xffff1fff==0))
    return dict(status='SUPPLIED_CSU_STATUS_DECODED_NOT_OWNERSHIP',hardware_executed=False,channels=rows,
                all_quiet_fields=all(r['quiet_fields_observed'] for r in rows),destructive_test_allowed=False,
                limits='Momentary busy/outstanding/FIFO fields only. Done/interrupt flags not acknowledged; errors not cleared or fully diagnosed. No exclusive ownership or DDR admission.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('parameters','header','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=plan(a.parameters.read_text(),a.header.read_text())
    r['input_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.parameters,a.header)}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
