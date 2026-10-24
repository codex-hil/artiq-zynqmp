#!/usr/bin/env python3
"""Strict offline AIB snapshot decoder, never an isolation/write permit. LGPL-3.0-or-later."""
import argparse,json,re
from pathlib import Path
FIELDS=(('request_before',0xff413030),('type',0xff413038),('ack',0xff413040),('request_after',0xff413030))
MASK=0x30000

def parse(text):
 lines=text.splitlines()
 if lines.count('AIB_BEGIN')!=1 or lines.count('AIB_END')!=1:raise ValueError('Incomplete/duplicate AIB frame')
 a,b=lines.index('AIB_BEGIN'),lines.index('AIB_END')
 rows=[s for s in lines if s.startswith('AIB ')]
 if lines[a+1:b]!=rows or len(rows)!=8:raise ValueError('Wrong AIB extent')
 samples=[]
 for sample in range(2):
  values={}
  for (name,address),line in zip(FIELDS,rows[sample*4:sample*4+4]):
   m=re.fullmatch(r'AIB '+str(sample)+' '+name+' '+f'0x{address:08x}'+r' 0x([0-9a-fA-F]{8})',line)
   if not m:raise ValueError('Malformed/changed AIB field')
   values[name]=int(m[1],16)
  if values['request_before']!=values['request_after']:raise ValueError('Request changed within sample')
  values['selected_request']=values['request_before']&MASK;values['selected_ack']=values['ack']&MASK;values['selected_type']=values['type']&MASK
  samples.append(values)
 stable=samples[0]==samples[1]
 return dict(status='AIB_READ_ONLY_OBSERVATION',hardware_executed=False,sample_count=2,selected_mask=hex(MASK),samples=samples,stable_across_samples=stable,selected_inactive_observed=stable and all(not (s['selected_request']|s['selected_ack']) for s in samples),destructive_test_allowed=False,isolation_write_allowed=False,ownership='NOT_PROVEN',limits='Sequential non-atomic reads; brackets do not detect ABA or ACK/TYPE races. Clear bits are not a reservation, source halt, future release exclusion or completed request receipt. Decoder alone does not prove hardware provenance.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 with a.output.open('x') as f:json.dump(parse(a.input.read_text()),f,indent=2);f.write('\n')
