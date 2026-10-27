#!/usr/bin/env python3
"""Offline directed AIB instance inventory; never DDR admission. LGPL-3.0-or-later."""
import argparse,json,re
from pathlib import Path
# UG1085 Table16-17 and exact lpd_slcr.h. Names describe direction, not DMA scope.
ROUTES={'RPUM0':(16,1,'RPU0','LPD'),'RPUM1':(17,2,'RPU1','LPD'),
 'LPD_DDR':(27,3,'RPU via LPD','DDR via FPD'),'FPD_MAIN':(24,4,'LPD','FPD other slaves'),
 'RPUS0':(18,5,'LPD','RPU0'),'RPUS1':(19,6,'LPD','RPU1'),
 'USB0S':(22,7,'LPD','USB0'),'USB1S':(23,8,'LPD','USB1'),
 'OCMS':(26,9,'LPD','OCM'),'AFIFS2':(28,10,'LPD','M_AXI_HPM0_LPD'),
 'FPD_LPDIBS':(2,11,'FPD','LPD except OCM'),'FPD_OCM':(3,12,'FPD','OCM'),
 'AFIFS0':(0,13,'FPD','M_AXI_HPM0_FPD'),'AFIFS1':(1,14,'FPD','M_AXI_HPM1_FPD')}
def verify_header(text):
 for kind in ['REQ','TYPE','ACK']:
  masks={n:int(v,16) for n,v in re.findall(r'#define LPD_SLCR_ISO_AIBAXI_'+kind+r'_(\w+)_MASK\s+\(\(u32\)0X([0-9A-F]+)U\)',text)}
  if masks!={n:1<<r[0] for n,r in ROUTES.items()}:raise ValueError('Changed/incomplete AIB header map')
def decode(request,ack,response_type):
 if not all(type(v) is int and 0<=v<2**32 for v in (request,ack,response_type)):raise ValueError('Expected unsigned32 words')
 known=sum(1<<r[0] for r in ROUTES.values())
 return dict(kind='DIRECTED_AIB_INSTANCE_OBSERVATION',destructive_test_allowed=False,isolation_write_allowed=False,
  instances=[dict(name=n,bit=r[0],instance=r[1],master=r[2],slave=r[3],request=bool(request&(1<<r[0])),ack=bool(ack&(1<<r[0])),type_bit=bool(response_type&(1<<r[0]))) for n,r in sorted(ROUTES.items(),key=lambda x:x[1][1])],unknown_bits={'request':hex(request&~known),'ack':hex(ack&~known),'type':hex(response_type&~known)},limits='Directed AXI instances only; APB GPU instance15 absent. Raw TYPE bit preserved without assigning response semantics. Observation is not full-master drain or ownership proof.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('request','ack','type'):p.add_argument('--'+n,type=lambda s:int(s,0),required=True)
 p.add_argument('--header',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify_header(a.header.read_text())
 with a.output.open('x') as f:json.dump(decode(a.request,a.ack,a.type),f,indent=2);f.write('\n')
