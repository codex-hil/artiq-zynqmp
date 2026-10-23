#!/usr/bin/env python3
"""Validate optional diagnostic observer reads, never drain admission; LGPL-3.0-or-later."""
import json,re
from pathlib import Path
ADDRESSES=(0xa0003000,0xa0003004)


def check_map(path):
    registers=json.loads(Path(path).read_text())['registers']
    for name,address,bits in [('dma_observer_outstanding',ADDRESSES[0],7),('dma_observer_flags',ADDRESSES[1],4)]:
        expected=dict(address=address,words=1,bits=bits,word_order='big',word_bytes=4)
        if registers.get(name)!=expected:raise ValueError('Wrong observer CSR map '+name)


def parse(text):
    lines=text.splitlines()
    if lines.count('DMA_OBSERVER_BEGIN')!=1 or lines.count('DMA_OBSERVER_END')!=1:
        raise ValueError('Incomplete/duplicate observer frame')
    start,end=lines.index('DMA_OBSERVER_BEGIN'),lines.index('DMA_OBSERVER_END');rows=[]
    for i,line in enumerate(lines):
        if not line.startswith('DMA_OBSERVER '):continue
        m=re.fullmatch(r'DMA_OBSERVER ([01]) 0x([0-9a-fA-F]{8}) 0x([0-9a-fA-F]{8})',line)
        if not m or not start<i<end:raise ValueError('Malformed/out-of-frame observer row')
        rows.append((int(m[1]),int(m[2],16),int(m[3],16)))
    if [(s,a) for s,a,v in rows]!=[(s,a) for s in range(2) for a in ADDRESSES]:
        raise ValueError('Wrong observer sequence')
    samples=[dict(outstanding=rows[i][2],flags=rows[i+1][2]) for i in (0,2)]
    for s in samples:
        if s['outstanding']>127 or s['flags']>15:raise ValueError('Unknown observer bits')
        if s['flags']&12:raise ValueError('Unexpected quiet/epoch assertion in unqualified design')
    return dict(status='OBSERVER_READS_DECODED_NOT_DRAIN',hardware_executed=False,
                samples=samples,stable=samples[0]==samples[1],
                error_observed=any(s['flags']&3 for s in samples),
                zero_count_observed=all(s['outstanding']==0 for s in samples),
                epoch_qualified=False,destructive_test_allowed=False,
                limits='Zero local count is not historical PS drain or core/PMU ownership proof.')
