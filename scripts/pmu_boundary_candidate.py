"""Diagnostic PMU image pins and bounded coherent telemetry; LGPL-3.0-or-later."""
import hashlib,json,re
from pathlib import Path
from check_pmu_boundary_image import check
SCRIPTS={'scripts/pmu_boundary_candidate.py','scripts/check_pmu_boundary_image.py','scripts/package_local_candidate.py','scripts/probe_pmu_boundary.tcl','scripts/test_candidate_runtime_hw.py','scripts/run_trained_observer.py','scripts/run_boot_firmware.tcl'}
def preflight(path,repo):
 m=json.loads(Path(path).read_text())
 if set(m)!={'elf','symbols','script_sha256'} or set(m['script_sha256'])!=SCRIPTS:raise ValueError('Exact PMU diagnostic gate required')
 for n,h in m['script_sha256'].items():
  if hashlib.sha256((repo/n).read_bytes()).hexdigest()!=h:raise ValueError('Changed PMU helper '+n)
 for n in ('elf','symbols'):
  item=m[n]
  if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed PMU '+n)
 result=check(Path(m['elf']['path']).read_bytes(),Path(m['symbols']['path']).read_text())
 if result['telemetry']['start']!='0xffdd7cf4':raise ValueError('Changed fixed telemetry address')
 return m

def parse(text):
 lines=text.splitlines()
 if lines.count('PMU_BOUNDARY_BEGIN')!=1 or lines.count('PMU_BOUNDARY_END')!=1:raise ValueError('Incomplete/duplicate PMU frame')
 start,end=lines.index('PMU_BOUNDARY_BEGIN'),lines.index('PMU_BOUNDARY_END');rows=[s for s in lines if s.startswith('PMU_BOUNDARY ')]
 if lines[start+1:end]!=rows or len(rows)!=40:raise ValueError('Wrong PMU frame extent')
 snapshots=[]
 for sample in range(4):
  values={}
  for field,line in zip(['before']+['word'+str(i) for i in range(8)]+['after'],rows[sample*10:(sample+1)*10]):
   m=re.fullmatch(r'PMU_BOUNDARY '+str(sample)+' '+field+r' 0x([0-9a-fA-F]{8})',line)
   if not m:raise ValueError('Malformed PMU record')
   values[field]=int(m[1],16)
  coherent=values['before']==values['word0']==values['after'] and not values['before']&1
  if coherent:
   if [values['word'+str(i)] for i in (1,2,4,5,6,7)]!=[0x504d5542,1,0,0x7f,0,0] or values['word3']==0:raise ValueError('Wrong coherent PMU identity/ACK/claims')
  snapshots.append(dict(coherent=coherent,values=values))
 if not any(s['coherent'] for s in snapshots):raise ValueError('No coherent PMU sample in fixed budget; do not blind retry')
 return dict(status='PMU_BOUNDARY_OBSERVATION_PASS_NOT_QUIESCENT',hardware_executed=True,snapshots=snapshots,coherent_samples=sum(s['coherent'] for s in snapshots),destructive_test_allowed=False,limits='External AXI observation of local RAM, ACK0/unresolved7f. Coherent samples are not interrupt/ROM/DDR exclusion proof.')
