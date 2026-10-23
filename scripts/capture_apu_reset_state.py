#!/usr/bin/env python3
"""APU reset parser/preflight for inherited-lease collector. LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from plan_apu_reset_snapshot import ADDRESS, decode, plan as validate_plan
from test_candidate_runtime_hw import lease,bounded,REPO,CABLE
from check_hw_storage import require_runtime_space
SCRIPTS={'scripts/capture_apu_reset_state.py','scripts/probe_apu_reset_state.tcl','scripts/plan_apu_reset_snapshot.py','scripts/plan_rpu_snapshot.py','scripts/test_candidate_runtime_hw.py','scripts/check_hw_storage.py','scripts/check_remote_rtio_build.py'}
def parse(text):
    lines=text.splitlines()
    if lines.count('APU_BEGIN')!=1 or lines.count('APU_END')!=1:
        raise ValueError('Incomplete/duplicate APU frame')
    start,end=lines.index('APU_BEGIN'),lines.index('APU_END')
    rows=[]
    for i,line in enumerate(lines):
        if not line.startswith('APU '):continue
        m=re.fullmatch(r'APU ([01]) 0xfd1a0104 0x([0-9a-fA-F]{8})',line)
        if not m or not start<i<end:raise ValueError('Malformed/out-of-frame APU row')
        rows.append((int(m[1]),int(m[2],16)))
    if [s for s,v in rows]!=[0,1]:raise ValueError('Wrong APU sequence')
    return decode([v for s,v in rows])


def preflight(path):
    m=json.loads(path.read_text())
    if set(m.get('script_sha256',{}))!=SCRIPTS:raise ValueError('Missing script pins')
    for n,h in m['script_sha256'].items():
        if hashlib.sha256((REPO/n).read_bytes()).hexdigest()!=h:raise ValueError('Changed script '+n)
    p=Path(m['plan']['path'])
    if hashlib.sha256(p.read_bytes()).hexdigest()!=m['plan']['sha256']:raise ValueError('Changed read plan')
    plan=json.loads(p.read_text())
    sources = plan.get('input_sha256', {})
    if len(sources) != 1 or {Path(n).name for n in sources} != {'crf_apb.h'}:
        raise ValueError('Missing vendor pins')
    for n, h in sources.items():
        if hashlib.sha256(Path(n).read_bytes()).hexdigest() != h:
            raise ValueError('Changed vendor source')
    headers = {Path(n).name: Path(n).read_text() for n in sources}
    expected = validate_plan(headers['crf_apb.h'])
    if {k: v for k, v in plan.items() if k != 'input_sha256'} != expected:
        raise ValueError('Plan differs from validated fixed allowlist')


