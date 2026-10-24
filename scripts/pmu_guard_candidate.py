"""Exact opt-in laboratory guard image/record gate; LGPL-3.0-or-later."""
import hashlib,json,re,subprocess
from pathlib import Path
from check_pmu_lab_guard import check
TOOL=Path('/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/gnu/microblaze/lin/bin')
SCRIPTS={'scripts/pmu_guard_candidate.py','scripts/check_pmu_lab_guard.py','scripts/check_pmu_boundary_image.py','scripts/package_local_candidate.py','scripts/probe_pmu_lab_guard.tcl','scripts/restart_pmu_for_restore.tcl','scripts/test_candidate_runtime_hw.py','scripts/run_trained_observer.py','scripts/run_boot_firmware.tcl','scripts/check_hw_storage.py','scripts/load_rtio_runtime.py','scripts/test_rtio_debug_hw.py','scripts/test_ethernet_hw.py'}
def check_vector_read(dis):
 match=re.search(r'<artiq_pmu_enter_lab_guard>:\n(.*?)(?=\n[0-9a-f]+ <)',dis,re.S)
 if not match:raise ValueError('Missing guard block')
 block=match[1]
 rows=re.findall(r'^([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)$',block,re.M)
 loads=[(pc,word) for pc,word,ins in rows if ins.startswith(('lw','lh','lb','ll'))]
 if loads!=[('ffdc4738','e8800010')]:raise ValueError('Unexpected guard memory read')
 words={pc:word for pc,word,ins in rows}
 for pc,word in {'ffdc4734':'b000ffd4','ffdc4738':'e8800010','ffdc473c':'f8830030','ffdc472c':'30800001','ffdc4730':'f883002c'}.items():
  if words.get(pc)!=word:raise ValueError('Changed vector snapshot sequence')
 return dict(address='0xffd40010',version=1)

def preflight(path,repo):
 m=json.loads(Path(path).read_text())
 if set(m) not in ({'elf','symbols','disassembly','script_sha256'},{'elf','symbols','disassembly','script_sha256','profile'}) or set(m['script_sha256'])!=SCRIPTS:raise ValueError('Exact guard gate required')
 for n,h in m['script_sha256'].items():
  if hashlib.sha256((repo/n).read_bytes()).hexdigest()!=h:raise ValueError('Changed guard helper '+n)
 for n in ('elf','symbols','disassembly'):
  item=m[n]
  if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Changed guard '+n)
 elf=Path(m['elf']['path']);symbols=Path(m['symbols']['path']).read_text();dis=Path(m['disassembly']['path']).read_text()
 if subprocess.check_output([str(TOOL/'mb-nm'),'-n','-S',str(elf)],text=True,timeout=15)!=symbols:raise ValueError('Symbol file differs from ELF')
 if subprocess.check_output([str(TOOL/'mb-objdump'),'-d',str(elf)],text=True,timeout=15)!=dis:raise ValueError('Disassembly differs from ELF')
 profile=m.get('profile','sleep')
 if profile not in ('sleep','vector-v1'):raise ValueError('Unknown guard profile')
 result=check(elf.read_bytes(),symbols,dis)
 if profile=='vector-v1':check_vector_read(dis)
 if result['terminal_pc']!=('0xffdc474c' if profile=='vector-v1' else '0xffdc4738') or result.get('terminal_mode')!='sleep-reentry':raise ValueError('Expected exact sleep guard terminal')
 shift=32 if profile=='vector-v1' else 0
 for name,addr,size in [('artiq_pmu_request',0xffdd7f20+shift,32),('artiq_pmu_guard',0xffdd7f68+shift,64)]:
  matches=re.findall(r'^([0-9a-f]+) '+f'{size:08x}'+r' b '+name+'$',symbols,re.M)
  if matches!=[f'{addr:08x}']:raise ValueError('Changed fixed guard records')
 return m

def parse(text,nonce,profile="sleep"):
 if profile not in ("sleep","vector-v1"):raise ValueError("Unknown guard profile")
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
   if w[:6]!=[2,2,nonce&0xffffffff,nonce>>32,1,0] or (w[8:11]!=[0,0x7f,2] or (w[11:]!=[0,0,0,0,0] if profile=='sleep' else w[11]!=1 or w[13:]!=[0,0,0])):raise ValueError('Wrong guard session/state/ACK')
   if not w[6]&2 or w[7]!=(w[6]&~2):raise ValueError('Guard did not positively clear IE preserving other MSR bits')
  results.append(dict(coherent=coherent,values=values))
  if coherent and profile=='vector-v1':results[-1]['vector_snapshot']={'version':1,'gpo0':hex(w[12]),'ram_vector_remap':bool(w[12]&1),'scope':'Sampled mapping only; no ROM/event exclusion proof'}
 if profile=='vector-v1' and len({r['vector_snapshot']['gpo0'] for r in results if r['coherent']})>1:raise ValueError('Changed GPO0 inside immutable record')
 if not any(r['coherent'] for r in results):raise ValueError('No guarded record in fixed budget; restore without retry')
 return dict(status='LAB_GUARD_RECORD_PASS_RESTORATION_REQUIRED',hardware_executed=True,nonce=hex(nonce),samples=results,destructive_test_allowed=False,limits='IE-cleared sampled guard record, not continued PC proof/ROM-NMI-error exclusion or exclusive DDR ownership. ACK0 remains.')
