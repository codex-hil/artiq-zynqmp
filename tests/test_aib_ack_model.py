"""Protocol failure/hold controls, no hardware. LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/ddr'))
from aib_ack_model import AibModel
class Tests(unittest.TestCase):
 def model(self):
  m=AibModel(7);m.begin(7,1,0x30000,4,4,0,3);return m
 def test_partial_timeout_holds(self):
  m=self.model()
  for ack in [0,0x10000,0x20000]:r=m.observe(7,1,0x30004,ack,0)
  self.assertEqual(r['state'],'FAILED_HELD_MODEL');self.assertEqual(r['request_word'],'0x30004')
  with self.assertRaises(ValueError):m.release()
  with self.assertRaises(ValueError):m.observe(7,1,0x30004,0x30000,0)
 def test_ack_all_and_no_release(self):
  m=self.model();r=m.observe(7,1,0x30004,0x30004,0)
  self.assertEqual(r['state'],'DRAINED_HELD_MODEL');self.assertFalse(r['destructive_test_allowed'])
  with self.assertRaises(ValueError):m.release()
 def test_changed_epoch_request_type_and_malformed(self):
  for args in [(8,1,0x30004,0x30000,0),(7,2,0x30004,0x30000,0),(7,1,4,0x30000,0),(7,1,0x30004,0x30000,1),(7,1,0x30004,True,0)]:
   self.assertEqual(self.model().observe(*args)['state'],'FAILED_HELD_MODEL')
 def test_stale_or_unreviewed_entry_rejected(self):
  for mask,req,ack,budget in [(0,0,0,3),(0x4000000,0,0,3),(0x10000,0x10000,0,3),(0x10000,0,0x10000,3),(0x10000,0,0,0)]:
   with self.assertRaises(ValueError):AibModel(7).begin(7,1,mask,req,ack,0,budget)
if __name__=='__main__':unittest.main()
