#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Scoped admission substitution over separate combined reset candidate only."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
from unittest.mock import patch
from master_admission_registered import MasterLinkBoundaryRegistered
p=argparse.ArgumentParser();p.add_argument('output',type=Path)
p.add_argument('--confirm-shared-reset-policy',action='store_true',required=True)
a=p.parse_args();exporter=Path(__file__).with_name('export-grouped-registered-physical.py')
old=sys.argv
try:
 sys.argv=[str(exporter),str(a.output),'--confirm-shared-reset-policy']
 with patch('master_link_boundary.MasterLinkBoundary',MasterLinkBoundaryRegistered):
  runpy.run_path(str(exporter),run_name='__main__')
finally:sys.argv=old
f=a.output/'export.json';r=json.loads(f.read_text())
r['variant']='SEPARATE_REGISTERED_ADMISSION_COMBINED_RESET_NOT_ADOPTED'
r['latency']='One additional control edge before SYS permit synchronization, including fault withdrawal'
root=exporter.resolve().parents[3]
for name in ('diagnostics/drtio/master_admission_registered.py','diagnostics/drtio/role-reversal/export-registered-admission-physical.py'):
 r['assembly_source_sha256'][name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
f.write_text(json.dumps(r,indent=2)+'\n')
print('REGISTERED_ADMISSION_EXPORT_PASS_NOT_DEPLOYED')
