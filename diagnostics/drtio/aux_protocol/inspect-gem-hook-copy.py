#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Verify disabled code identity and enabled release-store dominance in a copy."""
import argparse,hashlib,importlib.util,json,re,struct
from pathlib import Path

def load(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def function(text):
 marker='<emacps_error_handler>:';start=text.index(marker);end=text.find('\n\n',start);part=text[start:end];ins={};calls={}
 for line in part.splitlines():
  m=re.match(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(\S+)[ \t]*(.*)',line)
  if m:ins[int(m[1],16)]=(int(m[2],16),m[3],m[4].split('//')[0].strip())
  m=re.match(r'^\s*([0-9a-f]+):\s+R_AARCH64_(CALL26|JUMP26)\s+(\S+)',line)
  if m:calls[int(m[1],16)]=(m[2],m[3])
 return ins,calls,part

def dominates(ins,calls,publish):
 pending=[(min(ins),False)];visited=set();reached=set()
 while pending:
  at,seen=pending.pop()
  if (at,seen) in visited:continue
  visited.add((at,seen));assert at in ins,'Escaping function CFG'
  if at==publish:seen=True
  _,op,args=ins[at]
  if at in calls:
   assert seen,('Recovery before publication',hex(at),calls[at]);reached.add(at)
   if calls[at][0]=='JUMP26':continue
  elif op in ('br','blr'):raise AssertionError('Unreviewed indirect transfer')
  elif op=='ret':continue
  elif op=='b' or op.startswith('b.') or op in ('cbz','cbnz','tbz','tbnz'):
   target=int(re.search(r'(?:^|, )([0-9a-f]+) <',args)[1],16);pending.append((target,seen))
   if op=='b':continue
  pending.append((at+4,seen))
 assert reached==set(calls),'Unvisited recovery callsite'
 return len(visited)

def main():
 p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();b=a.artifacts
 elf=load('elf','inspect-retained-caller.py');rel=load('rel','inspect-irq-probes.py')
 binding=json.loads((b/'retained-binding.json').read_text());old=Path(binding['object']);source=Path(binding['source']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 assert sha(source)==binding['source_sha256'],'Deployed source changed'
 assert elf.sections(old)['.text']==elf.sections(b/'default-off.o')['.text']
 commands=json.loads((b/'commands.json').read_text());alias=next(x for x in commands['default-off'] if x.endswith('/xemacpsif_hw.c'))
 assert rel.relocs(old,str(source))==rel.relocs(b/'default-off.o',alias)
 off,offcalls,_=function((b/'default-off-disassembly.txt').read_text());ins,calls,part=function((b/'enabled-disassembly.txt').read_text())
 code=elf.sections(b/'enabled.o')['.text']
 for at,(word,_,_) in ins.items():assert struct.unpack_from('<I',code,at)[0]==word,'Disassembly/object mismatch'
 assert ins[0]==(0x35000042,'cbnz','w2, 8 <emacps_error_handler+0x8>') and ins[4][1]=='ret'
 assert ins[0x20][0]==0x90000002 and ins[0x24][0]==0x91000042
 assert re.search(r'20: R_AARCH64_ADR_PREL_PG_HI21\s+mnf_copy_only_gem_fault',part)
 assert re.search(r'24: R_AARCH64_ADD_ABS_LO12_NC\s+mnf_copy_only_gem_fault',part)
 assert ins[0x2c][0]==0x52800023 and ins[0x30][0]==0x889ffc43
 assert [at for at,(_,op,args) in ins.items() if op=='stlr']==[0x30]
 assert set(n for kind,n in calls.values())==set(n for kind,n in offcalls.values())
 assert any(name=='HandleEmacPsError' for kind,name in calls.values())
 states=dominates(ins,calls,0x30)
 undef=lambda p:set(x.split()[-1] for x in p.read_text().splitlines() if x.strip())
 assert undef(b/'enabled-undefined.txt')-undef(b/'default-off-undefined.txt')=={'mnf_copy_only_gem_fault'}
 assert not any('__atomic' in x for x in undef(b/'enabled-undefined.txt'))
 # Graph controls move publication past the first recovery call, or remove it.
 for publish in (0x104,0x100000):
  try:dominates(ins,calls,publish)
  except AssertionError:pass
  else:raise AssertionError('Bad publication dominance accepted')
 r={'status':'COPY_ONLY_GEM_HOOK_DEFAULT_OFF_IDENTITY_AND_ENABLED_RELEASE_DOMINANCE_PASS','default_off_instructions_and_relocation_meaning_identical':True,'enabled_nonzero_error_store_address':'0x30','error_zero_path':'Entry CBNZ w2 else RET; no latch store or recovery','all_recovery_calls_dominated_by_store':True,'recovery_calls':{hex(k):list(v) for k,v in calls.items()},'cfg_states_checked':states,'new_undefined_symbol':'mnf_copy_only_gem_fault; deliberately no storage definition or runnable image','graph_negative_controls':'Late or absent publication refused','hardware_accessed':False,'deployed_sources_changed':False,'retained_source_sha256':sha(source),'object_sha256':{'default_off':sha(b/'default-off.o'),'enabled':sha(b/'enabled.o')},'limits':['Copy-only objects, no physical IRQ execution or deployment','Hook reports fault only; original recovery and its IRQ unmask path remain unchanged','Does not qualify IRQ nesting, coherent memory/lifetime, late publication race, worker or clock/recovery gates']}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');(a.output.parent/'enabled-error-handler.txt').write_text(part+'\n');print(r['status'])
if __name__=='__main__':main()
