# SPDX-License-Identifier: LGPL-3.0-or-later
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_fake_process_memory_and_adapter_budget(self):
  base=ROOT/'diagnostics/ddr/pit_collect'
  with tempfile.TemporaryDirectory() as td:
   exe=Path(td)/'fake'
   subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-D__MICROBLAZE__','-DARTIQ_PIT_MMIO_AUDIT_ONLY','-I'+str(base),str(base/'pit_mmio_read.c'),str(base/'pit_ro_adapter.c'),str(ROOT/'tests/fixtures/pit_mmio_read_host.c'),'-o',str(exe)],check=True)
   subprocess.run([str(exe)],check=True,timeout=5)
 def test_target_and_audit_optin_required(self):
  base=ROOT/'diagnostics/ddr/pit_collect'
  with tempfile.TemporaryDirectory() as td:
   for flags in [[],['-D__MICROBLAZE__'],['-DARTIQ_PIT_MMIO_AUDIT_ONLY']]:
    z=subprocess.run(['gcc','-c',*flags,str(base/'pit_mmio_read.c'),'-o',str(Path(td)/'bad.o')],capture_output=True,text=True)
    self.assertNotEqual(z.returncode,0);self.assertIn('explicit MicroBlaze audit-only',z.stderr)
if __name__=='__main__':unittest.main()
