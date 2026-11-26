#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Mutant ELF/frame controls for exact static-network stack inventory."""
import argparse,hashlib,importlib.util,json,shutil,struct,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
s=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('inspect-network-static-stack.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
r=m.inspect(a.artifacts);assert {n:v['bytes'] for n,v in r['conditional_frame_sums'].items()}=={'mns_begin':448,'mns_poll':576,'mns_snapshot':368}
a.output.mkdir(parents=True,exist_ok=False);runs={}
for name in ('inverted-active-guard','changed-observer-register','missing-observer-frame'):
 d=a.output/name;d.mkdir()
 for f in a.artifacts.iterdir():
  if f.name in ('codec-normal.elf','execution-results.json','stack-sizes.txt') or f.name.startswith('codec-normal') and f.suffix=='.su':shutil.copy2(f,d/f.name)
 elf=d/'codec-normal.elf'
 if name=='missing-observer-frame':
  f=d/'codec-normal.elf-test_master_network_static.su';f.write_text(''.join(l for l in f.read_text().splitlines(True) if ':health\t' not in l))
 else:
  data=bytearray(elf.read_bytes());address,word=(0x4022f0,0x34001bda) if name=='inverted-active-guard' else (0x402184,0xd63f0060)
  off=struct.unpack_from('<Q',data,32)[0];size,count=struct.unpack_from('<HH',data,54)
  for i in range(count):
   kind,flags,pos,va,pa,n,memsz,align=struct.unpack_from('<IIQQQQQQ',data,off+i*size)
   if kind==1 and va<=address<va+n:struct.pack_into('<I',data,pos+address-va,word);break
  else:raise AssertionError('Address not file-backed')
  elf.write_bytes(data)
 receipt=json.loads((d/'execution-results.json').read_text());receipt['runs']['normal']['elf_sha256']=hashlib.sha256(elf.read_bytes()).hexdigest();(d/'execution-results.json').write_text(json.dumps(receipt))
 text=subprocess.check_output(['/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/bin/llvm-objdump-19','-d',str(elf)],text=True);(d/'full-disassembly.txt').write_text(text)
 try:m.inspect(d)
 except AssertionError as error:runs[name]={'refused':True,'reason':str(error),'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest()}
 else:raise AssertionError('Unsafe mutation accepted')
report={'status':'NETWORK_STATIC_STACK_BASELINE_AND_THREE_MUTANT_REFUSALS_PASS','mutants_not_executed':True,'runs':runs}
(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
