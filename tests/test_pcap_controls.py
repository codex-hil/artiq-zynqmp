"""PCAP reset/mode/status independence controls; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from plan_pcap_controls import decode
class Tests(unittest.TestCase):
 def test_reset_and_idle_are_independent_no_admission(self):
  s=dict(status=0xa0000a46,reset=1,control=0,direction=0)
  r=decode([s,s]);self.assertTrue(r['stable']);self.assertEqual(r['reset_control_bits'],[True,True])
  self.assertFalse(r['status_fields']['sampled_read_write_idle'])
  self.assertFalse(r['destructive_test_allowed'])
  s['reset']=0;r=decode([s,s]);self.assertEqual(r['reset_control_bits'],[False,False])
  self.assertFalse(r['destructive_test_allowed'])
 def test_missing_invalid_unstable(self):
  s=dict(status=3,reset=0,control=1,direction=1)
  self.assertFalse(decode([s,dict(s,reset=1)])['stable'])
  for bad in [[s],[s,{}],[s,dict(s,reset=True)],[s,dict(s,control=-1)]]:
   with self.assertRaises(ValueError):decode(bad)
if __name__=='__main__':unittest.main()
