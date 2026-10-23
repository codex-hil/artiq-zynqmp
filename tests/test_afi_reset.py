"""AFI source audit controls; LGPL-3.0-or-later."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_afi_reset import audit,ANCHORS
class Tests(unittest.TestCase):
 def test_complete_and_changed_mask(self):
  with tempfile.TemporaryDirectory() as tmp:
   paths={n:Path(tmp)/n for n in ANCHORS}
   for n,p in paths.items():p.write_text('\n'.join(ANCHORS[n]))
   r=audit(paths);self.assertFalse(r['hardware_executed']);self.assertFalse(r['destructive_test_allowed'])
   p=paths['crf_apb.h'];p.write_text(p.read_text().replace('00000200','00000400'))
   with self.assertRaises(ValueError):audit(paths)
 def test_inventory(self):
  with self.assertRaises(ValueError):audit({})
if __name__=='__main__':unittest.main()
