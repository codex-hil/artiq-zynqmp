"""Offline quiescence protocol transition controls; LGPL-3.0-or-later."""
import sys,unittest,itertools
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/ddr'))
from pmu_quiesce_model import Model,REQUIRED,match_receipt
class Tests(unittest.TestCase):
 def test_every_missing_condition_blocks_ack(self):
  names=sorted(REQUIRED)
  for values in itertools.product([False,True],repeat=len(names)):
   m=Model(123);m.request(123,7,10);r=m.observe(dict(zip(names,values)),11,20)
   self.assertEqual(r['state']=='PARKED_MODEL',all(values));self.assertFalse(r['destructive_test_allowed'])
 def test_stale_epoch_and_sequence_not_accepted(self):
  m=Model(123);m.request(123,7,10);r=m.observe(dict.fromkeys(REQUIRED,True),11,20)
  self.assertTrue(match_receipt(r,123,7));self.assertFalse(match_receipt(r,124,7));self.assertFalse(match_receipt(r,123,8))
  with self.assertRaises(ValueError):m.request(123,8,12)
 def test_timeout_before_ack_is_rejection_after_ack_never_resumes(self):
  m=Model(1);m.request(1,1,10);self.assertEqual(m.observe(dict.fromkeys(REQUIRED,True),30,20)['state'],'REJECTED')
  m=Model(1);m.request(1,1,10);m.observe(dict.fromkeys(REQUIRED,True),11,20)
  self.assertEqual(m.timeout_after_ack()['state'],'PARKED_MODEL')
  with self.assertRaises(ValueError):m.resume()
 def test_bad_fields_and_clock_reject(self):
  for claims,now in [({},11),(dict.fromkeys(REQUIRED,1),11),(dict.fromkeys(REQUIRED,True),9)]:
   m=Model(1);m.request(1,1,10);self.assertEqual(m.observe(claims,now,20)['state'],'REJECTED')
if __name__=='__main__':unittest.main()
