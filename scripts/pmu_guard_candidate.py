"""Exact opt-in laboratory guard image/record gate; LGPL-3.0-or-later."""
import hashlib,json,re,subprocess
from pathlib import Path
from check_pmu_lab_guard import check
TOOL=Path('/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/gnu/microblaze/lin/bin')
SCRIPTS={'scripts/pmu_guard_candidate.py','scripts/check_pmu_lab_guard.py','scripts/check_pmu_boundary_image.py','scripts/package_local_candidate.py','scripts/probe_pmu_lab_guard.tcl','scripts/restart_pmu_for_restore.tcl','scripts/test_candidate_runtime_hw.py','scripts/run_trained_observer.py','scripts/run_boot_firmware.tcl'}
def preflight(path,repo):
 m=json.loads(Path(path).read_text())
 if set(m)!={'elf','symbols','disassembly','script_sha256'} or set(m['script_sha256'])!=SCRIPTS:raise ValueError('Exact guard gate required')
 for n,h in m['script_sha256'].items():
  if hashlib.sha256((repo/n).read_bytes()).hexdigest()!=h:raise ValueError('Changed guard helper '+n)
 for n in ('elf','symbols','disassembly'):
  item=m[n]
  if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed guard '+n)
 elf=Path(m['elf']['path']);symbols=Path(m['symbols']['path']).read_text();dis=Path(m['disassembly']['path']).read_text()
 if subprocess.check_output([str(TOOL/'mb-nm'),'-n','-S',str(elf)],text=True,timeout=15)!=symbols:raise ValueError('Symbol file differs from ELF')
 if subprocess.check_output([str(TOOL/'mb-objdump'),'-d',str(elf)],text=True,timeout=15)!=dis:raise ValueError('Disassembly differs from ELF')
 result=check(elf.read_bytes(),symbols,dis)
 if result['terminal_pc']!='0xffdc4734':raise ValueError('Changed guard terminal')
 for name,addr,size in [('artiq_pmu_request',0xffdd7f20,32),('artiq_pmu_guard',0xffdd7f68,64)]:
  matches=re.findall(r'^([0-9a-f]+) '+f'{size:08x}'+r' b '+name+'$',symbols,re.M)
  if matches!=[f'{addr:08x}']:raise ValueError('Changed fixed guard records')
 return m

def parse(text,nonce):
 lines=text.splitlines()
 if lines.count('PMU_GUARD_BEGIN')!=1 or lines.count('PMU_GUARD_END')!=1:raise ValueError('Incomplete/duplicate guard frame')
 start,end=lines.index('PMU_GUARD_BEGIN'),lines.index('PMU_GUARD_END');rows=[s for s in lines if s.startswith('PMU_GUARD ')]
 if lines[start+1:end]!=rows or len(rows)!=72:raise ValueError('Wrong guard extent')
 results=[]
 for sample in range(4):
  values=[]
  for name,line in zip(['before']+['word'+str(i) for i in range(16)]+['after'],rows[sample*18:(sample+1)*18]):
   match=re.fullmatch(r'PMU_GUARD '+str(sample)+' '+name+r' 0x([0-9a-fA-F]{8})',line)
   if not match:raise ValueError('Malformed guard row')
   values.append(int(match[1],16))
  coherent=values[0]==values[1]==values[-1]==2
  w=values[1:17]
  if coherent:
   if w[:6]!=[2,2,nonce&0xffffffff,nonce>>32,1,0] or w[8:]!=[0,0x7f,2,0,0,0,0,0]:raise ValueError('Wrong guard session/state/ACK')
   if not w[6]&2 or w[7]!=(w[6]&~2):raise ValueError('Guard did not positively clear IE preserving other MSR bits')
  results.append(dict(coherent=coherent,values=values))
 if not any(r['coherent'] for r in results):raise ValueError('No guarded record in fixed budget; restore without retry')
 return dict(status='LAB_GUARD_RECORD_PASS_RESTORATION_REQUIRED',hardware_executed=True,nonce=hex(nonce),samples=results,destructive_test_allowed=False,limits='IE-cleared sampled guard record, not continued PC proof/ROM-NMI-error exclusion or exclusive DDR ownership. ACK0 remains.')
