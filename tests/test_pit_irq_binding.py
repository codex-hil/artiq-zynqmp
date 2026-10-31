# SPDX-License-Identifier: LGPL-3.0-or-later
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_target_binding_guards_with_explicit_host_doubles(self):
  base=ROOT/'diagnostics/ddr/pit_collect'
  with tempfile.TemporaryDirectory() as td:
   for flags in [['-O2'],['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']]:
    exe=Path(td)/'binding'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',*flags,'-D__MICROBLAZE__','-DARTIQ_PIT_TERMINAL_AUDIT_ONLY','-DARTIQ_PIT_MMIO_AUDIT_ONLY','-DARTIQ_PIT_IRQ_AUDIT_ONLY','-I'+str(base),str(base/'pit_irq_composition_audit.c'),str(ROOT/'tests/fixtures/pit_irq_binding_host.c'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=5)
if __name__=='__main__':unittest.main()
