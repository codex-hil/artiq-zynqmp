#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Bind actual Gray source objects/owners to unchanged emitted candidate RTL."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
from unittest.mock import patch
from migen.genlib.cdc import GrayCounter,MultiReg
from migen.fhdl import verilog
from aux_gray_pointer import AuxGrayPointer
import master_cdc_inventory as inventory
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args()
original_collect=inventory.collect;original_convert=verilog.convert;captured={}
def collect(fragment,top=None,source_notes=None):
 sources={}
 def walk(module,path):
  if isinstance(module,GrayCounter):sources[module.q]=(path,'GrayCounter.q',module)
  if isinstance(module,AuxGrayPointer):sources[module.gray]=(path,'AuxGrayPointer.gray',module)
  for i,(name,child) in enumerate(module._submodules):walk(child,path+'/'+str(name or type(child).__name__)+':'+str(i))
 walk(top,'top');owners={}
 for domain,statements in fragment.sync.items():
  visitor=inventory.Assignments();visitor.visit(statements)
  for left,right in visitor.items:
   for signal in left:owners.setdefault(signal,set()).add(domain)
 rows=[]
 for special in fragment.specials:
  if not isinstance(special,MultiReg):continue
  matches=[(signal,info) for signal,info in sources.items() if special.i is signal]
  if not matches:continue
  assert len(matches)==1;signal,(path,kind,module)=matches[0]
  origin=sorted(owners.get(signal,set()));assert len(origin)==1,(path,origin)
  rows.append((signal,special,path,kind,origin[0]))
 assert len(rows)==16,(len(rows),[(r[2],r[3]) for r in rows]);captured['objects']=rows
 return original_collect(fragment,top,source_notes)
def convert(*args,**kwargs):
 result=original_convert(*args,**kwargs);captured['namespace']=result.ns;return result
exporter=Path(__file__).with_name('export-retained-local-physical.py');old=sys.argv
try:
 sys.argv=[str(exporter),str(a.output),'--confirm-shared-reset-policy','--confirm-parent-reset-contract']
 with patch('master_cdc_inventory.collect',collect),patch('migen.fhdl.verilog.convert',convert):runpy.run_path(str(exporter),run_name='__main__')
finally:sys.argv=old
ns=captured['namespace'];endpoints=json.loads((a.output/'cdc-endpoints.json').read_text())['multiregs'];rows=[]
for signal,special,path,kind,domain in captured['objects']:
 name=ns.get_name(signal);output=ns.get_name(special.o)
 matched=[e for e in endpoints if e['input_signals']==[name] and e['output_signals']==[output]];assert len(matched)==1
 e=matched[0]
 rows.append(dict(source_name=name,object_path=path,kind=kind,source_domain=domain,destination=special.odomain,declared_bits=len(signal),stage_registers=e['stage_registers']))
rows.sort(key=lambda r:r['stage_registers'][0]);(a.output/'gray-source-objects.json').write_text(json.dumps(rows,indent=2)+'\n')
print('SIXTEEN_ACTUAL_REGISTERED_GRAY_SOURCE_OBJECTS_BOUND')
