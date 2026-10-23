"""Exact observational request-image gate, never a PMU park permit. LGPL-3.0-or-later."""
import hashlib,json,re
from pathlib import Path
from check_pmu_boundary_image import check
SCRIPTS={'scripts/pmu_request_candidate.py','scripts/check_pmu_boundary_image.py','scripts/package_local_candidate.py','scripts/probe_pmu_observe_request.tcl','scripts/test_candidate_runtime_hw.py','scripts/run_trained_observer.py','scripts/run_boot_firmware.tcl'}
def preflight(path,repo):
 m=json.loads(Path(path).read_text())
 if set(m)!={'elf','symbols','script_sha256'} or set(m['script_sha256'])!=SCRIPTS:raise ValueError('Exact request gate required')
 for n,h in m['script_sha256'].items():
  if hashlib.sha256((repo/n).read_bytes()).hexdigest()!=h:raise ValueError('Changed request helper '+n)
 for n in ('elf','symbols'):
  item=m[n]
  if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed request '+n)
 text=Path(m['symbols']['path']).read_text();check(Path(m['elf']['path']).read_bytes(),text)
 for name,addr in [('artiq_pmu_request',0xffdd7e20),('artiq_pmu_echo',0xffdd7df4),('artiq_pmu_boundary',0xffdd7e40)]:
  matches=re.findall(r'^([0-9a-f]+) 00000020 b '+name+'$',text,re.M)
  if matches!=[f'{addr:08x}']:raise ValueError('Changed fixed request/echo layout')
 return m

def parse(text,nonce):
 lines=text.splitlines()
 if lines.count('PMU_ECHO_BEGIN')!=1 or lines.count('PMU_ECHO_END')!=1:raise ValueError('Incomplete/duplicate echo frame')
 start,end=lines.index('PMU_ECHO_BEGIN'),lines.index('PMU_ECHO_END');rows=[s for s in lines if s.startswith('PMU_ECHO ')]
 if lines[start+1:end]!=rows or len(rows)!=40:raise ValueError('Wrong echo extent')
 results=[]
 for sample in range(4):
  values=[]
  for name,line in zip(['before']+['word'+str(i) for i in range(8)]+['after'],rows[sample*10:(sample+1)*10]):
   match=re.fullmatch(r'PMU_ECHO '+str(sample)+' '+name+r' 0x([0-9a-fA-F]{8})',line)
   if not match:raise ValueError('Malformed echo row')
   values.append(int(match[1],16))
  coherent=values[0]==values[1]==values[-1]==2
  if coherent and values[1:9]!=[2,nonce&0xffffffff,nonce>>32,1,0,1,0,0]:raise ValueError('Wrong nonce/sequence/status/ACK in echo')
  results.append({'coherent':coherent,'values':values})
 if not any(r['coherent'] for r in results):raise ValueError('No exact echo in bounded budget; no blind retry')
 return dict(status='PMU_OBSERVE_REQUEST_ECHO_PASS_NOT_QUIESCENT',hardware_executed=True,nonce=hex(nonce),sequence=1,samples=results,destructive_test_allowed=False,limits='Cooperating session echo only, not authentication/boot identity/IRQ-ROM exclusion or DDR ownership.')
