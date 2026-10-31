# SPDX-License-Identifier: LGPL-3.0-or-later
"""Conditional normal-path stack model for exact digest ELF; never HW admission."""
import re,hashlib
from package_local_candidate import loads
from check_pit_digest_root_flow import check as exact_check
ROOT='pit_digest_root_audit'
FENCE_PIN=(4292659064, 24, '24072df1489e3f1e888357098c23516e3112815901ea0796cee2303e250dcd30')
FRAMES={'pit_digest_root_audit':336,'pit_capture_digest':156,'pit_collect.constprop.0':92,
 'pit_sample_sha256':300,'swap':0,'pit_publish':104,'pit_terminal_publish':152,
 'pit_terminal_build':24,'pit_mailbox_prepare_audit':0,'pit_terminal_audit':0,
 'observe.lto_priv.1':44,'disable.lto_priv.1':28,'read_word.lto_priv.1':32,
 'write_word.lto_priv.1':32,'barrier.lto_priv.1':32,'digest_ordered_read':28,
 'pit_ro_read':44,'pit_mmio_read':0,'pit_irq_msr_audit':0,'pit_irq_disable_audit':8,
 'microblaze_disable_interrupts':0,'pit_mailbox_sample_write_audit':28,
 'pit_mailbox_sample_barrier_audit':28,'pit_mailbox_terminal_write_audit':28,
 'pit_mailbox_terminal_barrier_audit':28,'pit_word_slot_write':0,
 'pit_word_slot_barrier':32,'fence':0}
# Reviewed concrete root/forwarding bindings, not arbitrary callback resolution.
INDIRECT={('pit_collect.constprop.0','r26'):'read_word.lto_priv.1',
 ('pit_publish','r22'):'write_word.lto_priv.1',('pit_publish','r24'):'barrier.lto_priv.1',
 ('pit_terminal_publish','r22'):'pit_mailbox_terminal_write_audit',
 ('pit_terminal_publish','r24'):'pit_mailbox_terminal_barrier_audit',
 ('observe.lto_priv.1','r3'):'pit_irq_msr_audit',('disable.lto_priv.1','r3'):'pit_irq_disable_audit',
 ('read_word.lto_priv.1','r3'):'digest_ordered_read',('write_word.lto_priv.1','r3'):'pit_mailbox_sample_write_audit',
 ('barrier.lto_priv.1','r3'):'pit_mailbox_sample_barrier_audit',
 ('pit_ro_read','r3'):'pit_mmio_read',('pit_word_slot_barrier','r3'):'fence'}
def max_path(frames,graph,root):
 active=set()
 def walk(n):
  if n in active:raise ValueError('recursive call graph')
  if n not in frames or n not in graph:raise ValueError('unbounded/missing function')
  if type(frames[n]) is not int or frames[n]<0:raise ValueError('invalid frame')
  active.add(n);children=[walk(c) for c in graph[n]];active.remove(n)
  size,path=max(children,key=lambda x:x[0]) if children else (0,[])
  return frames[n]+size,[n]+path
 return walk(root)
def audit(data,symbols,disassembly):
 exact_check(data,symbols,disassembly)
 a,z,h=FENCE_PIN
 if re.findall(r'^([0-9a-f]+) ([0-9a-f]+) [tT] fence$',symbols,re.M)!=[(f'{a:08x}',f'{z:08x}')]:raise ValueError('changed fence range')
 spans=[s for s in loads(data)[2] if s['address']<=a and a+z<=s['address']+s['filesz']]
 if len(spans)!=1:raise ValueError('fence mapping')
 seg=spans[0];body=seg['payload'][a-seg['address']:a-seg['address']+z]
 if hashlib.sha256(body).hexdigest()!=h:raise ValueError('changed fence instructions')
 for offset in range(0,z,4):
  rows=re.findall(r'^'+format(a+offset,'08x')+r':\s+([0-9a-f]{8})\s+[^\n]+',disassembly,re.M)
  if rows!=[f"{int.from_bytes(body[offset:offset+4],'little'):08x}"]:raise ValueError('stale fence listing')
 ranges={n:(int(a,16),int(z,16)) for a,z,n in re.findall(r'^([0-9a-f]+) ([0-9a-f]+) [tT] (\S+)$',symbols,re.M)}
 byaddr={a:n for n,(a,z) in ranges.items()};graph={};sites=[];pending=[ROOT]
 while pending:
  name=pending.pop()
  if name in graph:continue
  if name not in FRAMES or name not in ranges:raise ValueError('unreviewed frame/function: '+name)
  a,z=ranges[name]
  rows=[(int(pc,16),asm) for pc,asm in re.findall(r'^([0-9a-f]+):\s+[0-9a-f]{8}\s+([^\n]+)',disassembly,re.M) if a<=int(pc,16)<a+z]
  allocations=[-int(m[1]) for pc,asm in rows if (m:=re.match(r'addik\s+r1, r1, (-\d+)\b',asm))]
  if allocations!=([FRAMES[name]] if FRAMES[name] else []):raise ValueError('unexpected stack allocation: '+name)
  edges=set()
  for pc,asm in rows:
   if m:=re.match(r'brlid\s+r15, (-?\d+)',asm):
    target=(pc+int(m[1]))&0xffffffff
    if target not in byaddr:raise ValueError('unresolved direct call')
    callee=byaddr[target];kind='direct'
   elif m:=re.match(r'brald\s+r15, (r\d+)',asm):
    if (name,m[1]) not in INDIRECT:raise ValueError('unresolved indirect call')
    callee=INDIRECT[name,m[1]];kind='reviewed-binding-assumption'
   else:continue
   edges.add(callee);sites.append(dict(caller=name,pc=pc,callee=callee,kind=kind))
  graph[name]=sorted(edges);pending+=list(edges)
 peak,path=max_path(FRAMES,graph,ROOT)
 return dict(status='CONDITIONAL_NORMAL_PATH_MODEL_NOT_TOTAL_STACK_PROOF',hardware_executed=False,
  deployable=False,normal_peak_bytes=peak,peak_path=path,frames={n:FRAMES[n] for n in graph},
  graph=graph,call_sites=sites,indirect_binding_assumptions=True,
  limits='Exact artifact plus manually reviewed callback binding assumptions; excludes entry caller, exceptions/interrupt/NMI/debug/error frames, recursion through hostile callbacks and hung MMIO. No generic instruction semantics/CFG or stack ownership/recovery proof.')
