#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Run static AArch64 Linux-user harness ONLY; never load a board."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);p.add_argument('--route',action='store_true');p.add_argument('--full-setup',action='store_true');a=p.parse_args();root=a.artifacts.resolve()
q=Path('/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/bin/qemu-aarch64')
env=dict(os.environ,LD_LIBRARY_PATH='/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/lib/x86_64-linux-gnu')
results={}
cases=[('normal',0,'A53_CODEC_EMULATION_PASS calls=11334'),('panic',101,'A53_CODEC_EMULATOR_PANIC')]
if a.full_setup:cases.append(('setup-negative',99,''))
if a.route:cases.append(('route-negative',99,''))
for variant,code,marker in cases:
 r=subprocess.run([str(q),'-cpu','cortex-a53',str(root/('codec-'+variant+'.elf'))],env=env,capture_output=True,text=True,timeout=30)
 (root/(variant+'-execution.log')).write_text(r.stdout+r.stderr)
 assert r.returncode==code,(variant,r.returncode,r.stdout,r.stderr)
 assert marker in r.stdout
 if variant!='normal':assert 'A53_CODEC_EMULATION_PASS' not in r.stdout
 if a.route and variant=='normal':assert 'A53_ROUTE_EMULATION_PASS faults=63 controls=4' in r.stdout
 if a.full_setup and variant=='normal':assert 'A53_FULL_SETUP_EMULATION_PASS cases=16 sends=259 pops=260' in r.stdout
 if variant=='setup-negative':assert 'A53_FULL_SETUP_EMULATION_PASS' not in r.stdout
 if variant=='route-negative':assert 'A53_ROUTE_EMULATION_PASS' not in r.stdout
 results[variant]={'exit_code':r.returncode,'marker':marker,'elf_sha256':hashlib.sha256((root/('codec-'+variant+'.elf')).read_bytes()).hexdigest()}
report={'status':('AARCH64_FULL_CANONICAL_SETUP_16_CASES_AND_ASSERTION_NEGATIVE_PASS' if a.full_setup else 'AARCH64_FULL_ROUTE_63_FAULTS_AND_ASSERTION_NEGATIVE_PASS' if a.route else 'AARCH64_QEMU_USER_CODEC_11334_CALLS_AND_FORCED_HOOK_NEGATIVE_PASS'),'runs':results,'qemu_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'version':subprocess.check_output([str(q),'--version'],env=env,text=True).splitlines()[0],'limits':['Linux-user syscalls test only; not board panic/runtime/CPU role behavior','Forced negative calls hook directly; not proof that every Rust panic path or CPU exception reaches it','No target MMIO, hardware, firmware deployment or platform clock/reset proof']}
(root/'execution-results.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
