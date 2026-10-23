#!/usr/bin/env python3
"""Inspect actual linked guard flow; never grants physical DDR admission. LGPL-3.0-or-later."""
import argparse,json,re
from pathlib import Path
from check_pmu_boundary_image import check as check_layout

def check(elf,symbols,disassembly):
 layout=check_layout(elf,symbols)
 found=re.findall(r'^([0-9a-f]+) ([0-9a-f]+) [tT] artiq_pmu_enter_lab_guard$',symbols,re.M)
 record=re.findall(r'^([0-9a-f]+) 00000040 b artiq_pmu_guard$',symbols,re.M)
 helper=re.findall(r'^([0-9a-f]+) [0-9a-f]+ T microblaze_disable_interrupts$',symbols,re.M)
 if len(found)!=1 or len(record)!=1 or len(helper)!=1:raise ValueError('Guard/helper/local record missing')
 start,size=(int(v,16) for v in found[0]);record=int(record[0],16);helper=int(helper[0],16)
 if not 0xffdc0000<=record<record+64<=int(layout['stack']['start'],16):raise ValueError('Guard record outside local data')
 rows=[]
 for line in disassembly.splitlines():
  m=re.fullmatch(r'([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)',line)
  if m and start<=int(m[1],16)<start+size:rows.append((int(m[1],16),int(m[2],16),m[3]))
 if [a for a,w,s in rows]!=list(range(start,start+size,4)):raise ValueError('Incomplete guard instructions')
 if any(re.match(r'(rtsd|rtid|rtbd|rted|brad|brald|braid|bralid)\b',s) for a,w,s in rows):raise ValueError('Guard returns/escapes unexpectedly')
 calls=[i for i,(a,w,s) in enumerate(rows) if s.startswith('brlid')]
 if len(calls)!=1:raise ValueError('Unexpected guard calls')
 i=calls[0];previous=rows[i-1][1]
 if previous>>16!=0xb000:raise ValueError('Expected extended relative helper call')
 offset=((previous&0xffff)<<16)|(rows[i][1]&0xffff)
 if offset&0x80000000:offset-=1<<32
 if rows[i][0]+offset!=helper:raise ValueError('Guard call not interrupt-only helper')
 for index,(address,word,instruction) in enumerate(rows):
  if not instruction.startswith('b') or index==i or index==len(rows)-1:continue
  target=re.search(r'// ([0-9a-f]+)\s*$',instruction)
  if not instruction.startswith('beqid') or not target or not start<=int(target[1],16)<start+size:raise ValueError('Unexpected guard branch')
 # Require publication barrier followed by sleep/backward branch. Wake resumes
 # only at the branch back to sleep; no memory operation lies in that loop.
 if [r[1] for r in rows[-3:]]!=[0xb8220004,0xba020004,0xb800fffc]:raise ValueError('Guard terminal not ordered sleep loop')
 return dict(status='LINKED_LAB_GUARD_FLOW_PASS_NOT_HARDWARE',hardware_executed=False,guard_start=hex(start),guard_bytes=size,record_start=hex(record),terminal_pc=hex(rows[-2][0]),terminal_mode='sleep-reentry',interrupt_helper=hex(helper),destructive_test_allowed=False,limits='Actual static flow and local layout only; live MSR/ROM/NMI/history/core exclusion unproven. Host backend tests do not substitute for PMU execution.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['elf','symbols','disassembly','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();r=check(a.elf.read_bytes(),a.symbols.read_text(),a.disassembly.read_text())
 with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
