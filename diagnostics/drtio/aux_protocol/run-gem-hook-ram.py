#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Run source-copy GEM handler under A53 Linux-user; recovery is RAM stubs."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args();b=a.artifacts
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(b/'execution-results.json').write_text('{"status":"INCOMPLETE","hardware_accessed":false}\n')
variants=('enabled','default-off','no-hook-negative');expected={name:sha(b/(name+'.elf')) for name in variants}
(b/'preexecution-hashes.json').write_text(json.dumps(expected,indent=2)+'\n')
allowed={'check','record','HandleEmacPsError','HandleTxErrors','emacps_recv_handler','setup_rx_bds','xemacps_process_sent_bds','pass','gem_hook_test_main','emacps_error_handler'}
for name in variants:
 assert not (b/(name+'-undefined.txt')).read_text().strip()
 table=subprocess.check_output(['readelf','-sW',str(b/(name+'.elf'))],text=True)
 functions=[]
 for line in table.splitlines():
  f=line.split()
  if len(f)>=8 and f[3]=='FUNC':
   symbol=f[-1];assert symbol.split('.')[0] in allowed,('Unreviewed linked function',symbol);functions.append(symbol)
 assert {'emacps_error_handler','gem_hook_test_main','HandleEmacPsError','HandleTxErrors','emacps_recv_handler','setup_rx_bds','xemacps_process_sent_bds'}<=set(n.split('.')[0] for n in functions)
 text=(b/(name+'-disassembly.txt')).read_text();assert not re.search(r'\b(?:blr|br)\s',text),'Unexpected indirect transfer'
 assert not re.search(r'\b(?:msr|mrs|smc|hvc)\s',text),'Unexpected privileged instruction'
q=Path('/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/bin/qemu-aarch64');env=dict(os.environ,LD_LIBRARY_PATH='/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/lib/x86_64-linux-gnu')
runs=[]
for mode in ('enabled','default-off'):
 for case in range(13):
  elf=b/(mode+'.elf');assert sha(elf)==expected[mode]
  r=subprocess.run([str(q),'-cpu','cortex-a53',str(elf),str(case)],env=env,capture_output=True,text=True,timeout=10)
  (b/(mode+'-'+str(case)+'.log')).write_text(r.stdout+r.stderr)
  assert r.returncode==0 and r.stdout=='A53_GEM_HOOK_RAM_PASS\n' and not r.stderr,(mode,case,r.returncode,r.stdout,r.stderr)
  runs.append({'mode':mode,'case':case,'exit_code':0})
elf=b/'no-hook-negative.elf';assert sha(elf)==expected['no-hook-negative']
r=subprocess.run([str(q),'-cpu','cortex-a53',str(elf),'1'],env=env,capture_output=True,text=True,timeout=10)
(b/'negative.log').write_text(r.stdout+r.stderr);assert r.returncode==99 and 'PASS' not in r.stdout
report={'status':'A53_GEM_COPY_HANDLER_26_RAM_CASES_AND_MISSING_HOOK_NEGATIVE_PASS','runs':runs,'negative_exit_code':99,'preexecution_elf_sha256':expected,'linked_function_allowlist':sorted(allowed),'hardware_accessed':False,'limits':['Linux-user CortexA53, not IRQ entry/priority/nesting or hardware execution','Real recovery functions replaced by RAM-only sentinels; no GEM access/recovery/management availability proof','Fresh process/BSS per independent case; latch never cleared/rearmed in a running process','Enabled source copy only; deployed BSP and board state untouched']}
(b/'execution-results.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
