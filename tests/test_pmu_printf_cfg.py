"""Actual linked CFG and bypass controls. SPDX-License-Identifier: LGPL-3.0-or-later"""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_pmu_printf_cfg import audit,verify_text,table_check
B=Path('/home/codex-hil/.local/state/artiq-builds/pmu-sleep-guard-full-20261023')
class Tests(unittest.TestCase):
 def test_actual_and_structural_bypass(self):
  text=(B/'disassembly.txt').read_text();elf=(B/'pmufw.elf').read_bytes();table=table_check(elf)
  verify_text(text,elf);self.assertFalse(audit(text,table)['destructive_test_allowed'])
  # Mutate complete first instruction row to a direct bypass into the load.
  import re
  bad=re.sub(r'ffdcc810:\s+[0-9a-f]{8}\s+[^\n]+','ffdcc810: b80001d8 bri 472 // ffdcc9e8',text)
  with self.assertRaises(ValueError):audit(bad,table)
  with self.assertRaises(ValueError):verify_text(bad,elf)
 def test_unknown_indirect_target_rejected(self):
  text=(B/'disassembly.txt').read_text().replace('ffdcc9ec:', 'ffdcc9e8:')
  with self.assertRaises(ValueError):audit(text,table_check((B/'pmufw.elf').read_bytes()))
if __name__=='__main__':unittest.main()
