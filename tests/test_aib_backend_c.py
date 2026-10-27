"""Policy adapter plus actual C session/protocol, mocked MMIO only. LGPL-3.0-or-later."""
import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_optimized_and_sanitized(self):
  with tempfile.TemporaryDirectory() as t:
   for flags in [['-O2'],['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']]:
    exe=Path(t)/'backend';base=ROOT/'diagnostics/ddr/aib_strict'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',*flags,'-I'+str(base),*[str(base/(n+'.c')) for n in ['aib_strict','aib_session','aib_backend']],str(ROOT/'tests/fixtures/aib_backend_host.c'),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=5)
if __name__=='__main__':unittest.main()
