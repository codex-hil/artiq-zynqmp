# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact inlined fault-writer scope only; not a whole-image execution gate."""
import hashlib,re
from package_local_candidate import loads
from check_pmu_boundary_image import check as check_layout
from check_pit_mailbox_layout import check as check_mailbox
from check_pit_word_stores import check as check_stores
PROFILE='pit-minimal-fault-slot-scoped-v1'
START,SIZE,DIGEST=0xffdd078c,440,'8d547850c4c02bf6c2bc74163c21ba8f8e1aac363cd0651ef2db03cbbca516ec'
STORAGE={'fault_slot_consumed':(0xffddd378,4,'b'),'pit_fault_slot_audit':(0xffddd400,64,'B'),
 'pit_mailbox_audit':(0xffddd440,144,'B'),'sample_slot':(0xffddd3b4,32,'b'),'terminal_slot':(0xffddd394,32,'b')}
BOUNDARIES={'__bss_start':0xffdd95c0,'__bss_end':0xffddd4d0,'_stack_end':0xffddddec,'_stack':0xffddedf0}
def check(data,symbols,disassembly):
 machine,entry,segs=loads(data)
 if machine!=189 or entry!=0xffdc0050:raise ValueError('expected full MicroBlaze ELF')
 if re.findall(r'^([0-9a-f]+) ([0-9a-f]+) [tT] pit_fault_store_audit$',symbols,re.M)!=[(f'{START:08x}',f'{SIZE:08x}')]:raise ValueError('changed writer range')
 for n,(a,z,k) in STORAGE.items():
  if re.findall(r'^([0-9a-f]+) ([0-9a-f]+) ([bB]) '+re.escape(n)+'$',symbols,re.M)!=[(f'{a:08x}',f'{z:08x}',k)]:raise ValueError('changed owned storage: '+n)
  spans=[s for s in segs if s['address']+s['filesz']<=a and a+z<=s['address']+s['memsz'] and s['flags']&2]
  if len(spans)!=1:raise ValueError('storage not unique zero-init writable tail')
 for n,a in BOUNDARIES.items():
  if re.findall(r'^([0-9a-f]+) [A-Za-z?] '+re.escape(n)+'$',symbols,re.M)!=[f'{a:08x}']:raise ValueError('changed boundary: '+n)
 intervals=sorted((a,a+z,n) for n,(a,z,k) in STORAGE.items())
 if any(a2<b for (a,b,n),(a2,b2,n2) in zip(intervals,intervals[1:])):raise ValueError('owned storage overlap')
 if not all(BOUNDARIES['__bss_start']<=a<b<=BOUNDARIES['__bss_end'] for a,b,n in intervals):raise ValueError('storage outside BSS')
 rows={}
 for pc,word in re.findall(r'^([0-9a-f]+):\s+([0-9a-f]{8})\s+[^\n]+',disassembly,re.M):
  a=int(pc,16)
  if a in rows:raise ValueError('duplicate instruction listing')
  rows[a]=int(word,16)
 body=bytearray()
 for pc in range(START,START+SIZE,4):
  spans=[s for s in segs if s['address']<=pc and pc+4<=s['address']+s['filesz']]
  if len(spans)!=1:raise ValueError('writer not uniquely file backed')
  s=spans[0];raw=s['payload'][pc-s['address']:pc-s['address']+4]
  if rows.get(pc)!=int.from_bytes(raw,'little'):raise ValueError('stale writer listing')
  body.extend(raw)
 if hashlib.sha256(body).hexdigest()!=DIGEST:raise ValueError('changed exact writer instructions')
 return dict(status='EXACT_FAULT_WRITER_SCOPE_PASS_NOT_DEPLOYMENT',profile=PROFILE,
  hardware_executed=False,deployable=False,layout=check_layout(data,symbols),mailbox=check_mailbox(data,symbols),
  stores=check_stores(data,symbols,'pit_fault_store_audit'),instruction_words=SIZE//4,
  stack_bytes=4100,stack_to_service_table_gap=2288,
  limits='Exact one-function/layout scope, including inlined formatter and two mbar instructions. Not whole-image/root/callback/exception-entry provenance, stack, visibility or recovery qualification.')
