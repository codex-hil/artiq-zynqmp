"""Bounded active-sampling decoder; LGPL-3.0-or-later."""
import re
from check_dma_observer_snapshot import ADDRESSES
SAMPLE_COUNT=128

def parse(text):
    lines=text.splitlines()
    if lines.count('DMA_ACTIVE_BEGIN')!=1 or lines.count('DMA_ACTIVE_END')!=1:
        raise ValueError('Incomplete/duplicate active frame')
    start,end=lines.index('DMA_ACTIVE_BEGIN'),lines.index('DMA_ACTIVE_END');rows=[]
    for i,line in enumerate(lines):
        if not line.startswith('DMA_ACTIVE '):continue
        m=re.fullmatch(r'DMA_ACTIVE ([0-9]+) 0x([0-9a-fA-F]{8}) 0x([0-9a-fA-F]{8})',line)
        if not m or not start<i<end:raise ValueError('Malformed active row')
        rows.append((int(m[1]),int(m[2],16),int(m[3],16)))
    if [(s,a) for s,a,v in rows]!=[(s,a) for s in range(SAMPLE_COUNT) for a in ADDRESSES]:raise ValueError('Wrong active sample inventory')
    counts=[rows[i][2] for i in range(0,len(rows),2)];flags=[rows[i][2] for i in range(1,len(rows),2)]
    if any(v>127 for v in counts) or any(v!=0 for v in flags):raise ValueError('Counter overflow/flags/error/epoch observed')
    seen=any(counts)
    return dict(status='NONZERO_SAMPLES_OBSERVED' if seen else 'INCONCLUSIVE_NO_NONZERO_SAMPLE',
                hardware_executed=False,nonzero_samples=sum(v>0 for v in counts),
                max_outstanding=max(counts),samples=counts,destructive_test_allowed=False,
                limits='Sequential finite sampling; workload overlap and final idle probe required separately. No PS drain/epoch qualification.')
