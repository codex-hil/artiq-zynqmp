#!/usr/bin/env python3
"""PMU event parser/preflight for inherited-lease collector. LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from plan_pmu_events_snapshot import REGISTERS, decode, plan as validate_plan
from test_candidate_runtime_hw import lease,bounded,REPO,CABLE
from check_hw_storage import require_runtime_space
SCRIPTS={'scripts/capture_pmu_events_state.py','scripts/probe_pmu_events_state.tcl','scripts/plan_pmu_events_snapshot.py','scripts/plan_rpu_snapshot.py','scripts/test_candidate_runtime_hw.py','scripts/check_hw_storage.py','scripts/check_remote_rtio_build.py'}
def parse(text):
    lines = text.splitlines()
    if lines.count('PMUEVENT_BEGIN') != 1 or lines.count('PMUEVENT_END') != 1:
        raise ValueError('Incomplete/duplicate PMUEVENT frame')
    begin, end = lines.index('PMUEVENT_BEGIN'), lines.index('PMUEVENT_END')
    rows = []
    for i, line in enumerate(lines):
        if not line.startswith('PMUEVENT '):
            continue
        m = re.fullmatch(r'PMUEVENT ([01]) (\w+) 0x([0-9a-fA-F]{8}) 0x([0-9a-fA-F]{8})', line)
        if not m or not begin < i < end:
            raise ValueError('Malformed/out-of-frame PMUEVENT row')
        rows.append((int(m[1]), m[2], int(m[3], 16), int(m[4], 16)))
    expected = [(s, n, a) for s in range(2) for n, a in REGISTERS.items()]
    if [r[:3] for r in rows] != expected:
        raise ValueError('Unexpected PMUEVENT register sequence')
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
    if len(sources) != 2 or {Path(n).name for n in sources} != {'pmu_iomodule.h', 'pmu_local.h'}:
        raise ValueError('Missing vendor pins')
    for n, h in sources.items():
        if hashlib.sha256(Path(n).read_bytes()).hexdigest() != h:
            raise ValueError('Changed vendor source')
    headers = {Path(n).name: Path(n).read_text() for n in sources}
    expected = validate_plan(headers['pmu_iomodule.h'], headers['pmu_local.h'])
    if {k: v for k, v in plan.items() if k != 'input_sha256'} != expected:
        raise ValueError('Plan differs from validated fixed allowlist')


