"""Offline exact plan and failure-stop qualification. LGPL-3.0-or-later."""
import contextlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import qualify_pmu_restore_hw as q
MARKERS=['STOP_REQUEST','HALT_CONFIRMED','REGISTER_READ_PASS','DOWNLOAD_START','DOWNLOAD_COMPLETE','RESUME_COMPLETE']
TEXT='\n'.join('PMU_RESTORE_STAGE '+x for x in MARKERS)+'\nPMU_RESTORE_BOOTSTRAP_STARTED\n'
class Tests(unittest.TestCase):
 def test_plan_scope_and_mutation(self):
  m=q.plan(q.REPO/'evidence/trained-observer-integration-2026-10-22/runtime-inputs.json');q.validate(m)
  for k,v in [('guard',True),('retries',1),('aib_writes',True)]:
   bad=dict(m);bad[k]=v
   with self.assertRaises(ValueError):q.validate(bad)
  m['script_sha256']['scripts/restart_pmu_for_restore.tcl']='0'*64
  with self.assertRaises(ValueError):q.validate(m)
 def test_marker_order_completeness(self):
  self.assertTrue(q.bootstrap(lambda *a:TEXT,['fake']))
  for text in [TEXT.replace('PMU_RESTORE_STAGE REGISTER_READ_PASS\n',''),TEXT+TEXT,'\n'.join(reversed(TEXT.splitlines()))]:
   with self.assertRaises(ValueError):q.bootstrap(lambda *a:text,['fake'])
 def test_failed_download_no_load_or_retry(self):
  @contextlib.contextmanager
  def lease():
   class FD:
    def fileno(self):return 123
   yield FD()
  class Reserve:
   def __init__(self,*a):pass
   def __enter__(self):return self
   def __exit__(self,*a):pass
  with tempfile.TemporaryDirectory() as tmp:
   m=Path(tmp)/'m.json';m.write_text('{}');out=Path(tmp)/'run'
   args=['q','--execute','--manifest',str(m),'--output',str(out),'--server','fake','--port','fake','--interface','fake']
   with patch.object(sys,'argv',args),patch.object(q,'validate',return_value={'restore_pmu':{'path':'fake'}}),patch.object(q,'lease',lease),patch.object(q,'RestoreReserve',Reserve),patch.object(q,'require_runtime_space'),patch.object(q,'bounded',return_value=(1,'register read error')) as run:
    self.assertEqual(q.main(),1);self.assertEqual(run.call_count,1)
   r=json.loads((out/'results.json').read_text());self.assertEqual(r['stages'],{'pmu-bootstrap':1});self.assertFalse(r['normal_runtime_verified'])
if __name__=='__main__':unittest.main()
