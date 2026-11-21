#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Run static AArch64 Linux-user harness ONLY; never load a board."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);modes=p.add_mutually_exclusive_group();modes.add_argument('--route',action='store_true');modes.add_argument('--full-setup',action='store_true');modes.add_argument('--cooperative-setup',action='store_true');modes.add_argument('--foreground',action='store_true');modes.add_argument('--resumable',action='store_true');modes.add_argument('--async-setup',action='store_true');modes.add_argument('--guarded-start',action='store_true');modes.add_argument('--static-caller',action='store_true');p.add_argument('--expected-hashes',type=Path);a=p.parse_args();root=a.artifacts.resolve()
(root/'execution-results.json').write_text(json.dumps({'status':'INCOMPLETE','hardware_admitted':False})+'\n')
q=Path('/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/bin/qemu-aarch64')
env=dict(os.environ,LD_LIBRARY_PATH='/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/lib/x86_64-linux-gnu')
results={}
cases=[('normal',0,'A53_CODEC_EMULATION_PASS calls=11334'),('panic',101,'A53_CODEC_EMULATOR_PANIC')]
if a.static_caller:cases.append(('static-caller-negative',99,''))
if a.guarded_start:cases.append(('guarded-start-negative',99,''))
if a.async_setup:cases.append(('async-setup-negative',99,''))
if a.resumable:cases.append(('resumable-negative',99,''))
if a.foreground:cases.append(('foreground-negative',99,''))
if a.cooperative_setup:cases.append(('cooperative-negative',99,''))
if a.full_setup:cases.append(('setup-negative',99,''))
if a.route:cases.append(('route-negative',99,''))
expected={}
if a.expected_hashes:
 for line in a.expected_hashes.read_text().splitlines():
  digest,name=line.split();expected[name]=digest
 for variant,_,_ in cases:
  name='codec-'+variant+'.elf'
  assert name in expected and hashlib.sha256((root/name).read_bytes()).hexdigest()==expected[name],('ELF hash mismatch',name)
for variant,code,marker in cases:
 r=subprocess.run([str(q),'-cpu','cortex-a53',str(root/('codec-'+variant+'.elf'))],env=env,capture_output=True,text=True,timeout=30)
 (root/(variant+'-execution.log')).write_text(r.stdout+r.stderr)
 assert r.returncode==code,(variant,r.returncode,r.stdout,r.stderr)
 assert marker in r.stdout
 if variant!='normal':assert 'A53_CODEC_EMULATION_PASS' not in r.stdout
 if a.route and variant=='normal':assert 'A53_ROUTE_EMULATION_PASS faults=63 controls=4' in r.stdout
 if a.full_setup and variant=='normal':assert 'A53_FULL_SETUP_EMULATION_PASS cases=16 sends=259 pops=260' in r.stdout
 if a.cooperative_setup and variant=='normal':assert 'A53_COOPERATIVE_SETUP_EMULATION_PASS cases=22 healthy_turns=522 max_mock_ops=22' in r.stdout
 if a.foreground and variant=='normal':assert 'A53_FOREGROUND_COMPOSITION_PASS cases=8 healthy_turns=522' in r.stdout
 if a.resumable and variant=='normal':assert 'A53_RESUMABLE_COMPOSITION_PASS cases=69 healthy_turns=550 max_rt_callbacks=1' in r.stdout
 if a.async_setup and variant=='normal':assert 'A53_ASYNC_SETUP_PASS cases=27 healthy_turns=8827 max_callbacks=1' in r.stdout
 if a.guarded_start and variant=='normal':assert 'A53_GUARDED_START_PASS cases=24 healthy_turns=8830 max_callbacks=1' in r.stdout
 if a.static_caller and variant=='normal':assert 'A53_STATIC_CALLER_PASS turns=8830 max_callbacks=1 single_use=1' in r.stdout
 if variant=='static-caller-negative':assert 'A53_STATIC_CALLER_PASS' not in r.stdout
 if variant=='guarded-start-negative':assert 'A53_GUARDED_START_PASS' not in r.stdout
 if variant=='async-setup-negative':assert 'A53_ASYNC_SETUP_PASS' not in r.stdout
 if variant=='resumable-negative':assert 'A53_RESUMABLE_COMPOSITION_PASS' not in r.stdout
 if variant=='foreground-negative':assert 'A53_FOREGROUND_COMPOSITION_PASS' not in r.stdout
 if variant=='cooperative-negative':assert 'A53_COOPERATIVE_SETUP_EMULATION_PASS' not in r.stdout
 if variant=='setup-negative':assert 'A53_FULL_SETUP_EMULATION_PASS' not in r.stdout
 if variant=='route-negative':assert 'A53_ROUTE_EMULATION_PASS' not in r.stdout
 results[variant]={'exit_code':r.returncode,'marker':marker,'elf_sha256':hashlib.sha256((root/('codec-'+variant+'.elf')).read_bytes()).hexdigest()}
report={'status':('AARCH64_STATIC_CALLER_AND_ASSERTION_NEGATIVE_PASS' if a.static_caller else 'AARCH64_GUARDED_START_24_CASES_AND_ASSERTION_NEGATIVE_PASS' if a.guarded_start else 'AARCH64_WHOLE_ASYNC_SETUP_27_CASES_AND_ASSERTION_NEGATIVE_PASS' if a.async_setup else 'AARCH64_RESUMABLE_COMPOSITION_69_CASES_AND_ASSERTION_NEGATIVE_PASS' if a.resumable else 'AARCH64_FOREGROUND_COMPOSITION_8_CASES_AND_ASSERTION_NEGATIVE_PASS' if a.foreground else 'AARCH64_COOPERATIVE_SETUP_22_CASES_AND_ASSERTION_NEGATIVE_PASS' if a.cooperative_setup else 'AARCH64_FULL_CANONICAL_SETUP_16_CASES_AND_ASSERTION_NEGATIVE_PASS' if a.full_setup else 'AARCH64_FULL_ROUTE_63_FAULTS_AND_ASSERTION_NEGATIVE_PASS' if a.route else 'AARCH64_QEMU_USER_CODEC_11334_CALLS_AND_FORCED_HOOK_NEGATIVE_PASS'),'runs':results,'pre_execution_hashes_verified':bool(a.expected_hashes),'qemu_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'version':subprocess.check_output([str(q),'--version'],env=env,text=True).splitlines()[0],'limits':['Linux-user syscalls test only; not board panic/runtime/CPU role behavior','Forced negative calls hook directly; not proof that every Rust panic path or CPU exception reaches it','No target MMIO, hardware, firmware deployment or platform clock/reset proof']}
(root/'execution-results.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
