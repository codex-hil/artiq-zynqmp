#!/usr/bin/env python3
"""Bounded leased read-only ZDMA capture; defaults offline. LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from plan_zdma_snapshot import BASES,OFFSETS,decode
from test_candidate_runtime_hw import lease,bounded,REPO,CABLE
from check_hw_storage import require_runtime_space

SCRIPTS={'scripts/capture_zdma_status.py','scripts/probe_zdma_status.tcl','scripts/plan_zdma_snapshot.py',
         'scripts/test_candidate_runtime_hw.py','scripts/check_hw_storage.py','scripts/check_remote_rtio_build.py'}


def parse(text):
    lines=text.splitlines()
    if lines.count('ZDMA_BEGIN')!=1 or lines.count('ZDMA_END')!=1:raise ValueError('Incomplete/duplicate capture frame')
    begin=lines.index('ZDMA_BEGIN');end=lines.index('ZDMA_END')
    if begin>=end:raise ValueError('Reversed capture frame')
    records=[]
    for i,line in enumerate(lines):
        if not line.startswith('ZDMA '):continue
        if not begin<i<end:raise ValueError('Record outside capture frame')
        m=re.fullmatch(r'ZDMA ([01]) ([0-9]+) (status|control2) 0x([0-9a-fA-F]{8}) 0x([0-9a-fA-F]{8})',line)
        if not m:raise ValueError('Malformed ZDMA row')
        records.append((int(m[1]),int(m[2]),m[3],int(m[4],16),int(m[5],16)))
    expected=[(s,i,n,b+o) for s in range(2) for i,b in enumerate(BASES) for n,o in OFFSETS.items()]
    if [r[:4] for r in records]!=expected:raise ValueError('Unexpected/missing/duplicate/out-of-order register')
    samples=[{},{}]
    for sample,channel,name,address,value in records:samples[sample][address]=value
    return decode(samples)


def preflight(inputs):
    m=json.loads(inputs.read_text())
    if set(m.get('script_sha256',{}))!=SCRIPTS:raise ValueError('Missing execution dependencies')
    for name,digest in m['script_sha256'].items():
        if hashlib.sha256((REPO/name).read_bytes()).hexdigest()!=digest:raise ValueError('Changed execution script: '+name)
    p=Path(m['plan']['path'])
    if hashlib.sha256(p.read_bytes()).hexdigest()!=m['plan']['sha256']:raise ValueError('Changed register plan')
    plan=json.loads(p.read_text())
    expected=[dict(channel=i,register=n,address=hex(b+o),width_bits=32) for i,b in enumerate(BASES) for n,o in OFFSETS.items()]
    if plan['registers']!=expected:raise ValueError('Plan differs from fixed read allowlist')
    if len(plan.get('input_sha256',{}))!=2 or {Path(n).name for n in plan['input_sha256']}!={'xparameters.h','xzdma_hw.h'}:raise ValueError('Missing vendor input binding')
    for name,digest in plan['input_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:raise ValueError('Changed vendor source')
    return m


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--server');a=p.parse_args()
    preflight(a.inputs)
    if a.output.exists():raise ValueError('Use fresh output')
    if a.execute and not a.server:p.error('--execute requires --server')
    if a.execute:require_runtime_space(a.output,REPO)
    a.output.mkdir(parents=True)
    if not a.execute:
        (a.output/'results.json').write_text(json.dumps(dict(status='PREFLIGHT_PASS_NO_HW',hardware_executed=False))+'\n');return 0
    result=dict(status='FAIL',hardware_executed=False)
    try:
        with lease() as held:
            preflight(a.inputs);require_runtime_space(a.output,REPO)
            env=os.environ.copy();env['GENESYS_LEASE_FD']=str(held.fileno())
            command=['vivado-container','shell','-c','exec "$@"','bash','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',str(REPO/'scripts/probe_zdma_status.tcl'),a.server,CABLE]
            result['hardware_executed']=True
            code,text=bounded(command,45,env,held.fileno())
            (a.output/'snapshot.log').write_text(text)
            if code:raise RuntimeError('Read-only snapshot failed; no fallback/force access')
            result.update(status='READ_ONLY_CAPTURE_COMPLETE',decoded=parse(text),cable=CABLE,
                          input_sha256=hashlib.sha256(a.inputs.read_bytes()).hexdigest(),raw_sha256=hashlib.sha256(text.encode()).hexdigest())
    except subprocess.TimeoutExpired as error:
        partial=error.output or ''
        if isinstance(partial,bytes):partial=partial.decode(errors='replace')
        (a.output/'snapshot.log').write_text(partial)
        result['error']='TIMEOUT: read-only snapshot exceeded45s'
    except Exception as error:result['error']=str(error)
    finally:(a.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0 if result['status']=='READ_ONLY_CAPTURE_COMPLETE' else 1


if __name__=='__main__':raise SystemExit(main())
