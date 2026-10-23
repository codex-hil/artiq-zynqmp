#!/usr/bin/env python3
"""Leased PERIPHERAL register capture; offline default. LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from plan_peripheral_dma_snapshot import REGISTERS, decode, plan as validate_plan
from test_candidate_runtime_hw import lease,bounded,REPO,CABLE
from check_hw_storage import require_runtime_space
SCRIPTS={'scripts/capture_peripheral_dma_state.py','scripts/probe_peripheral_dma_state.tcl','scripts/plan_peripheral_dma_snapshot.py','scripts/plan_zdma_snapshot.py','scripts/test_candidate_runtime_hw.py','scripts/check_hw_storage.py','scripts/check_remote_rtio_build.py'}
def parse(text):
    lines = text.splitlines()
    if lines.count('PERIPHERAL_BEGIN') != 1 or lines.count('PERIPHERAL_END') != 1:
        raise ValueError('Incomplete/duplicate PERIPHERAL frame')
    begin, end = lines.index('PERIPHERAL_BEGIN'), lines.index('PERIPHERAL_END')
    rows = []
    for i, line in enumerate(lines):
        if not line.startswith('PERIPHERAL '):
            continue
        m = re.fullmatch(r'PERIPHERAL ([01]) (\w+) 0x([0-9a-fA-F]{8}) 0x([0-9a-fA-F]{8})', line)
        if not m or not begin < i < end:
            raise ValueError('Malformed/out-of-frame PERIPHERAL row')
        rows.append((int(m[1]), m[2], int(m[3], 16), int(m[4], 16)))
    expected = [(s, n, a) for s in range(2) for n, a in REGISTERS.items()]
    if [r[:3] for r in rows] != expected:
        raise ValueError('Unexpected PERIPHERAL register sequence')
    samples = [{}, {}]
    for s, n, a, v in rows:
        samples[s][n] = v
    return decode(samples)


def preflight(path):
    m=json.loads(path.read_text())
    if set(m.get('script_sha256',{}))!=SCRIPTS:raise ValueError('Missing script pins')
    for n,h in m['script_sha256'].items():
        if hashlib.sha256((REPO/n).read_bytes()).hexdigest()!=h:raise ValueError('Changed script '+n)
    p=Path(m['plan']['path'])
    if hashlib.sha256(p.read_bytes()).hexdigest()!=m['plan']['sha256']:raise ValueError('Changed read plan')
    plan=json.loads(p.read_text())
    sources = plan.get('input_sha256', {})
    if len(sources) != 4 or {Path(n).name for n in sources} != {'xparameters.h', 'xemacps_hw.h', 'xsdps_hw.h', 'xqspipsu_hw.h'}:
        raise ValueError('Missing vendor pins')
    for n, h in sources.items():
        if hashlib.sha256(Path(n).read_bytes()).hexdigest() != h:
            raise ValueError('Changed vendor source')
    headers = {Path(n).name: Path(n).read_text() for n in sources}
    expected = validate_plan(headers)
    if {k: v for k, v in plan.items() if k != 'input_sha256'} != expected:
        raise ValueError('Plan differs from validated fixed allowlist')


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
                cmd=['vivado-container','shell','-c','exec "$@"','bash','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',str(REPO/'scripts/probe_peripheral_dma_state.tcl'),a.server,CABLE]
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
