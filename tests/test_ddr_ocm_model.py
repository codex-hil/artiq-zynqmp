"""OCM model image/layout and host execution, no HW; LGPL-3.0-or-later."""
import ctypes,json,sys,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_ocm_image import check
class Tests(unittest.TestCase):
 def test_real_image_layout_and_bad_stack(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'image'
   subprocess.run(['bash',str(ROOT/'scripts/build_ddr_ocm_model.sh'),str(out)],check=True,capture_output=True)
   elf=(out/'model.elf').read_bytes();symbols=(out/'symbols.txt').read_text()
   r=check(elf,symbols);self.assertFalse(r['destructive_ddr_test_allowed'])
   undefined=subprocess.check_output(['nm','-u',str(out/'model.elf')],text=True)
   self.assertEqual(undefined,'')
   self.assertIn('model_exception',symbols);self.assertIn('model_report',symbols)
   with self.assertRaises(ValueError):check(elf,symbols.replace('00000000fffe4000','0000000080000000'))
 def test_ocm_callback_model_on_host(self):
  with tempfile.TemporaryDirectory() as tmp:
   lib=Path(tmp)/'model.so';src=ROOT/'diagnostics/ddr/bounded_test'
   subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fPIC','-shared',str(src/'pattern.c'),str(src/'ocm_model.c'),'-o',str(lib)],check=True)
   loaded=ctypes.CDLL(str(lib));self.assertEqual(loaded.ocm_model_main(),0)
   self.assertEqual(ctypes.c_uint32.in_dll(loaded,'model_result').value,0)
if __name__=='__main__':unittest.main()
