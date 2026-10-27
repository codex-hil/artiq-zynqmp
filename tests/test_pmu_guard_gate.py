"""Actual guard ELF/disassembly binding controls, no HW; LGPL-3.0-or-later."""
import sys,json,tempfile,unittest,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from pmu_guard_candidate import preflight,check_vector_read
class Tests(unittest.TestCase):
 def test_rebound_vector_profile_is_explicitly_refused(self):
  m=json.loads((ROOT/'evidence/guard-context-recovery-plan-2026-10-27/guard-inputs.json').read_text())
  m['script_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in m['script_sha256']}
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'m.json';p.write_text(json.dumps(m))
   with self.assertRaisesRegex(ValueError,'write-only'):preflight(p,ROOT)
 def test_vector_read_mutations(self):
  text=Path('/home/codex-hil/.local/state/artiq-builds/pmu-vector-snapshot-full-20261024/disassembly.txt').read_text()
  self.assertEqual(check_vector_read(text)['address'],'0xffd40010')
  for old,new in [('b000ffd4','b000ffdc'),('e8800010','e8800014'),('f8830030','f8830034'),('30800001','30800002')]:
   with self.assertRaises(ValueError):check_vector_read(text.replace(old,new))
 def test_historical_guard_rejected(self):
  with self.assertRaises(ValueError):
   preflight(ROOT/'evidence/pmu-guard-boot-integration-2026-10-23/guard-inputs.json',ROOT)
 def test_actual_guard_and_stale_disassembly_pin(self):
  path=ROOT/'evidence/guard-context-recovery-plan-2026-10-27/guard-inputs.json'
  with self.assertRaises(ValueError):preflight(path,ROOT)
  m=json.loads(path.read_text());m['disassembly']['sha256']='0'*64
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'bad.json';p.write_text(json.dumps(m))
   with self.assertRaises(ValueError):preflight(p,ROOT)
if __name__=='__main__':unittest.main()
