# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact relocatable assembly object scope; no vector/linked/live qualification."""
import struct
BASE_WORDS=[0x94608001,0x94808005,0x94a08003,0xb0000000,0x31000000,0xf8080000,0xb8220004,0xb0005046,0x31205831,0xf9280004,0x31200001,0xf9280008,0x31200001,0xf928000c,0x31200007,0xf9280010,0xf8680014,0xf8880018,0xf8a8001c,0xf8080020,0xf8080024,0xf8080028,0xf808002c,0xf8080030,0xf8080034,0xf8080038,0xf808003c,0xb8220004,0x31200001,0xf9280000,0xb8000000,0x80000000]
def check(data):
 if data[:7]!=b'\x7fELF\x01\x01\x01':raise ValueError('little-endian ELF32 required')
 h=struct.unpack_from('<HHIIIIIHHHHHH',data,16)
 if h[0:3]!=(1,189,1) or h[3]!=0 or h[4]!=0 or h[8]!=0 or h[9]!=0 or h[10]!=40:raise ValueError('relocatable MicroBlaze section object required')
 off,count,names=h[5],h[11],h[12]
 if not count or names>=count or off+40*count>len(data):raise ValueError('bad section table')
 sections=[struct.unpack_from('<10I',data,off+40*i) for i in range(count)]
 def payload(s):
  if s[4]+s[5]>len(data):raise ValueError('section out of file')
  return data[s[4]:s[4]+s[5]]
 def string(tab,i):
  if i>=len(tab):raise ValueError('bad string index')
  end=tab.find(b'\0',i)
  if end<0:raise ValueError('unterminated string')
  return tab[i:end].decode('ascii')
 strings=payload(sections[names]);named={}
 for s in sections[1:]:
  n=string(strings,s[0])
  if n in named:raise ValueError('duplicate section')
  named[n]=s
 if any('vector' in n for n in named):raise ValueError('vector section forbidden')
 required={'.text','.data','.bss','.bss.pit_fault_entry_slot','.text.pit_fault_sw_entry_audit','.text.pit_fault_hw_entry_audit','.rela.text.pit_fault_sw_entry_audit','.rela.text.pit_fault_hw_entry_audit','.symtab','.strtab','.shstrtab'}
 if set(named)!=required:raise ValueError('unexpected section closure')
 for n in ['.text','.data','.bss']:
  if named[n][5]:raise ValueError('unexpected default section contents')
 s=named['.bss.pit_fault_entry_slot']
 if (s[1],s[2],s[5],s[8])!=(8,3,64,8):raise ValueError('owned slot shape')
 sym=named['.symtab'];st=payload(sections[sym[6]])
 if sym[9]!=16 or sym[5]%16:raise ValueError('bad symbol table')
 symbols=[struct.unpack_from('<IIIBBH',payload(sym),i) for i in range(0,sym[5],16)]
 syms=[(string(st,s[0]),s) for s in symbols]
 slot=[s for n,s in syms if n=='pit_fault_entry_slot']
 if len(slot)!=1 or slot[0][1:4]!=(0,64,17) or sections[slot[0][5]]!=named['.bss.pit_fault_entry_slot']:raise ValueError('slot symbol')
 for route,tag in [(1,'sw'),(2,'hw')]:
  name='pit_fault_'+tag+'_entry_audit';section=named['.text.'+name];expected=BASE_WORDS[:];expected[12]=0x31200000+route
  if section[1]!=1 or section[2]!=6 or section[8]!=4 or payload(section)!=struct.pack('<32I',*expected):raise ValueError('changed exact entry instructions')
  entries=[s for n,s in syms if n==name]
  if len(entries)!=1 or entries[0][1:4]!=(0,128,18) or sections[entries[0][5]]!=section:raise ValueError('entry symbol')
  rela=named['.rela.text.'+name]
  if rela[1]!=4 or rela[9]!=12 or sections[rela[6]]!=sym or sections[rela[7]]!=section:raise ValueError('relocation metadata')
  raw=payload(rela)
  if len(raw)!=24:raise ValueError('relocation count')
  a,info,addend=struct.unpack_from('<IIi',raw)
  if a!=12 or info&255!=5 or addend or info>>8>=len(syms) or syms[info>>8][0]!='pit_fault_entry_slot':raise ValueError('slot relocation')
  if struct.unpack_from('<IIi',raw,12)!=(120,0,0):raise ValueError('loop relocation')
 return dict(status='EXACT_STANDALONE_STACKLESS_OBJECT_NOT_HANDLER_ADMISSION',hardware_executed=False,deployable=False,entry_functions=2,words_per_entry=32,slot_bytes=64,uses_stack=False,calls=False,vector_sections=False,edr_read=False,linked_slot_address_qualified=False,reentry_excluded=False,sleep_proven=False,recovery_proven=False)
