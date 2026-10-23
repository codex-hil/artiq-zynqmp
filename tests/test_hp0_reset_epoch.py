"""Source audit controls; LGPL-3.0-or-later."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_hp0_reset_epoch import audit,ANCHORS
class Tests(unittest.TestCase):
 def test_complete_and_missing_anchor(self):
  with tempfile.TemporaryDirectory() as tmp:
   paths={n:Path(tmp)/n for n in ANCHORS}
   for n,p in paths.items():p.write_text('\n'.join(ANCHORS[n]))
   r=audit(paths);self.assertFalse(r['destructive_test_allowed']);self.assertFalse(r['hardware_executed'])
   paths['top.v'].write_text('\n'.join(ANCHORS['top.v'][1:]))
   with self.assertRaises(ValueError):audit(paths)
 def test_inventory(self):
  with self.assertRaises(ValueError):audit({})
if __name__=='__main__':unittest.main()
