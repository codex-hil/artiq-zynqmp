#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""A53 source-copy GEM fault -> actual observer -> Rust startup, RAM only."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args();b=a.artifacts
(b/'execution-results.json').write_text('{"status":"INCOMPLETE","hardware_accessed":false}\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();modes=('normal','missing-hook','false-ready');expected={n:sha(b/(n+'.elf')) for n in modes};(b/'preexecution-hashes.json').write_text(json.dumps(expected,indent=2)+'\n')
for name in modes:
 assert not (b/(name+'-undefined.txt')).read_text().strip()
 symbols=subprocess.check_output(['readelf','-sW',str(b/(name+'.elf'))],text=True)
 functions=[f[-1] for l in symbols.splitlines() if len(f:=l.split())>=8 and f[3]=='FUNC']
 assert {'emacps_error_handler','gem_master_main','mns_begin','mns_poll','mns_snapshot','HandleEmacPsError','HandleTxErrors'}<=set(functions)
 assert not any(n.startswith(('Xil_','XScu','XSetup','XEmacPs_')) for n in functions),'Real hardware helper linked'
 text=(b/(name+'-disassembly.txt')).read_text();assert not re.search(r'\b(?:msr|mrs|smc|hvc)\s',text),'Privileged instruction in test image'
q=Path('/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/bin/qemu-aarch64');env=dict(os.environ,LD_LIBRARY_PATH='/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/lib/x86_64-linux-gnu');runs=[]
for case in range(13):
 elf=b/'normal.elf';assert sha(elf)==expected['normal'];r=subprocess.run([str(q),'-cpu','cortex-a53',str(elf),str(case)],env=env,capture_output=True,text=True,timeout=30);(b/('normal-'+str(case)+'.log')).write_text(r.stdout+r.stderr)
 assert r.returncode==0 and r.stdout=='A53_GEM_MASTER_START_PASS\n' and not r.stderr,(case,r.returncode,r.stdout,r.stderr)
 runs.append({'case':case,'exit_code':0})
for name,case in [('missing-hook',3),('false-ready',8)]:
 elf=b/(name+'.elf');assert sha(elf)==expected[name];r=subprocess.run([str(q),'-cpu','cortex-a53',str(elf),str(case)],env=env,capture_output=True,text=True,timeout=30);(b/(name+'.log')).write_text(r.stdout+r.stderr)
 assert r.returncode==99 and 'PASS' not in r.stdout,(name,r.returncode,r.stdout,r.stderr)
r={'status':'A53_GEM_HANDLER_TO_OBSERVER_RUST_MASTER_13_CASES_AND_TWO_NEGATIVES_PASS','normal_runs':runs,'negative_exit_codes':{'missing-hook':99,'false-ready':99},'preexecution_elf_sha256':expected,'hardware_accessed':False,'limits':['Linux-user ordinary handler calls inside fake bus/foreground, not actual IRQ execution','Recovery functions are RAM stubs; source-copy hook only, deployed BSP unchanged','No next fakeCRI/AUX callback after publication is tested; in-flight call already begun is not contained','No real GEM recovery, management availability, IRQ priority/nesting/FPU or worker/clock admission']}
(b/'execution-results.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
