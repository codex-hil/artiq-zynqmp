"""Actual linked guard opt-in/control-flow checks; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_pmu_lab_guard import check
ON=Path('/home/codex-hil/.local/state/artiq-builds/pmu-sleep-guard-full-20261023')
OFF=Path('/home/codex-hil/.local/state/artiq-builds/pmu-sleep-guard-disabled-20261023')
class Tests(unittest.TestCase):
 def test_actual_guard_and_escape_rejection(self):
  elf=(ON/'pmufw.elf').read_bytes();symbols=(ON/'symbols.txt').read_text();dis=(ON/'disassembly.txt').read_text()
  self.assertFalse(check(elf,symbols,dis)['destructive_test_allowed'])
  for bad in [dis.replace('b800fffc','b8000004'),dis.replace('b9f48524','b9f48528'),dis.replace('ba020004','80000000'),dis.replace('ffdc4734:\tb8220004','ffdc4734:\t80000000'),dis.replace('// ffdc46c8','// 40000000')]:
   with self.assertRaises(ValueError):check(elf,symbols,bad)
 def test_default_firmware_has_no_guard_or_record(self):
  symbols=(OFF/'symbols.txt').read_text()
  self.assertNotIn('artiq_pmu_enter_lab_guard',symbols);self.assertNotIn('artiq_pmu_guard',symbols)
if __name__=='__main__':unittest.main()
