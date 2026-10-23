#!/usr/bin/env python3
"""Check linked PMU-local telemetry image footprint, not deployment. LGPL-3.0-or-later."""
import argparse,json,re,hashlib
from pathlib import Path
from package_local_candidate import loads
BASE=0xffdc0000;RAM_END=0xffddf6e0;TABLE_END=0xffddfae0

def check(data,text):
 machine,entry,parts=loads(data)
 if machine!=189 or entry!=0xffdc0050:raise ValueError('Wrong MicroBlaze PMU image')
 if len(parts)!=3 or any(p['vaddr']!=p['address'] for p in parts):raise ValueError('Unexpected PMU load layout')
 for p in parts:
  lo=p['address'];hi=lo+p['memsz']
  if not ((BASE<=lo<hi<=RAM_END) or (lo==RAM_END and hi==TABLE_END)):raise ValueError('PMU segment outside local RAM/table')
 ordered=sorted(parts,key=lambda p:p['address'])
 if any(a['address']+a['memsz']>b['address'] for a,b in zip(ordered,ordered[1:])):raise ValueError('Overlapping PMU segments')
 symbols={}
 for line in text.splitlines():
  m=re.fullmatch(r'([0-9a-fA-F]+) (?:([0-9a-fA-F]+) )?([a-zA-Z]) (\S+)',line)
  if m:symbols[m[4]]=(int(m[1],16),int(m[2],16) if m[2] else None,m[3])
 record=symbols.get('artiq_pmu_boundary');stacklo=symbols.get('_stack_end');stackhi=symbols.get('_stack')
 if not record or record[1:]!=(32,'b') or not stacklo or not stackhi:raise ValueError('Missing/wrong PMU telemetry or stack')
 addr=record[0];lo=stacklo[0];hi=stackhi[0]
 if not BASE<=addr<addr+32<=lo<hi<=RAM_END:raise ValueError('Record/stack overlap or not PMU RAM')
 if not any(p['address']+p['filesz']<=addr and addr+32<=p['address']+p['memsz'] for p in parts):raise ValueError('Telemetry not zero-init segment memory')
 return dict(status='PMU_BOUNDARY_LOCAL_LAYOUT_PASS_NOT_HARDWARE',hardware_executed=False,entry=hex(entry),telemetry=dict(start=hex(addr),bytes=32),stack=dict(start=hex(lo),end_exclusive=hex(hi)),bytes_after_stack_before_extension_table=RAM_END-hi,destructive_test_allowed=False,limits='PMU-local layout only; RWE legacy segment flags retained. No boot/telemetry-access/coherence/quiescence proof.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--elf',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=check(a.elf.read_bytes(),a.symbols.read_text());r['elf_sha256']=hashlib.sha256(a.elf.read_bytes()).hexdigest()
 with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
