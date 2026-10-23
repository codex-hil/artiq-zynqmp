"""Actual guard ELF/disassembly binding controls, no HW; LGPL-3.0-or-later."""
import sys,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from pmu_guard_candidate import preflight
class Tests(unittest.TestCase):
 def test_actual_guard_and_stale_disassembly_pin(self):
  path=ROOT/'evidence/pmu-guard-boot-integration-2026-10-23/guard-inputs.json';preflight(path,ROOT)
  m=json.loads(path.read_text());m['disassembly']['sha256']='0'*64
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'bad.json';p.write_text(json.dumps(m))
   with self.assertRaises(ValueError):preflight(p,ROOT)
if __name__=='__main__':unittest.main()
