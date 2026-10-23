"""Compiled mask interpretation and corruption controls; LGPL-3.0-or-later."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_pmu_irq_policy import review,mask
BUILD=Path('/home/codex-hil/.local/state/artiq-builds/fsbl-spd-dump-20261022')
class Tests(unittest.TestCase):
 def test_actual_objects_and_wrong_mask(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'out';r=review(BUILD,out)
   self.assertEqual(r['helpers']['microblaze_disable_interrupts']['cleared_msr_mask'],'0x2')
   self.assertEqual(r['helpers']['microblaze_disable_exceptions']['cleared_msr_mask'],'0x100')
   dis=(out/'microblaze_disable_interrupts.dis').read_text()
   self.assertEqual(mask(dis.replace('-3','-257'),'microblaze_disable_interrupts'),0x100)
   with self.assertRaises(ValueError):mask(dis.replace('mts','nop'),'microblaze_disable_interrupts')
   with self.assertRaises(ValueError):review(BUILD,out)
if __name__=='__main__':unittest.main()
