#!/usr/bin/env python3
"""Pin AMD AFI reset paths; no reset execution or DDR permit. LGPL-3.0-or-later."""
import argparse,hashlib,json,re
from pathlib import Path
ANCHORS={
'pm_reset.c':['static PmResetGeneric pmResetAfiFm2 = {','.mask = CRF_APB_RST_FPD_TOP_AFI_FM2_RESET_MASK,','.resetAssert = &PmResetAssertGen,','XPfw_RMW32(ctrlAddr, mask, 0U);','XPfw_RMW32(ctrlAddr, mask, mask);'],
'crf_apb.h':['#define CRF_APB_RST_FPD_TOP ', '#define CRF_APB_RST_FPD_TOP_AFI_FM2_RESET_MASK    ((u32)0X00000200U)'],
'afi.h':['#define AFI_FM2_BASEADDR                        ((u32)0xFD380000U)'],
'psu_init.tcl':['set psu_afi_config {','mask_write 0XFD1A0100 0x00001F80 0x00000000']}
def audit(paths):
 if set(paths)!=set(ANCHORS):raise ValueError('Exact source inventory required')
 sources={}
 for n,anchors in ANCHORS.items():
  p=Path(paths[n]);data=p.read_bytes();lines=data.decode().splitlines();matches={}
  for a in anchors:
   hits=[i for i,s in enumerate(lines,1) if a in s]
   if not hits:raise ValueError('Missing anchor '+n+': '+a)
   matches[a]=hits
  sources[n]={'path':str(p.resolve()),'sha256':hashlib.sha256(data).hexdigest(),'anchors':matches}
 return {'status':'OFFLINE_AFI_RESET_SOURCE_REVIEW','hardware_executed':False,'sources':sources,
 'findings':['AFIFM2 has separate generic reset control mask0x200 in RST_FPD_TOP; not PL fabric reset.',
 'Generated psu_afi_config releases AFI0..5 reset controls using mask0x1f80.',
 'PMU generic reset operations manipulate control bits; inspected anchors are not an interconnect drain certificate.'],
 'not_proven':['HP0 pending-transaction disposal/completion across AFI reset','AFI reset automatically follows fabric reset','Reset cannot be released by PMU later'],
 'destructive_test_allowed':False,'next':'Review isolation/quiesce acknowledgment protocol and read-only observations; no AFI reset write or inferred drain delay.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 paths={n:a.build/('sdt' if n=='psu_init.tcl' else 'pmu-app/src')/n for n in ANCHORS}
 r=audit(paths);a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
