"""PMU event observation controls; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from plan_pmu_events_snapshot import decode,REGISTERS
class Tests(unittest.TestCase):
 def test_mask_signal_and_no_admission(self):
  z=dict.fromkeys(REGISTERS,0);s=dict(z,gpi1=0x25,gpi1_enable=0x24)
  r=decode([s,s]);self.assertEqual(r['processor_wake_signal_and_enable'],[0x24]*2)
  self.assertFalse(r['destructive_test_allowed']);self.assertFalse(decode([z,z])['destructive_test_allowed'])
 def test_incomplete_invalid_changes(self):
  z=dict.fromkeys(REGISTERS,0)
  self.assertFalse(decode([z,dict(z,irq_pending=1)])['stable'])
  for bad in [[z],[z,{}],[z,dict(z,gpi1=True)],[z,dict(z,gpi1=-1)]]:
   with self.assertRaises(ValueError):decode(bad)
if __name__=='__main__':unittest.main()
