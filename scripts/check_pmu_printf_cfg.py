#!/usr/bin/env python3
"""Delay-slot-aware structural printf dominance audit. LGPL-3.0-or-later."""
import argparse,json,re,hashlib,struct
from pathlib import Path
from check_pmu_printf_table import check as table_check, mapped

def verify_text(text,elf):
 for line in text.splitlines():
  m=re.fullmatch(r'([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)',line)
  if m and 0xffdcc810<=int(m[1],16)<0xffdccbc0:
   if struct.unpack('<I',mapped(elf,int(m[1],16),4))[0]!=int(m[2],16):raise ValueError('Disassembly differs from ELF')

def audit(text,table):
 rows={}
 for line in text.splitlines():
  m=re.fullmatch(r'([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)',line)
  if m and 0xffdcc810<=int(m[1],16)<0xffdccbc0:rows[int(m[1],16)]=m[3]
 if set(rows)!=set(range(0xffdcc810,0xffdccbc0,4)):raise ValueError('Incomplete printf')
 edges={};pending=[(0xffdcc810,None)]
 while pending:
  node=pending.pop()
  if node in edges:continue
  pc,continuation=node
  if pc not in rows:raise ValueError('Control outside printf')
  ins=rows[pc];op=ins.split()[0]
  if continuation is not None:
   if op.startswith(('br','rt','beq','bne','blt','bgt','ble','bge')):raise ValueError('Control instruction in delay slot')
   successors=[] if continuation==-1 else [(continuation,None)]
  elif op=='bra':
   if pc!=0xffdcc9ec:raise ValueError('Unknown indirect branch')
   successors=[(int(t,16),None) for t in table['unique_targets']]
  elif op=='brlid':successors=[(pc+4,pc+8)] # Callee assumed to return, ABI effects NOT proved.
  elif op=='rtsd':successors=[(pc+4,-1)]
  elif op in ('bri','brid') or op.startswith(('beq','bne','blt','bgt','ble','bge')):
   target=re.search(r'// ([0-9a-f]+)\s*$',ins)
   if not target:raise ValueError('Missing direct target')
   t=int(target[1],16);conditional=op not in ('bri','brid');delayed=op.endswith('d')
   choices=[t]+([pc+8 if delayed else pc+4] if conditional else [])
   successors=[(pc+4,d) if delayed else (d,None) for d in choices]
  elif op.startswith(('br','rt')):raise ValueError('Unsupported control '+ins)
  else:successors=[(pc+4,None)]
  edges[node]=successors;pending.extend(successors)
 target=(0xffdcc9ec,None)
 if target not in edges:raise ValueError('Indirect jump unreachable')
 def reachable_without(blocked):
  seen=set();todo=[(0xffdcc810,None)]
  while todo:
   n=todo.pop()
   if n in seen or n[0]==blocked:continue
   seen.add(n);todo.extend(edges[n])
  return target in seen
 required=[0xffdcc99c,0xffdcc9d0,0xffdcc9d4,0xffdcc9d8,0xffdcc9dc,0xffdcc9e0,0xffdcc9e4,0xffdcc9e8]
 dominance={hex(pc):not reachable_without(pc) for pc in required}
 if not all(dominance.values()):raise ValueError('Index-check structural bypass '+str(dominance))
 return {'status':'STRUCTURAL_DOMINANCE_PASS_CONDITIONAL_ON_CALL_RETURNS','hardware_executed':False,'destructive_test_allowed':False,'reachable_context_nodes':len(edges),'dominates_indirect_jump':dominance,'limits':'Calls modeled as returning to their own continuation with ABI preserved; no callee corruption/nonlocal return proof. Branch outcomes overapproximated. Unsigned CMPU semantics and register value ranges require separate evidence. ROM/reset/NMI and memory exclusion not established.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('elf','disassembly','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();raw=a.disassembly.read_bytes();elf=a.elf.read_bytes();verify_text(raw.decode(),elf);r=audit(raw.decode(),table_check(elf));r['disassembly_sha256']=hashlib.sha256(raw).hexdigest()
 with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
