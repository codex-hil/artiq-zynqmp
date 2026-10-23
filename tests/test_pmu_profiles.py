"""Target-preprocessor option review, no hardware; LGPL-3.0-or-later."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_pmu_profiles import review
BUILD=Path('/home/codex-hil/.local/state/artiq-builds/fsbl-spd-dump-20261022')
class Tests(unittest.TestCase):
 def test_actual_headers_and_profiles(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'review';r=review(BUILD,out);p=r['profiles']
   self.assertIn('ENABLE_PM',p['baseline']['enabled_service_macros'])
   self.assertNotIn('ENABLE_PM',p['pm_disabled']['enabled_service_macros'])
   self.assertIn('ENABLE_FPGA_LOAD',p['pm_disabled']['enabled_service_macros'])
   for name in ['ENABLE_PM','ENABLE_SCHEDULER','ENABLE_FPGA_LOAD','ENABLE_SECURE']:
    self.assertNotIn(name,p['service_reduced']['enabled_service_macros'])
   self.assertFalse(r['hardware_executed']);self.assertFalse(r['destructive_test_allowed'])
   with self.assertRaises(ValueError):review(BUILD,out)
if __name__=='__main__':unittest.main()
