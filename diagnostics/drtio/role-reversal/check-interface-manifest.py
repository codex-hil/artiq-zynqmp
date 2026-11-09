#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Offline candidate consistency only. Never grants deployment/MMIO permission."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
CONTRACT={
 'schema':1,'profile':'genesys-reversed-roles-shape-guard-offline-v1',
 'scope':'TEST_FIXTURE_ONLY_NOT_DEPLOYED','deployment_admissible':False,
 'management':{'base':0xb0000000,'identity':0x47524d31,'identity_discovers_optional_capability':False,
  'registers':{'identity':0,'command':4,'reset_status':8,'shape_fault_ro_bit0':12},
  'optional_shape_fault_present_in_fixture':True,'runtime_capability_granted':False},
 'target':{'data_bits':32,'address_bits':40,'id_bits':16,'len':0,'size':2,
  'alignment_bytes':4,'lock':0,'bursts':[0,1],'wlast':1,'max_reads':1,'max_writes':1,
  'malformed_handling':'READY0_STICKY_FAULT_NO_AXI_ERROR_RESPONSE'},
 'reset':{'requester_abandoned_required':True,'requester_withdrawn_required':True,
  'bridge_target_coordinated_reset_required':True,'automatic_retry':False,
  'same_hung_cpu_recovery_qualified':False},
 'hardware':{'accessed':False,'physical_cdc_qualified':False,'maintenance_hold':True,
  'deployed_bitstream_sha256':None,'deployed_firmware_sha256':None}}
SOURCES=('diagnostics/drtio/aux_reset_management.py','diagnostics/drtio/master_dual_ingress.py',
 'diagnostics/drtio/master_axi_drain.py','diagnostics/drtio/master_axi_shape_guard.py',
 'diagnostics/drtio/master_rx_progress.py','diagnostics/drtio/test_master_full_shape_fault.py',
 'diagnostics/drtio/role-reversal/a53/reset_driver.h',
 'diagnostics/drtio/role-reversal/a53/shape_recovery.h')
def validate(m):
 if set(m)!={'contract','source_sha256'} or m['contract']!=CONTRACT:
  raise ValueError('Candidate contract mismatch; no deployment capability can be granted')
 if set(m['source_sha256'])!=set(SOURCES):raise ValueError('Source binding set mismatch')
 for name in SOURCES:
  if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=m['source_sha256'][name]:
   raise ValueError('Source changed: '+name)
 return {'status':'OFFLINE_CANDIDATE_CONSISTENCY_PASS','deployment_admissible':False,
         'runtime_capability_granted':False,'source_bindings':len(SOURCES)}
if __name__=='__main__':
 try:print(json.dumps(validate(json.loads(Path(sys.argv[1]).read_text())),sort_keys=True))
 except (ValueError,KeyError,IndexError,OSError) as error:
  print('MANIFEST_REFUSED: '+str(error),file=sys.stderr);sys.exit(1)
