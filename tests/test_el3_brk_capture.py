"""Exact BRK class and mandatory restoration controls; LGPL-3.0-or-later."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_el3_brk_capture import verify
from test_exception_observer_integration import IntegrationTests
from test_candidate_runtime_hw import lifecycle


class BrkTests(unittest.TestCase):
 def log(self):return IntegrationTests('test_full_normal_dispatch').output(True,True)
 def test_tcl_dispatch_and_exact_fault(self):
  text=self.log();self.assertNotIn('ERROR',text)
  r=verify(text);self.assertEqual(r['status'],'EXPECTED_BRK_CAPTURE_RESTORE_REQUIRED')
  self.assertFalse(r['normal_observation_pass']);self.assertFalse(r['hardware_executed'])
 def test_each_wrong_fault_field_rejects(self):
  text=self.log()
  for key,expected in [('x14',4),('x15',243),('x16',12),('x17',0xf2000053),('x19',0xfffc884c),('x20',0x600002cd)]:
   with self.subTest(key=key):
    wrong=text.replace(f'EXCEPTION_REGISTER {key} {expected}',f'EXCEPTION_REGISTER {key} 0')
    with self.assertRaises(ValueError):verify(wrong)
 def test_normal_duplicate_and_incomplete_reject(self):
  text=self.log()
  for wrong in [text+text,text.replace('EXPECTED_BRK_TRANSPORT_CAPTURED',''),text+'EXCEPTION_OBSERVER_NORMAL_COMPLETE\n',text.replace('EXCEPTION_REGISTER x18 0','EXCEPTION_REGISTER x18 -1')]:
   with self.assertRaises(ValueError):verify(wrong)
  # FAR is intentionally not asserted valid for BRK.
  self.assertEqual(verify(text.replace('EXCEPTION_REGISTER x18 0','EXCEPTION_REGISTER x18 123'))['registers']['x18'],123)
 def test_expected_fault_never_waives_restore(self):
  text=self.log();calls=[]
  def cycle(role):
   calls.append(role)
   if role=='candidate':verify(text);return 'expected-brk'
   raise RuntimeError('restore failed')
  r=lifecycle(cycle)
  self.assertEqual(calls,['candidate','restore']);self.assertEqual(r['status'],'FAIL');self.assertEqual(r['restoration'],'FAIL')


if __name__=='__main__':unittest.main()
