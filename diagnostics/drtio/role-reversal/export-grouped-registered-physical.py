#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate combined export; explicit reset-policy review remains an obligation."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
from unittest.mock import patch
from migen import Module
from aux_reset_control import AuxResetControl as OriginalControl
from aux_reset_registered import AuxResetRegistered
from aux_reset_domains_grouped import AuxResetDomainsGrouped
from master_physical_assembly import MasterPhysicalAssembly as OriginalAssembly

class RegisteredCoordinator(Module):
 def __init__(self,domains):
  if domains!=5:raise ValueError('Five logical domains required')
  self.submodules.raw=raw=OriginalControl(domains)
  self.submodules.outputs=out=AuxResetRegistered(raw,control='sys')
  for name in ('request','requester_abandoned','domain_ready'):
   setattr(self,name,getattr(raw,name))
  for name in ('reset','admit','abandonment_ready'):
   setattr(self,name,getattr(out,name))

def grouped(domains,*,control):
 if tuple(domains)!=('ps','sys','rtio_rx','rio','rio_phy'):
  raise ValueError('Unexpected logical domain mapping')
 return AuxResetDomainsGrouped(control=control,shared_tx_clock_confirmed=True,
                               shared_reset_policy_confirmed=True)

class CheckedAssembly(OriginalAssembly):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  # Inspect actual parent connections, before conversion; frequency equality
  # alone would not establish that these domains share the same clock signal.
  for name in ('sys','rio','rio_phy'):
   clk=getattr(self.core,'cd_'+name).clk
   drivers=[s for s in self.core._fragment.comb if getattr(s,'l',None) is clk]
   if len(drivers)!=1 or drivers[0].r is not self.phy.tx_clock:
    raise ValueError('Common TX signal identity not established: '+name)

p=argparse.ArgumentParser();p.add_argument('output',type=Path)
p.add_argument('--confirm-shared-reset-policy',action='store_true',required=True)
a=p.parse_args();exporter=Path(__file__).with_name('export-physical-assembly.py')
old=sys.argv
try:
 sys.argv=[str(exporter),str(a.output),'--guarded-candidate']
 with patch('master_dual_ingress.AuxResetControl',RegisteredCoordinator), \
      patch('master_dual_ingress.AuxResetDomains',side_effect=grouped), \
      patch('master_physical_assembly.MasterPhysicalAssembly',CheckedAssembly):
  runpy.run_path(str(exporter),run_name='__main__')
finally:sys.argv=old
f=a.output/'export.json';r=json.loads(f.read_text())
r['variant']='SEPARATE_GROUPED_REGISTERED_MASKED_NOT_ADOPTED'
r['common_tx_clock']='Actual parent assignment RHS object identity checked for SYS/rio/rio_phy'
r['reset_policy']='Explicit caller confirmation; semantic baseline audit still required'
r['manifest_scope']='Original contract baseline only; no variant or deployment attestation'
root=exporter.resolve().parents[3]
for name in ('aux_reset_registered.py','aux_reset_domains_grouped.py','aux_reset_domains_masked.py','role-reversal/export-grouped-registered-physical.py'):
 rel='diagnostics/drtio/'+name
 r['assembly_source_sha256'][rel]=hashlib.sha256((root/rel).read_bytes()).hexdigest()
f.write_text(json.dumps(r,indent=2)+'\n')
print('COMBINED_EXPORT_PASS_NOT_DEPLOYED')
