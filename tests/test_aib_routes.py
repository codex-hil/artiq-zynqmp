"""AIB audit failure controls; LGPL-3.0-or-later."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_aib_routes import audit,ANCHORS
class Tests(unittest.TestCase):
 def test_scope_and_changed_route(self):
  with tempfile.TemporaryDirectory() as tmp:
   paths={n:Path(tmp)/n for n in ANCHORS}
   for n,p in paths.items():p.write_text('\n'.join(ANCHORS[n]))
   r=audit(paths);self.assertFalse(r['destructive_test_allowed']);self.assertEqual(len(r['rejected_shortcuts']),3)
   p=paths['xpfw_aib.h'];p.write_text(p.read_text().replace('FPD_TO_AFI_FS0','PL_TO_AFI_FM2'))
   with self.assertRaises(ValueError):audit(paths)
 def test_inventory(self):
  with self.assertRaises(ValueError):audit({})
if __name__=='__main__':unittest.main()
