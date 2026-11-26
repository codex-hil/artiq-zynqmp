#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Validate files only. Structural completeness NEVER admits hardware/runtime."""
import argparse,datetime,hashlib,json,re,stat
from pathlib import Path

# Geometry follows the GICv2 Linux driver; source is reference, not board state.
GEOMETRY_REFERENCE='https://raw.githubusercontent.com/torvalds/linux/master/drivers/irqchip/irq-gic.c'
DIST=0xf9010000;CPU=0xf9020000
FORBIDDEN={CPU+0xc,CPU+0x10,CPU+0x20,CPU+0x1000} # acknowledge/EOI/deactivate

def require(condition,message):
 if not condition:raise ValueError(message)

def uint(value,bits,path):
 require(type(value) is int and 0<=value<1<<bits,path+': unsigned integer required')
 return value

def irq_count(typer):return min(((typer&31)+1)*32,1020)

def addresses(count):
 result={CPU+x for x in (0,4,8,0x1c,0x14)}|{DIST,DIST+4}
 for offset,perword in ((0x100,32),(0x80,32),(0x400,4),(0x800,4),(0xc00,16)):
  result|={DIST+offset+4*i for i in range((count+perword-1)//perword)}
 return result

def sample(value,path):
 require(type(value) is dict and set(value)=={'banks'},path+': banks object required')
 banks=value['banks'];require(type(banks) is list and len(banks)==2,path+': both declared security views required')
 names=set();summary=[]
 for bank in banks:
  require(type(bank) is dict and set(bank)=={'view','cpu','current_el','daif','view_provenance','ctlr','pmr','bpr','abpr','rpr','distributor','read_addresses'},path+': bank fields incomplete/unknown')
  view=bank['view'];require(view in ('secure','nonsecure') and view not in names,path+': missing/duplicate bank view');names.add(view)
  require(type(bank['cpu']) is int and bank['cpu']==0,path+': CPU0 bank required')
  require(type(bank['current_el']) is int and bank['current_el'] in (1,2,3),path+': currentEL missing/invalid')
  uint(bank['daif'],64,path+'.daif');require(type(bank['view_provenance']) is str and bank['view_provenance'].strip(),path+': view provenance missing')
  for n,bits in [('ctlr',32),('pmr',8),('bpr',3),('abpr',3),('rpr',8)]:uint(bank[n],bits,path+'.'+n)
  d=bank['distributor'];require(type(d) is dict and set(d)=={'ctlr','typer','enable','group','priority','target','config'},path+': distributor incomplete/unknown')
  uint(d['ctlr'],32,path+'.dist.ctlr');count=irq_count(uint(d['typer'],32,path+'.dist.typer'))
  for key,perword in [('enable',32),('group',32),('priority',4),('target',4),('config',16)]:
   values=d[key];require(type(values) is list and len(values)==(count+perword-1)//perword,path+': truncated/oversized '+key)
   for x in values:uint(x,32,path+'.'+key)
  if count%32:require(d['enable'][-1]>>(count%32)==0,path+': reserved IRQ enable bits set')
  reads=bank['read_addresses'];require(type(reads) is list,path+': access log missing')
  for x in reads:uint(x,64,path+'.read_address')
  require(len(reads)==len(set(reads)),path+': duplicate read address')
  require(not set(reads)&FORBIDDEN,path+': acknowledgement/EOI/deactivate access forbidden')
  require(set(reads)==addresses(count),path+': register coverage mismatch')
  enabled=[irq for irq in range(count) if d['enable'][irq//32]>>(irq%32)&1]
  expected=[]
  for irq in (68,89):
   if irq<count:expected.append({'irq':irq,'enabled':irq in enabled,'raw_priority':d['priority'][irq//4]>>(8*(irq%4))&255,'raw_target':d['target'][irq//4]>>(8*(irq%4))&255})
  summary.append({'view':view,'slots_from_typer':count,'enabled_irqs':enabled,'enabled_outside_retained_195_irq_profile':[i for i in enabled if i>=195],'source_expected_irqs':expected})
 require(names=={'secure','nonsecure'},path+': incomplete view coverage')
 require(len({r['slots_from_typer'] for r in summary})==1,path+': inconsistent geometry across bank views')
 return summary

def validate(data,expected_image):
 require(type(data) is dict and set(data)=={'schema','kind','capture_id','board_serial','image_sha256','cpu','canonical_lease','transport','started_utc','ended_utc','before','after'},'top-level fields incomplete/unknown')
 require(data['schema']=='gic400-snapshot-v1','unsupported schema');require(data['kind'] in ('synthetic','capture'),'capture kind required')
 require(re.fullmatch('[0-9a-f]{64}',expected_image) is not None,'expected image digest invalid')
 require(data['image_sha256']==expected_image,'image identity mismatch')
 require(data['board_serial']=='210383B7F02DA','board identity mismatch');require(type(data['cpu']) is int and data['cpu']==0,'CPU identity mismatch')
 require(data['canonical_lease']=='/home/codex-hil/.cache/genesys-210383B7F02DA.lock','canonical lease metadata missing/mismatched')
 for name in ('capture_id','transport'):require(type(data[name]) is str and data[name].strip(),name+': provenance missing')
 times=[]
 for name in ('started_utc','ended_utc'):
  require(type(data[name]) is str,name+': timestamp required')
  value=datetime.datetime.fromisoformat(data[name].replace('Z','+00:00'));require(value.tzinfo is not None and value.utcoffset()==datetime.timedelta(0),name+': UTC timezone required');times.append(value)
 require(times[0]<=times[1],'capture time reversed')
 before=sample(data['before'],'before');sample(data['after'],'after');require(data['before']==data['after'],'unstable bookend observations')
 return {'status':'STRUCTURALLY_COMPLETE_SYNTHETIC' if data['kind']=='synthetic' else 'STRUCTURALLY_COMPLETE_UNVERIFIED_CAPTURE','structurally_complete':True,'hardware_admitted':False,'runtime_admitted':False,'kind':data['kind'],'banks':before,'geometry_reference':GEOMETRY_REFERENCE,'limitations':['Caller-supplied identity/lease/view metadata is not authenticated; no device access or lease acquisition occurs','Matching bookends do not exclude ABA/intervening changes, IRQs or incorrect bank access','Completeness does not prove priorities permit bounded nesting, FPU safety or stack adequacy','No freshness/current-image/physical clock/worker/management/recovery admission']}

def unique(pairs):
 result={}
 for key,value in pairs:
  require(key not in result,'duplicate JSON key: '+key);result[key]=value
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('snapshot',type=Path);p.add_argument('--expected-image-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();status=0
 try:
  info=a.snapshot.stat();require(stat.S_ISREG(info.st_mode),'regular snapshot file required');require(info.st_size<=2*1024*1024,'snapshot too large');raw=a.snapshot.read_bytes();require(len(raw)<=2*1024*1024,'snapshot grew beyond size limit');r=validate(json.loads(raw,object_pairs_hook=unique),a.expected_image_sha256);r['input_sha256']=hashlib.sha256(raw).hexdigest()
 except (ValueError,TypeError,KeyError,OSError) as error:
  r={'status':'REJECTED_INCOMPLETE_OR_INCONSISTENT','reason':str(error),'structurally_complete':False,'hardware_admitted':False,'runtime_admitted':False};status=2
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status']);raise SystemExit(status)
if __name__=='__main__':main()
