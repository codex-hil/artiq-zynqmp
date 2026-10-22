"""PSTATE field controls, no hardware; LGPL-3.0-or-later."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from decode_a64_debug_pstate import decode


class PstateTests(unittest.TestCase):
 def test_all_mode_encodings(self):
  valid={0,4,5,8,9,12,13}
  for mode in range(32):
   if mode in valid:self.assertEqual(decode(mode)['currentel_encoding'],mode&12)
   else:
    with self.assertRaises(ValueError):decode(mode)
 def test_masks_independent_of_flags(self):
  for bits in range(16):
   r=decode(0xf000000d|(bits<<6))
   self.assertEqual(r['required_observer_masks_present'],bits==15)
   for name,bit in [('D',3),('A',2),('I',1),('F',0)]:self.assertEqual(r['masked'][name],bool(bits & (1<<bit)))
 def test_captured_pstate_not_admitted(self):
  r=decode(0x600002cd)
  self.assertEqual(r['mode'],'EL3h');self.assertFalse(r['masked']['A'])
  self.assertFalse(r['required_observer_masks_present']);self.assertFalse(r['destructive_test_allowed'])
  for value in [True,-1,1<<32,'0']:
   with self.assertRaises(ValueError):decode(value)


if __name__=='__main__':unittest.main()
