#!/usr/bin/env python3
"""Audit generated PL reset topology without granting DDR admission; LGPL-3.0-or-later."""
import argparse,hashlib,json
from pathlib import Path

ANCHORS={
 'top.v':['assign async_reset = (~pl_resetn0__SHIFTED);','assign saxihp0_fpd_aclk__SHIFTED = sys_clk;','assign epoch_qualified = 1\'d0;','.PRE(async_reset)','.Q(sys_rst)','if (sys_rst) begin','.saxihp0_fpd_aclk(saxihp0_fpd_aclk)','.pl_resetn0(pl_resetn0)'],
 'gateware.py':['self.cd_sys, ~self.zynq_ultra_ps_e_0.outputs["pl_resetn0"]','ps.inputs["saxihp0_fpd_aclk"].eq(self.cd_sys.clk)'],
 'observer.py':['self.epoch_qualified=Signal()','self.outstanding=Signal(max=capacity+1)','self.sync += ['],
 'psu_init.tcl':['set psu_ps_pl_reset_config_data {','mask_write 0XFF0A0054 0xFFFFFFFF 0x00000000','mask_write 0XFF0A0054 0xFFFFFFFF 0x80000000']}

def audit(paths):
 if set(paths)!=set(ANCHORS):raise ValueError('Exact source inventory required')
 result={}
 for role,needles in ANCHORS.items():
  p=Path(paths[role]);data=p.read_bytes();lines=data.decode().splitlines();anchors={}
  for needle in needles:
   found=[i for i,line in enumerate(lines,1) if needle in line]
   if not found:raise ValueError('Missing '+role+' anchor '+needle)
   anchors[needle]=found
  result[role]={'path':str(p.resolve()),'sha256':hashlib.sha256(data).hexdigest(),'anchors':anchors}
 return dict(status='OFFLINE_SOURCE_TOPOLOGY_AUDIT',hardware_executed=False,sources=result,
             established=['Generated PS pl_resetn0 drives asynchronous assert/two-flop sys reset release.',
                          'HP0 interface clock uses sys clock; observer epoch qualification tied zero.',
                          'Observer state uses sys synchronous reset and loses prior accounting history.',
                          'Generated PS initialization toggles GPIO bank5 high/low/high; internal PS mapping not proven here.'],
             not_proven=['HP0 PS endpoint/FIFO reset coverage and completion','No accepted PS transactions survive PL accounting reset','PMU cannot release or initiate another DDR owner','Generated source equivalence to trained-boot PL state'],
             required_next='Review PS IP implementation/register reset coverage and establish a single qualified epoch or use separately qualified no-PL boot; do not arm epoch from a delay or sampled zero.',
             destructive_test_allowed=False)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['top','gateware','observer','ps-init']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=audit(dict(zip(ANCHORS,[a.top,a.gateware,a.observer,a.ps_init])))
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
