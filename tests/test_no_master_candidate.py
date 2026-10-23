"""No-master image pin/PL-DONE controls; LGPL-3.0-or-later."""
import sys,json,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from no_master_candidate import preflight,verify_configuration
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_configuration_is_not_admission(self):
  c={'stable':True,'status_fields':{'fields':{'pl_done':[True,True]}}};w={'observations':{'pcap_context':c}}
  self.assertFalse(verify_configuration(w)['destructive_test_allowed'])
  c['status_fields']['fields']['pl_done']=[True,False]
  with self.assertRaises(ValueError):verify_configuration(w)
 def test_actual_build_and_stale_pin(self):
  path=ROOT/'evidence/no-master-boot-integration-2026-10-23/pl-inputs.json'
  preflight(path,ROOT)
  m=json.loads(path.read_text());m['bitstream']['sha256']='0'*64
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'bad.json';p.write_text(json.dumps(m))
   with self.assertRaises(ValueError):preflight(p,ROOT)
if __name__=='__main__':unittest.main()
