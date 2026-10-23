"""Actual linked PMU ELF layout controls; LGPL-3.0-or-later."""
import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_pmu_boundary_image import check
BUILD=Path('/home/codex-hil/.local/state/artiq-builds/pmu-boundary-full-20261023')
class Tests(unittest.TestCase):
 def test_actual_image_and_corrupt_record(self):
  data=(BUILD/'pmufw.elf').read_bytes();text=(BUILD/'symbols.txt').read_text();r=check(data,text)
  self.assertEqual(r['telemetry']['bytes'],32);self.assertFalse(r['destructive_test_allowed'])
  with self.assertRaises(ValueError):check(data,text.replace('00000020 b artiq_pmu_boundary','00000040 b artiq_pmu_boundary'))
 def test_ddr_segment_rejected(self):
  data=bytearray((BUILD/'pmufw.elf').read_bytes());phoff=struct.unpack_from('<I',data,28)[0]
  struct.pack_into('<I',data,phoff+12,0x40000000)
  with self.assertRaises(ValueError):check(bytes(data),(BUILD/'symbols.txt').read_text())
if __name__=='__main__':unittest.main()
