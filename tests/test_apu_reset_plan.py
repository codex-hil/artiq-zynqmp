"""APU raw-control decoder rejection tests; LGPL-3.0-or-later."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from plan_apu_reset_snapshot import decode

class ApuTests(unittest.TestCase):
 def test_reset_and_por_separate_never_admit(self):
  r=decode([0x804,0x804]);self.assertTrue(r['stable'])
  self.assertTrue(r['cores'][2]['reset_control_bits'][0])
  self.assertFalse(r['cores'][2]['power_on_reset_control_bits'][0])
  self.assertTrue(r['cores'][1]['power_on_reset_control_bits'][0])
  self.assertFalse(r['destructive_test_allowed'])
 def test_changes_unknown_missing_invalid(self):
  self.assertFalse(decode([0,2])['stable'])
  self.assertEqual(decode([0x80000000]*2)['unknown_bits'],[0x80000000]*2)
  for bad in [[],[0],[0,True],[0,-1],[0,1<<32]]:
   with self.assertRaises(ValueError):decode(bad)

if __name__=='__main__':unittest.main()
