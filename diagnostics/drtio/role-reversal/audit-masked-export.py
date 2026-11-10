#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Narrow emitted-text delta audit; not sequential equivalence or CDC signoff."""
import hashlib,json,re,sys
from pathlib import Path
def audit(base,candidate):
 old=(base/'master_physical_candidate.v').read_text();new=(candidate/'master_physical_candidate.v').read_text()
 a=json.loads((base/'cdc-endpoints.json').read_text())['multiregs']
 b=json.loads((candidate/'cdc-endpoints.json').read_text())['multiregs']
 if len(a)!=49 or len(b)!=49:raise ValueError('Expected49 synchronizers')
 rename={};masks=[];unused=[]
 for x,y in zip(a,b):
  for field in ('bits','destination','requested_reset','lowered_register_reset'):
   if x[field]!=y[field]:raise ValueError('Unrelated synchronizer metadata changed')
  if x['stage_registers']!=y['stage_registers']:
   if len(x['input_signals'])!=1 or 'releases_local_ready' not in x['input_signals'][0]:
    raise ValueError('Unexpected synchronizer changed')
   source=x['input_signals'][0]
   reset=[n for n in y['input_signals'] if n!=source]
   if len(reset)!=1 or not reset[0].startswith('aux_release_'):raise ValueError('Unexpected mask source')
   for src,dst in zip(y['stage_registers'],x['stage_registers']):rename[src]=dst
   masks.append((f'({source} & (~{reset[0]}))',source))
 if len(masks)!=5 or len(rename)!=10:raise ValueError('Expected5 masks/10 register renames')
 for expression,source in masks:
  # Vendor lowering creates one unused combinational alias in addition to D expr.
  found=re.findall(r'^assign (\w+) = '+re.escape(expression)+r';$',new,re.M)
  if len(found)!=1:raise ValueError('Expected one exact unused alias')
  name=found[0]
  if len(re.findall(r'\b'+re.escape(name)+r'\b',new))!=2:raise ValueError('Alias not unused')
  declaration='wire '+name+';\n';assignment='assign '+name+' = '+expression+';\n'
  if new.count(declaration)!=1 or new.count(assignment)!=1:raise ValueError('Alias declaration mismatch')
  new=new.replace(declaration,'').replace(assignment,'');unused.append(name)
  if new.count(expression)!=1:raise ValueError('Expected one remaining mask on stage1 D')
  new=new.replace(expression,source)
 for src,dst in rename.items():new=re.sub(r'\b'+re.escape(src)+r'\b',dst,new)
 if new!=old:raise ValueError('Other generated RTL text changed')
 inits={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in base.glob('*.init')}
 if len(inits)!=6:raise ValueError('Expected six memoryinitializers')
 for name,h in inits.items():
  if hashlib.sha256((candidate/name).read_bytes()).hexdigest()!=h:raise ValueError('Memoryinit changed')
 return {'status':'NARROW_RTL_TEXT_DELTA_PASS','masks':5,'register_renames':10,
         'unused_generator_aliases':unused,'other_rtl_text_identical':True,
         'six_memory_init_hashes':inits,'limits':['Not sequential equivalence','Not CDC/reset/timing qualification']}
if __name__=='__main__':
 try:print(json.dumps(audit(Path(sys.argv[1]),Path(sys.argv[2])),indent=2))
 except (ValueError,OSError,IndexError) as e:print('MASKED_EXPORT_REFUSED: '+str(e),file=sys.stderr);sys.exit(1)
