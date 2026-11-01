# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact synthetic non-PMU link fixture, explicitly not hardware firmware."""
import re,struct
from package_local_candidate import loads
from check_pit_fault_entry_object import BASE_WORDS

def check(data,symbols,disassembly):
 machine,entry,segs=loads(data)
 if machine!=189 or entry!=0x10000 or len(segs)!=2:raise ValueError('synthetic non-PMU fixture required')
 code=[s for s in segs if (s['address'],s['vaddr'],s['filesz'],s['memsz'],s['flags'])==(0x10000,0x10000,256,256,5)]
 slot=[s for s in segs if (s['address'],s['vaddr'],s['filesz'],s['memsz'],s['flags'])==(0x20000,0x20000,0,64,6)]
 if len(code)!=1 or len(slot)!=1:raise ValueError('exact disjoint code/zero-BSS slot mapping required')
 for n,a,z,k in [('pit_fault_sw_entry_audit',0x10000,128,'T'),('pit_fault_hw_entry_audit',0x10080,128,'T'),('pit_fault_entry_slot',0x20000,64,'B')]:
  if re.findall(r'^([0-9a-f]+) ([0-9a-f]+) '+k+' '+n+'$',symbols,re.M)!=[(f'{a:08x}',f'{z:08x}')]:raise ValueError('changed exact symbol: '+n)
 rows={}
 for pc,w in re.findall(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+[^\n]+',disassembly,re.M):
  pc=int(pc,16)
  if pc in rows:raise ValueError('duplicate listing word')
  rows[pc]=int(w,16)
 for index,route in enumerate((1,2)):
  expected=BASE_WORDS[:];expected[3]=0xb0000002;expected[12]=0x31200000+route
  raw=code[0]['payload'][128*index:128*(index+1)]
  if raw!=struct.pack('<32I',*expected):raise ValueError('changed linked instructions/slot relocation')
  if any(rows.get(0x10000+128*index+4*i)!=w for i,w in enumerate(expected)):raise ValueError('stale linked listing')
 h=struct.unpack_from('<HHIIIIIHHHHHH',data,16);off,count,names=h[5],h[11],h[12]
 if h[10]!=40 or names>=count or off+40*count>len(data):raise ValueError('invalid section metadata')
 sections=[struct.unpack_from('<10I',data,off+40*i) for i in range(count)]
 sh=sections[names];strings=data[sh[4]:sh[4]+sh[5]];named={}
 for s in sections[1:]:
  end=strings.find(b'\0',s[0])
  if end<0:raise ValueError('bad section name')
  n=strings[s[0]:end].decode('ascii')
  if n in named:raise ValueError('duplicate section')
  named[n]=s
 if set(named)!={'.text','.bss','.symtab','.strtab','.shstrtab'} or any(s[1] in (4,9) for s in sections):raise ValueError('unexpected section/relocation/vector closure')
 s=named['.bss']
 if (s[1],s[2],s[3],s[5],s[8])!=(8,3,0x20000,64,8):raise ValueError('slot section bounds/alignment')
 return dict(status='EXACT_SYNTHETIC_NON_PMU_LINK_PASS_NOT_FIRMWARE',hardware_executed=False,deployable=False,
  synthetic_addresses=True,entry_count=2,instruction_words=64,slot_address=0x20000,slot_bytes=64,
  resolved_slot_relocations=True,uses_stack=False,calls=False,vector_sections=False,
  pmu_runtime_layout_qualified=False,reentry_excluded=False,sleep_proven=False,recovery_proven=False)
