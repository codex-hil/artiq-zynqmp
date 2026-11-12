#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate retained-reset/local-boundary assembly, no default substitution."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
from unittest.mock import patch
from migen import Module
from aux_reset_domains_retained import AuxResetDomainsRetained
from master_admission_registered import MasterAdmissionRegistered
from master_link_local_reset import MasterLinkLocalReset
class RegisteredLocalBoundary(Module):
 def __init__(self,codec,admit,reset_request,status):
  self.submodules.sample=s=MasterAdmissionRegistered(admit,reset_request)
  self.submodules.boundary=b=MasterLinkLocalReset(codec,s.allowed,reset_request,status,parent_reset_contract_confirmed=True)
  self.allowed=b.allowed;self.gt_reset_request=b.gt_reset_request
p=argparse.ArgumentParser();p.add_argument('output',type=Path)
p.add_argument('--confirm-shared-reset-policy',action='store_true',required=True)
p.add_argument('--confirm-parent-reset-contract',action='store_true',required=True)
a=p.parse_args();exporter=Path(__file__).with_name('export-grouped-registered-physical.py');old=sys.argv
try:
 sys.argv=[str(exporter),str(a.output),'--confirm-shared-reset-policy']
 with patch('aux_reset_domains_grouped.AuxResetDomainsGrouped',AuxResetDomainsRetained),patch('master_link_boundary.MasterLinkBoundary',RegisteredLocalBoundary):
  runpy.run_path(str(exporter),run_name='__main__')
finally:sys.argv=old
f=a.output/'export.json';r=json.loads(f.read_text());r['variant']='SEPARATE_RETAINED_RELEASE_REGISTERED_ADMISSION_LOCAL_RESET_NOT_ADOPTED'
r['parent_reset_contract']='Explicit fixture confirmation only; running-clock full integration and isolated FDPE stopped-clock evidence remain separate, not full physical qualification'
r['latency']='One added control admission edge; local-reset boundary can reopen earlier than original requested-status path'
root=exporter.resolve().parents[3]
for name in ('aux_reset_domains_retained.py','aux_reset_retention.py','master_admission_registered.py','master_link_local_reset.py','role-reversal/export-retained-local-physical.py'):
 rel='diagnostics/drtio/'+name;r['assembly_source_sha256'][rel]=hashlib.sha256((root/rel).read_bytes()).hexdigest()
f.write_text(json.dumps(r,indent=2)+'\n');print('RETAINED_LOCAL_EXPORT_PASS_NOT_DEPLOYED')
