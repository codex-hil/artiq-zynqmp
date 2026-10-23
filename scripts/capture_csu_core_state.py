#!/usr/bin/env python3
"""Leased CSU status/core-metadata capture; offline default. LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from plan_csu_dma_snapshot import ADDRESSES,decode
from test_candidate_runtime_hw import lease,bounded,REPO,CABLE
from check_hw_storage import require_runtime_space
SCRIPTS={'scripts/capture_csu_core_state.py','scripts/probe_csu_core_state.tcl','scripts/plan_csu_dma_snapshot.py','scripts/plan_zdma_snapshot.py','scripts/test_candidate_runtime_hw.py','scripts/check_hw_storage.py','scripts/check_remote_rtio_build.py'}
CORES=[f'Cortex-A53 #{i}' for i in range(4)]+[f'Cortex-R5 #{i}' for i in range(2)]


def parse(text):
    lines=text.splitlines()
    if lines.count('CSU_BEGIN')!=1 or lines.count('CSU_END')!=1:raise ValueError('Incomplete/duplicate CSU frame')
    begin=lines.index('CSU_BEGIN');end=lines.index('CSU_END');rows=[]
    for i,line in enumerate(lines):
        if not line.startswith('CSU '):continue
        m=re.fullmatch(r'CSU ([01]) 0x([0-9a-fA-F]{8}) 0x([0-9a-fA-F]{8})',line)
        if not m or not begin<i<end:raise ValueError('Malformed/out-of-frame CSU row')
        rows.append((int(m[1]),int(m[2],16),int(m[3],16)))
    if [r[:2] for r in rows]!=[(s,a) for s in range(2) for a in ADDRESSES]:raise ValueError('Unexpected CSU register sequence')
    samples=[{},{}]
    for s,a,v in rows:samples[s][a]=v
    cores=[]
    for line in lines:
        if not line.startswith('CORE_METADATA '):continue
        m=re.fullmatch(r'CORE_METADATA (Cortex-(?:A53|R5) #[0-3]) (.+)',line)
        if not m:raise ValueError('Malformed core metadata')
        cores.append(dict(name=m[1],raw=m[2],ownership='NOT_PROVEN'))
    if [r['name'] for r in cores]!=CORES:raise ValueError('Missing/duplicate core inventory')
    return dict(csu=decode(samples),cores=cores,destructive_test_allowed=False)


def preflight(path):
    m=json.loads(path.read_text())
    if set(m.get('script_sha256',{}))!=SCRIPTS:raise ValueError('Missing script pins')
    for n,h in m['script_sha256'].items():
        if hashlib.sha256((REPO/n).read_bytes()).hexdigest()!=h:raise ValueError('Changed script '+n)
    p=Path(m['plan']['path'])
    if hashlib.sha256(p.read_bytes()).hexdigest()!=m['plan']['sha256']:raise ValueError('Changed read plan')
    plan=json.loads(p.read_text())
    if plan['addresses']!=[hex(a) for a in ADDRESSES] or plan['samples']!=2 or plan['width_bits']!=32:raise ValueError('Plan differs from fixed allowlist')
    if len(plan.get('input_sha256',{}))!=2 or {Path(n).name for n in plan['input_sha256']}!={'xparameters.h','xcsudma_hw.h'}:raise ValueError('Missing vendor pins')
    for n,h in plan['input_sha256'].items():
        if hashlib.sha256(Path(n).read_bytes()).hexdigest()!=h:raise ValueError('Changed vendor source')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true');p.add_argument('--server');a=p.parse_args()
    preflight(a.inputs)
    if a.output.exists():raise ValueError('Use fresh output')
    if a.execute and not a.server:p.error('--execute requires server')
    if a.execute:require_runtime_space(a.output,REPO)
    a.output.mkdir(parents=True);result=dict(status='PREFLIGHT_PASS_NO_HW',hardware_executed=False)
    if a.execute:
        result['status']='FAIL'
        try:
            with lease() as held:
                preflight(a.inputs);require_runtime_space(a.output,REPO)
                env=os.environ.copy();env['GENESYS_LEASE_FD']=str(held.fileno())
                result['hardware_executed']=True
                cmd=['vivado-container','shell','-c','exec "$@"','bash','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',str(REPO/'scripts/probe_csu_core_state.tcl'),a.server,CABLE]
                code,text=bounded(cmd,45,env,held.fileno());(a.output/'snapshot.log').write_text(text)
                if code:raise RuntimeError('Read-only capture failed; no force-access fallback')
                result.update(status='READ_ONLY_CAPTURE_COMPLETE',decoded=parse(text),cable=CABLE,lock=str(Path.home()/'.cache'/('genesys-'+CABLE+'.lock')),inputs_sha256=hashlib.sha256(a.inputs.read_bytes()).hexdigest(),raw_sha256=hashlib.sha256(text.encode()).hexdigest())
        except subprocess.TimeoutExpired as error:
            raw=error.output or '';raw=raw.decode(errors='replace') if isinstance(raw,bytes) else raw
            (a.output/'snapshot.log').write_text(raw);result['error']='TIMEOUT45s'
        except Exception as error:result['error']=str(error)
    (a.output/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return 1 if result['status']=='FAIL' else 0


if __name__=='__main__':raise SystemExit(main())
