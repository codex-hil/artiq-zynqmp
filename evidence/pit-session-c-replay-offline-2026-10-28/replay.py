# SPDX-License-Identifier: LGPL-3.0-or-later
"""Archived actual-C fake-transport replay; no hardware or C reexecution."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'diagnostics/ddr'))
from pit_session_correlation import Session
from pit_sleep_observation import ADDRESS
from pit_terminal_receipt import FORMAT
ARCHIVE=ROOT/'evidence/pit-ro-composition-offline-2026-10-28/fake-c-results.json'
IMAGE=hashlib.sha256(b'fake-c-trace-image').hexdigest()
def replay():
 archive=json.loads(ARCHIVE.read_text())
 assert archive['hardware_executed'] is False and archive['synthetic_callbacks'] is True
 results=[];controls=[];joined=b''
 for case in archive['results']:
  pair=bytes.fromhex(case['record_hex']);assert len(pair)==144;joined+=pair
  receipt=pair[48:];samples=pair[:48] if FORMAT.unpack(receipt)[3]==4 else None
  for when in ['no_reported_event','wake_before_terminal','debug_after_terminal']:
   s=Session(7,IMAGE);s.observe(dict(version=1,nonce=7,address=ADDRESS,return_code=0,value=0x10000))
   if when=='wake_before_terminal':s.event('wake')
   s.terminal(receipt,receipt,samples)
   if when=='debug_after_terminal':s.event('debug')
   r=s.observe(dict(version=1,nonce=7,address=ADDRESS,return_code=0,value=0x10000))
   assert r['terminal_status']==case['result']['status'] and r['terminal_content_bound']
   assert r['lifetime']['invalidated']==(when!='no_reported_event')
   assert not any(r[k] for k in ['sleep_proven','pmu_ram_access_allowed','hardware_executed','deployable','destructive_test_allowed'])
   results.append({'case':case['case'],'event_order':when,'result':r})
  for label in ['wrong_nonce','wrong_image','torn_snapshot','wrong_samples']:
   s=Session(8 if label=='wrong_nonce' else 7,'34'*32 if label=='wrong_image' else IMAGE)
   second=receipt[:-1] if label=='torn_snapshot' else receipt
   badsamples=bytes(48) if label=='wrong_samples' else samples
   try:s.terminal(receipt,second,badsamples)
   except ValueError:
    assert s.report()['lifetime']['invalidated'];controls.append({'case':case['case'],'mutation':label,'rejected':True})
   else:raise AssertionError((case['case'],label))
 assert hashlib.sha256(joined).hexdigest()==archive['output_sha256']
 return {'hardware_executed':False,'deployable':False,'synthetic_transport':True,'archived_actual_c_output':True,'archive_sha256':hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),'archived_output_sha256_verified':True,'cases':len(archive['results']),'correlated_traces':results,'negative_controls':controls,'limits':'Replay of archived actual-C output with fake callbacks. Added status/events are synthetic. No fresh C/target execution, authentic hardware origin, chronological proof or RAM admission.'}
if __name__=='__main__':print(json.dumps(replay(),indent=2))
