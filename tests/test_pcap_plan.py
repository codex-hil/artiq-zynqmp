"""PCAP field/bounds controls; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from plan_pcap_snapshot import decode
class Tests(unittest.TestCase):
 def test_read_write_idle_are_distinct(self):
  self.assertTrue(decode([3,3])['sampled_read_write_idle'])
  self.assertFalse(decode([1,1])['sampled_read_write_idle'])
  self.assertFalse(decode([2,2])['sampled_read_write_idle'])
  r=decode([0x8000000f]*2)
  self.assertEqual(r['other_status_bits'],[0x80000000]*2)
  self.assertTrue(r['fields']['pl_done'][0]);self.assertFalse(r['destructive_test_allowed'])
 def test_invalid_and_unstable(self):
  self.assertFalse(decode([3,1])['stable'])
  for bad in [[],[3],[3,True],[3,-1],[3,1<<32]]:
   with self.assertRaises(ValueError):decode(bad)
if __name__=='__main__':unittest.main()
