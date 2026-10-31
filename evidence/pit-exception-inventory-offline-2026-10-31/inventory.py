# SPDX-License-Identifier: LGPL-3.0-or-later
"""Read-only static ELF vector inventory; never executes/injects exceptions."""
import hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
BUILD=Path('/home/codex-hil/.local/state/artiq-builds/pit-digest-root-audit-20261031-v1')
sys.path.insert(0,str(ROOT/'scripts'))
from package_local_candidate import loads

def main():
 data=(BUILD/'audit-only.elf').read_bytes();symbols=(BUILD/'symbols.txt').read_text();dis=(BUILD/'disassembly.txt').read_text()
 machine,entry,segs=loads(data)
 if machine!=189:raise ValueError('MicroBlaze image required')
 def raw(a,z):
  spans=[s for s in segs if s['address']<=a and a+z<=s['address']+s['filesz']]
  if len(spans)!=1:raise ValueError('unique file-backed range required')
  s=spans[0];return s['payload'][a-s['address']:a-s['address']+z]
 allsyms={int(a,16):n for a,n in re.findall(r'^([0-9a-f]+)(?: [0-9a-f]+)? [tT] (\S+)$',symbols,re.M)}
 vectors=[]
 for name,a,target in [('_vector_reset',0xffdc0000,0xffdc0050),('_vector_sw_exception',0xffdc0008,0xffdc00bc),('_vector_interrupt',0xffdc0010,0xffdc58fc),('_vector_hw_exception',0xffdc0020,0xffdc891c)]:
  high,branch=struct.unpack('<2I',raw(a,8))
  if high>>16!=0xb000 or branch>>16!=0xb808:raise ValueError('unexpected vector encoding')
  dest=((high&0xffff)<<16)|(branch&0xffff)
  if dest!=target:raise ValueError('changed vector target')
  vectors.append(dict(name=name,address=a,target=dest,target_symbol=allsyms.get(dest),raw_hex=raw(a,8).hex()))
 handlers={}
 for name in ['XPfw_Exception','XPfw_InterruptHandler','XPfw_Exception_Handler','xil_printf','XPfw_UtilRMW']:
  m=re.search(r'^[0-9a-f]+ <'+name+r'>:\n.*?(?=\n[0-9a-f]+ <|\Z)',dis,re.M|re.S)
  if not m:raise ValueError('missing handler')
  text=m[0];(HERE/(name+'.dis')).write_text(text+'\n')
  rows=re.findall(r'^([0-9a-f]+):\s+([0-9a-f]{8})\s+([^\n]+)',text,re.M);body=b''.join(int(w,16).to_bytes(4,'little') for pc,w,asm in rows)
  for pc,w,asm in rows:
   if raw(int(pc,16),4)!=int(w,16).to_bytes(4,'little'):raise ValueError('stale listing')
  direct=[]
  for pc,w,asm in rows:
   if m:=re.match(r'brlid\s+r15, (-?\d+)',asm):
    dest=(int(pc,16)+int(m[1]))&0xffffffff;direct.append(dict(pc=int(pc,16),target=dest,symbol=allsyms.get(dest)))
  handlers[name]=dict(subword_store_sites=[dict(pc=int(pc,16),instruction=asm) for pc,w,asm in rows if re.match(r'(sb|sbi|sh|shi|sbr|shr)\s+',asm)],address=int(rows[0][0],16),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),frame_allocations=[-int(m[1]) for pc,w,asm in rows if (m:=re.match(r'addik\s+r1, r1, (-\d+)',asm))],direct_calls=direct,indirect_call_sites=[int(pc,16) for pc,w,asm in rows if re.match(r'brald\s+',asm)],self_loop_sites=[int(pc,16) for pc,w,asm in rows if re.match(r'bri\s+0\b',asm)])
 m=re.search(r'^([0-9a-f]+) ([0-9a-f]+) r g_TopLevelInterruptTable$',symbols,re.M)
 if not m:raise ValueError('missing IRQ table')
 a,z=[int(v,16) for v in m.groups()];table=raw(a,z)
 if z!=22*8:raise ValueError('unexpected IRQ table size')
 irqtable=[dict(index=i,mask=mask,target=target,symbol=allsyms.get(target)) for i,(mask,target) in enumerate(struct.iter_unpack('<2I',table))]
 report=dict(status='STATIC_VECTOR_DEPENDENCY_INVENTORY_NOT_EXCEPTION_BOUND',hardware_executed=False,deployable=False,elf_sha256=hashlib.sha256(data).hexdigest(),vectors=vectors,handlers=handlers,irq_table=dict(address=a,bytes=z,sha256=hashlib.sha256(table).hexdigest(),entries=irqtable),nmi_debug_paths_excluded=False,total_stack_qualified=False,recovery_qualified=False,limits='Static image only. No vector-selection/live MSR/platform routing observation, no nested exception bound or asynchronous exclusion. ROM/debug/NMI absence cannot be inferred from missing ELF symbols.')
 (HERE/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'vectors':len(vectors),'irq_entries':len(irqtable),'handlers':{n:r['frame_allocations'] for n,r in handlers.items()}}))
if __name__=='__main__':main()
