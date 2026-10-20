"""Board-bound clock restore admission, no hardware. LGPL-3.0-or-later."""
import hashlib,json,re
from pathlib import Path
DNA={'KASLI01':0x007865085f704854,'KASLI03':0x0048458a64b04854}


def validate(board,plan,baseline_file,source):
    raw=Path(baseline_file).read_bytes();baseline=json.loads(raw)
    if (board not in DNA or plan.get('board')!=board or baseline.get('board')!=board or
        int(baseline.get('dna','0'),16)!=DNA[board]):raise ValueError('Clock board/DNA binding mismatch')
    if hashlib.sha256(raw).hexdigest()!=plan.get('snapshot_sha256'):
        raise ValueError('Restoration baseline hash mismatch')
    if baseline.get('si_source_sha256')!=hashlib.sha256(source.encode()).hexdigest():
        raise ValueError('Driver differs from restoration baseline')
    if baseline.get('status')!='PASS' or baseline.get('changed_registers'):
        raise ValueError('Stable PASS snapshot required')
    regs=baseline['registers']
    if any(len(v)!=2 or v[0]!=v[1] for v in regs.values()):raise ValueError('Incomplete repeated baseline')
    writable=sorted({int(r) for r in re.findall(r'\bwrite\((\d+)',source)}-{136})
    expected=[dict(register=r,value=regs[str(r)][0]) for r in writable]
    if not expected or plan.get('configuration_to_compare_then_restore')!=expected:
        raise ValueError('Plan must replay exact complete board baseline')
    return baseline
