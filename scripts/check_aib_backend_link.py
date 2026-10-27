#!/usr/bin/env python3
"""Exact audit-link callback/address-table checks, not deployment. LGPL-3.0-or-later."""
import argparse,json,re,struct
from pathlib import Path
from check_pmu_printf_table import mapped

def check(elf,symbols):
 funcs={}
 for n in ('read_reg','write_request','ticks'):
  found=re.findall(r'^([0-9a-f]+) [0-9a-f]+ t '+n+'$',symbols,re.M)
  if len(found)!=1:raise ValueError('Missing/ambiguous backend callback '+n)
  funcs[n]=int(found[0],16)
 addresses=struct.unpack('<3I',mapped(elf,0xffdd42c4,12))
 if addresses!=(0xff413030,0xff413040,0xff413038):raise ValueError('Backend enum address table changed')
 expected={0xffdcfcdc:0xb0000000|(funcs['read_reg']>>16),0xffdcfce0:0x30c00000|(funcs['read_reg']&0xffff),
  0xffdcfcec:0xb0000000|(funcs['write_request']>>16),0xffdcfcf0:0x30800000|(funcs['write_request']&0xffff),
  0xffdcfcf8:0xb0000000|(funcs['ticks']>>16),0xffdcfcfc:0x30c00000|(funcs['ticks']&0xffff),
  0xffdcfcf4:0xf8d30014,0xffdcfd00:0xf8930018,0xffdcfd0c:0xf8d3001c}
 for pc,word in expected.items():
  if struct.unpack('<I',mapped(elf,pc,4))[0]!=word:raise ValueError('Changed linked callback assignment '+hex(pc))
 return {'status':'EXACT_AUDIT_CALLBACK_ASSIGNMENT_PASS_NOT_HARDWARE','hardware_executed':False,'destructive_test_allowed':False,'callbacks':{k:hex(v) for k,v in funcs.items()},'enum_read_table':[hex(a) for a in addresses],'limits':'Checks one exact linked build. Underlying transport callbacks, caller storage, control flow and all access paths not established.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('elf','symbols','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args()
 with a.output.open('x') as f:json.dump(check(a.elf.read_bytes(),a.symbols.read_text()),f,indent=2);f.write('\n')
