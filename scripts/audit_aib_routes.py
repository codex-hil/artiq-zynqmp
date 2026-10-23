#!/usr/bin/env python3
"""Review AIB route scope and failure handling offline; LGPL-3.0-or-later."""
import argparse,hashlib,json
from pathlib import Path
ANCHORS={
'xpfw_aib.c':['void XPfw_AibEnable(enum XPfwAib AibId)','LPD_SLCR_ISO_AIBAXI_REQ_AFIFS0_MASK,','Status = XPfw_Read32(LPD_SLCR_ISO_AIBAXI_ACK) & AibMask[AibId];','} while (TimeOutCount > 0U);','if (Status == 0U) {','No AIB#%d ack'],
'xpfw_aib.h':['XPFW_AIB_FPD_TO_AFI_FS0,','XPFW_AIB_FPD_TO_AFI_FS1,','XPFW_AIB_LPD_TO_AFI_FS2,','void XPfw_AibEnable(enum XPfwAib AibId);'],
'psu_init.tcl':['set psu_ps_pl_isolation_removal_data {','mask_write 0XFFD80120 0x00800000 0x00800000','mask_poll 0XFFD80110 0x00800000 0x00000000']}
def audit(paths):
 if set(paths)!=set(ANCHORS):raise ValueError('Exact source inventory required')
 sources={}
 for role,needles in ANCHORS.items():
  p=Path(paths[role]);data=p.read_bytes();lines=data.decode().splitlines();anchors={}
  for needle in needles:
   hits=[i for i,line in enumerate(lines,1) if needle in line]
   if not hits:raise ValueError('Missing '+role+' anchor '+needle)
   anchors[needle]=hits
  sources[role]={'path':str(p.resolve()),'sha256':hashlib.sha256(data).hexdigest(),'anchors':anchors}
 return dict(status='OFFLINE_AIB_SCOPE_REVIEW',hardware_executed=False,sources=sources,
  findings=['Named AFI_FS routes originate in PS FPD/LPD; no AFIFM2/HP0 PL-to-DDR isolation certificate established.',
   'XPfw_AibEnable polls ACK with bounded retries, logs missing ACK, returns void; call completion is not ACK success.',
   'Generated isolation-removal helper requests PL power-up and polls PMU power status; not HP0 outstanding count.'],
  rejected_shortcuts=['AFI_FS ACK interpreted as HP0 PL-master drain','Void helper return interpreted as successful isolation','PL power-up status interpreted as DDR ownership'],
  destructive_test_allowed=False,
  next='Prefer an explicit no-PL-master diagnostic image plus continuous AXI epoch tracking; separately resolve PMU/secondary-core ownership. No AIB writes from this audit.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=audit({n:a.build/('sdt' if n=='psu_init.tcl' else 'pmu-app/src')/n for n in ANCHORS})
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
