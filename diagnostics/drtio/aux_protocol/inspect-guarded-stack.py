#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Read-only retained ELF/target .su inventory; never infer runtime admission."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--retained-elf',type=Path,required=True);p.add_argument('--linker',type=Path,required=True);p.add_argument('--target-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
raw=subprocess.check_output(['readelf','-sW',str(a.retained_elf)],text=True)
expected={'_STACK_SIZE':40960,'_EL1_STACK_SIZE':2048,'_EL0_STACK_SIZE':1024,'_EL2_STACK_SIZE':1024};symbols={}
for line in raw.splitlines():
 fields=line.split()
 if len(fields)>=8 and fields[-1] in expected and fields[-2]=='ABS':symbols[fields[-1]]=int(fields[1],16)
assert symbols==expected,('Retained stack layout changed; review required',symbols)
rows=[];files=sorted(a.target_dir.glob('*.su'))
for f in files:
 for line in f.read_text().splitlines():
  fields=line.split('\t');assert len(fields)==3,(f,line)
  rows.append(dict(report=f.name,function=fields[0],frame_bytes=int(fields[1]),qualifier=fields[2]))
nm=a.target_dir/'guarded-stack-symbols.txt';context=None
if nm.exists():
 for line in nm.read_text().splitlines():
  fields=line.split()
  if len(fields)==4 and fields[-1]=='master_guarded_context_size':context=int(fields[1],16)
 probe_rows=[r for r in rows if r['report']=='guarded-stack-probe.su']
 assert context and probe_rows,'Missing target layout symbol/frame probe'
else:probe_rows=[]
ready=bool(context and probe_rows)
r={'status':'TARGET_FRAME_INVENTORY_AVAILABLE_RUNTIME_STACK_NOT_QUALIFIED' if ready else 'RETAINED_STACK_INVENTORY_PASS_TARGET_FRAME_REPORT_PENDING','runtime_admitted':False,'hardware_admitted':False,'retained_elf':str(a.retained_elf),'retained_elf_sha256':digest(a.retained_elf),'linker':str(a.linker),'linker_sha256':digest(a.linker),'retained_stack_bytes':symbols,'target_context_bytes':context,'target_probe_frames':probe_rows,'all_target_frames':rows,'target_report_sha256':{f.name:digest(f) for f in files},'limits':['Retained OctoberELF is source/artifact reference, not current device or activeEL/SP observation','Compiler .su per-function frames are not completecallchain/IRQ/lwIP/Rust-library stack highwater bound','Context size is an unlinked layout-probe symbol, not mandatory stack allocation or production placement','Need exactproductionlinker/EL/SP/caller/objectplacement andcallgraph/interrupt/nesting analysis beforeintegration','No firmware/HW/default changes']}
if nm.exists():r['target_symbols_sha256']=digest(nm)
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
