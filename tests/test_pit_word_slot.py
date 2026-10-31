# SPDX-License-Identifier: LGPL-3.0-or-later
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def exercise(self,mode):
  base=ROOT/'diagnostics/ddr/pit_collect'
  with tempfile.TemporaryDirectory() as td:
   for flags in [['-O2'],['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']]:
    exe=Path(td)/'slot'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',*flags,'-I'+str(base),*[str(base/(n+'.c')) for n in ['pit_word_slot','pit_publish','pit_terminal_record']],str(ROOT/'tests/fixtures/pit_word_slot_host.c'),'-o',str(exe)],check=True)
    subprocess.run([str(exe),str(mode)],check=True,timeout=5)
 def test_actual_publishers_word_slots_and_fence_reentry(self):self.exercise(0)
 def test_all_42_steps_and_four_fence_failures_preserve_uncommitted_state(self):self.exercise(1)
 def test_invalid_preparation_offsets_and_order(self):self.exercise(2)
if __name__=='__main__':unittest.main()
