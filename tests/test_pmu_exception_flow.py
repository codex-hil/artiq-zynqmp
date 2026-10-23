"""Conservative exception target decoding controls. SPDX-License-Identifier: LGPL-3.0-or-later"""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_pmu_exception_flow import audit
class Tests(unittest.TestCase):
 def test_extended_absolute_and_negative_relative_targets(self):
  text='''ffdc0008 <_vector_sw_exception>:
ffdc0008: b000ffdc imm -36
ffdc000c: b8080020 brai 32
ffdc0010 <helper>:
ffdc0010: b8000000 bri 0
ffdc0020 <_vector_hw_exception>:
ffdc0020: b9f4fff0 brlid r15, -16
ffdc0024: 98030000 bra r3
ffdc0028: e8610000 lwi r3, r1, 0
'''
  m=audit(text)
  self.assertEqual({e['target'] for e in m['direct_edges']},{'0xffdc0020','0xffdc0010'})
  self.assertEqual(len(m['unresolved_control']),1);self.assertEqual(len(m['memory_operations']),1)
  self.assertFalse(m['destructive_test_allowed'])
 def test_missing_vector_rejected(self):
  with self.assertRaises(ValueError):audit('')
if __name__=='__main__':unittest.main()
