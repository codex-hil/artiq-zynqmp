#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Actual-artifact negative controls for helper frame and jump table audit."""
import argparse,importlib.util,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--elf',type=Path,required=True);p.add_argument('--disassembly',type=Path,required=True);a=p.parse_args()
spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('inspect-linked-helpers.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
elf=a.elf.read_bytes();text=a.disassembly.read_text();m.audit(elf,text)
def offset(address):
 phoff=struct.unpack_from('<Q',elf,32)[0];ents,count=struct.unpack_from('<HH',elf,54)
 for i in range(count):
  kind,flags,pos,va,pa,size,memsz,align=struct.unpack_from('<IIQQQQQQ',elf,phoff+i*ents)
  if kind==1 and va<=address<va+size:return pos+address-va
 raise AssertionError('missing segment')
def refused(b,t):
 try:m.audit(b,t)
 except (AssertionError,ValueError):return
 raise AssertionError('Unsafe mutation accepted')
# Keep text and instruction mutually consistent: a new 32B frame must fail
# the reviewed frame contract, not merely the ELF/text hash check.
b=bytearray(elf);struct.pack_into('<I',b,offset(0x404bd0),0xa9be7bfd)
line=next(line for line in text.splitlines() if '404bd0: a9bf7bfd' in line)
t=text.replace(line,line.replace('a9bf7bfd','a9be7bfd').replace('#-0x10','#-0x20'));refused(b,t)
# Jump table relocation outside its function.
b=bytearray(elf);b[offset(0x4050a8)]=0x80;refused(b,text)
# Changed disassembly must not be accepted against the original ELF.
refused(elf,text.replace('4013d8: d61f0000','4013d8: d63f0000'))
print('LINKED_HELPER_BASELINE_AND_THREE_MUTANT_REFUSALS_PASS')
