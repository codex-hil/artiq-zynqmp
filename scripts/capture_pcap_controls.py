#!/usr/bin/env python3
"""PCAP reset parser/preflight for inherited-lease collector. LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from plan_pcap_controls import REGISTERS, decode, plan as validate_plan
from test_candidate_runtime_hw import lease,bounded,REPO,CABLE
from check_hw_storage import require_runtime_space
SCRIPTS={'scripts/capture_pcap_controls.py','scripts/probe_pcap_controls.tcl','scripts/plan_pcap_snapshot.py','scripts/plan_pcap_controls.py','scripts/plan_rpu_snapshot.py','scripts/test_candidate_runtime_hw.py','scripts/check_hw_storage.py','scripts/check_remote_rtio_build.py'}
def parse(text):
    lines=text.splitlines()
    if lines.count('PCAP_CONTEXT_BEGIN')!=1 or lines.count('PCAP_CONTEXT_END')!=1:
        raise ValueError('Incomplete/duplicate PCAP context frame')
    start,end=lines.index('PCAP_CONTEXT_BEGIN'),lines.index('PCAP_CONTEXT_END')
    rows=[]
    for i,line in enumerate(lines):
        if not line.startswith('PCAP_CONTEXT '):continue
        m=re.fullmatch(r'PCAP_CONTEXT ([01]) (status|reset|control|direction) 0x([0-9a-f]{8}) 0x([0-9a-fA-F]{8})',line)
        if not m or not start<i<end:raise ValueError('Malformed/out-of-frame context row')
        if int(m[3],16)!=REGISTERS[m[2]]:raise ValueError('Wrong register')
        rows.append((int(m[1]),m[2],int(m[4],16)))
    if [(s,n) for s,n,v in rows]!=[(s,n) for s in range(2) for n in REGISTERS]:raise ValueError('Wrong context sequence')
    return decode([{n:v for s,n,v in rows if s==sample} for sample in range(2)])


def preflight(path):
    m=json.loads(path.read_text())
    if set(m.get('script_sha256',{}))!=SCRIPTS:raise ValueError('Missing script pins')
    for n,h in m['script_sha256'].items():
        if hashlib.sha256((REPO/n).read_bytes()).hexdigest()!=h:raise ValueError('Changed script '+n)
    p=Path(m['plan']['path'])
    if hashlib.sha256(p.read_bytes()).hexdigest()!=m['plan']['sha256']:raise ValueError('Changed read plan')
    plan=json.loads(p.read_text())
    sources = plan.get('input_sha256', {})
    if len(sources) != 1 or {Path(n).name for n in sources} != {'xilfpga_pcap.h'}:
        raise ValueError('Missing vendor pins')
    for n, h in sources.items():
        if hashlib.sha256(Path(n).read_bytes()).hexdigest() != h:
            raise ValueError('Changed vendor source')
    headers = {Path(n).name: Path(n).read_text() for n in sources}
    expected = validate_plan(headers['xilfpga_pcap.h'])
    if {k: v for k, v in plan.items() if k != 'input_sha256'} != expected:
        raise ValueError('Plan differs from validated fixed allowlist')


