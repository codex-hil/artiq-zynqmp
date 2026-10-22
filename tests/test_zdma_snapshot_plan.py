"""Register allowlist and non-admission controls; LGPL-3.0-or-later."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from plan_zdma_snapshot import BASES,OFFSETS,plan,decode

PARAMETERS='#define XPAR_XZDMA_NUM_INSTANCES 16\n'+''.join(f'#define XPAR_XZDMA_{i}_BASEADDR {hex(b)}\n' for i,b in enumerate(BASES))
HEADER='\n'.join(f'#define {n} ({hex(v)}U)' for n,v in [('XZDMA_CH_STS_OFFSET',0x11c),('XZDMA_CH_CTRL2_OFFSET',0x200),('XZDMA_STS_ALL_MASK',3),('XZDMA_CH_CTRL2_EN_MASK',1)])


class SnapshotTests(unittest.TestCase):
 def test_exact_read_set(self):
  r=plan(PARAMETERS,HEADER);self.assertEqual(len(r['registers']),32)
  for row in r['registers']:
   self.assertIn(int(row['address'],16)-BASES[row['channel']],(0x11c,0x200))
  self.assertFalse(r['destructive_test_allowed'])
 def test_source_drift_rejected(self):
  for p,h in [(PARAMETERS.replace('16\n','8\n',1),HEADER),(PARAMETERS,HEADER.replace('0x11c','0x100')),(PARAMETERS+PARAMETERS,HEADER)]:
   with self.assertRaises(ValueError):plan(p,h)
 def test_busy_paused_error_enabled_and_drift_not_quiet(self):
  zero={b+o:0 for b in BASES for o in OFFSETS.values()}
  r=decode([zero,dict(zero)]);self.assertTrue(r['all_quiet_fields']);self.assertFalse(r['destructive_test_allowed'])
  for offset,value in [(0x11c,1),(0x11c,2),(0x11c,3),(0x200,1),(0x200,2)]:
   changed=dict(zero);changed[BASES[0]+offset]=value
   self.assertFalse(decode([zero,changed])['all_quiet_fields'])
 def test_incomplete_or_invalid_capture_rejected(self):
  zero={b+o:0 for b in BASES for o in OFFSETS.values()}
  bad=dict(zero);bad.pop(next(iter(bad)))
  for samples in [[zero],[zero,bad],[zero,{**zero,BASES[0]+0x11c:True}]]:
   with self.assertRaises(ValueError):decode(samples)


if __name__=='__main__':unittest.main()
