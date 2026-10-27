"""Directional isolation mapping and header drift controls. LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from decode_aib_instances import decode,verify_header
HEADER=Path('/home/codex-hil/.local/state/artiq-builds/pmu-sleep-guard-full-20261023/src/lpd_slcr.h')
class Tests(unittest.TestCase):
 def test_retained_usb_slave_capture(self):
  verify_header(HEADER.read_text());m=decode(0xc00000,0xc00000,0x19cf000f)
  selected=[r for r in m['instances'] if r['request']]
  self.assertEqual([(r['master'],r['slave']) for r in selected],[('LPD','USB0'),('LPD','USB1')])
  self.assertTrue(all(r['ack'] for r in selected));self.assertFalse(m['destructive_test_allowed'])
 def test_unknowns_drift_and_invalid(self):
  self.assertEqual(decode(1<<31,0,0)['unknown_bits']['request'],'0x80000000')
  with self.assertRaises(ValueError):verify_header(HEADER.read_text().replace('0X00400000U','0X00200000U'))
  for v in [-1,1<<32,True]:
   with self.assertRaises(ValueError):decode(v,0,0)
if __name__=='__main__':unittest.main()
