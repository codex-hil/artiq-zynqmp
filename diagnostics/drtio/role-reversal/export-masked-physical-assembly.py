#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate candidate export via scoped substitution; no default assembly change."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
from unittest.mock import patch
from aux_reset_domains_masked import AuxResetDomainsMasked
p=argparse.ArgumentParser();p.add_argument('output',type=Path);args=p.parse_args()
exporter=Path(__file__).with_name('export-physical-assembly.py')
original_argv=sys.argv
try:
 sys.argv=[str(exporter),str(args.output),'--guarded-candidate']
 with patch('master_dual_ingress.AuxResetDomains',AuxResetDomainsMasked):
  runpy.run_path(str(exporter),run_name='__main__')
finally:sys.argv=original_argv
report_path=args.output/'export.json';r=json.loads(report_path.read_text())
r['variant']='SEPARATE_MASKED_READY_NOT_ADOPTED'
r['manifest_scope']='Original v1 contract is a baseline only; no deployment capability or variant attestation'
root=exporter.resolve().parents[3]
for name in ('diagnostics/drtio/aux_reset_domains_masked.py','diagnostics/drtio/role-reversal/export-masked-physical-assembly.py'):
 r['assembly_source_sha256'][name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
report_path.write_text(json.dumps(r,indent=2)+'\n')
print('MASKED_PHYSICAL_CANDIDATE_EXPORT_PASS_NOT_DEPLOYED')
