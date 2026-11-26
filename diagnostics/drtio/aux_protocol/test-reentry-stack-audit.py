#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Mutate ELF guard behavior, not just text; require stack audit refusal."""
import argparse,hashlib,importlib.util,json,shutil,struct,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('inspect-reentry-stack.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
baseline=m.inspect(a.artifacts);assert baseline['conditional_frame_sums']['mfc_poll']['bytes']==576
assert {n:r['frame_bytes'] for n,r in baseline['rejected_entry_paths'].items()}=={'mfc_begin':0,'mfc_poll':128,'mfc_cancel':0,'mfc_snapshot':0}
a.output.mkdir(parents=True,exist_ok=False);runs={}
for name in ('guard-inverted','wrong-busy-code','missing-probe-frame'):
 d=a.output/name;d.mkdir()
 for f in a.artifacts.iterdir():
  if f.name in ('codec-normal.elf','execution-results.json','stack-sizes.txt') or f.name.startswith('codec-normal') and f.suffix=='.su':shutil.copy2(f,d/f.name)
 elf=d/'codec-normal.elf'
 if name=='missing-probe-frame':
  f=d/'codec-normal.elf-test_master_static_caller.su';f.write_text(''.join(line for line in f.read_text().splitlines(True) if ':probe_reentry\t' not in line))
 else:
  data=bytearray(elf.read_bytes());address,word=(0x4024b4,0x34001b00) if name=='guard-inverted' else (0x402814,0x12800040)
  phoff=struct.unpack_from('<Q',data,32)[0];ents,count=struct.unpack_from('<HH',data,54)
  for i in range(count):
   kind,flags,offset,va,pa,size,memsz,align=struct.unpack_from('<IIQQQQQQ',data,phoff+i*ents)
   if kind==1 and va<=address<va+size:struct.pack_into('<I',data,offset+address-va,word);break
  else:raise AssertionError('Address absent')
  elf.write_bytes(data)
 # Freeze new mutant hash and regenerate disassembly, so guard refusal cannot
 # be attributed merely to stale hashes or text/ELF mismatch.
 receipt=json.loads((d/'execution-results.json').read_text());receipt['runs']['normal']['elf_sha256']=hashlib.sha256(elf.read_bytes()).hexdigest();(d/'execution-results.json').write_text(json.dumps(receipt))
 text=subprocess.check_output(['/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/bin/llvm-objdump-19','-d',str(elf)],text=True);(d/'full-disassembly.txt').write_text(text)
 try:m.inspect(d)
 except AssertionError as error:runs[name]={'refused':True,'reason':str(error),'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest()}
 else:raise AssertionError('Unsafe audit mutant accepted: '+name)
result={'status':'GUARDED_STACK_BASELINE_AND_THREE_MUTANT_REFUSALS_PASS','mutants_not_executed':True,'runs':runs}
(a.output/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
