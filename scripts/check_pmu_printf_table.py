#!/usr/bin/env python3
"""Exact sleep-image printf switch inventory; no DDR admission.
SPDX-License-Identifier: LGPL-3.0-or-later
"""
import argparse,hashlib,json,struct
from pathlib import Path

def mapped(data,address,size):
 if data[:7]!=b'\x7fELF\x01\x01\x01' or struct.unpack_from('<H',data,18)[0]!=189:raise ValueError('Expected little-endian ELF32 MicroBlaze')
 off=struct.unpack_from('<I',data,28)[0];ents,count=struct.unpack_from('<HH',data,42)
 hits=[]
 for i in range(count):
  kind,pos,va,pa,filesz,memsz,flags,align=struct.unpack_from('<8I',data,off+i*ents)
  if kind==1 and va<=address and address+size<=va+filesz:
   raw=data[pos+address-va:pos+address-va+size]
   if len(raw)!=size:raise ValueError('Truncated mapping')
   hits.append(raw)
 if len(hits)!=1:raise ValueError('Ambiguous/non-file-backed address')
 return hits[0]

def check(data):
 # Bind instruction bytes including delayed upper-bound branch/shift.
 expected={0xffdcc99c:0x30800015,0xffdcc9d0:0x3063ff9d,
  0xffdcc9d4:0x16432003,0xffdcc9d8:0xbe52fff0,0xffdcc9dc:0x64630402,
  0xffdcc9e0:0xb000ffdd,0xffdcc9e4:0x306335d0,0xffdcc9e8:0xe8630000,
  0xffdcc9ec:0x98081800}
 for pc,word in expected.items():
  if struct.unpack('<I',mapped(data,pc,4))[0]!=word:raise ValueError('Changed switch instruction '+hex(pc))
 table=struct.unpack('<22I',mapped(data,0xffdd35d0,88))
 if any(t&3 or not 0xffdcc810<=t<0xffdccbc0 for t in table):raise ValueError('Switch target outside printf')
 return {'status':'EXACT_PRINTF_TABLE_INVENTORY_NOT_EXCLUSION_PROOF','hardware_executed':False,'destructive_test_allowed':False,'elf_sha256':hashlib.sha256(data).hexdigest(),'table_start':'0xffdd35d0','table_bytes':88,'index_count':22,'entries':[{'index':i,'format_character':chr(99+i),'target':hex(t)} for i,t in enumerate(table)],'unique_targets':[hex(t) for t in sorted(set(table))],'limits':'Exact instruction/table bytes and target range checked; unsigned bound semantics and domination of all paths require separate CFG proof. No full memory/ROM/reset/exception exclusion.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--elf',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 with a.output.open('x') as f:json.dump(check(a.elf.read_bytes()),f,indent=2);f.write('\n')
