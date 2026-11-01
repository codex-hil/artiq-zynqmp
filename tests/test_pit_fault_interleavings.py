# SPDX-License-Identifier: LGPL-3.0-or-later
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pit_fault_interleavings import analyze,apply
from pit_exception_receipt import decode
class Tests(unittest.TestCase):
 def test_single_and_nonreturning_nested_prefixes(self):
  r=analyze();self.assertEqual(r['events_per_writer'],19);self.assertEqual(len(r['single_prefixes']),20)
  self.assertTrue(all(x['result']=='rejected' for x in r['single_prefixes'][:-1]));self.assertEqual(r['single_prefixes'][-1]['result'],'a')
  self.assertEqual(r['nested_nonreturning_cases'],400)
  self.assertEqual(r['nested_nonreturning_counts'],{'rejected':379,'a':1,'b':20,'structurally_valid_mixed':0})
  self.assertFalse(r['first_fault_preserved']);self.assertFalse(r['reentry_excluded']);self.assertFalse(r['pmu_ram_access_allowed'])
 def test_forbidden_resume_counterexample_replays_and_decodes(self):
  r=analyze();self.assertEqual(r['forbidden_outer_resume_counts']['structurally_valid_mixed'],4)
  w=r['mixed_witness'];self.assertEqual(w['cut'],7);state=[0]*16
  for row in w['trace']:apply(state,(row['kind'],row['word'],row['value']))
  raw=struct.pack('<16I',*state);self.assertEqual(raw.hex(),w['final_hex']);self.assertNotIn(raw.hex(),[r['record_a_hex'],r['record_b_hex']])
  decoded=decode(raw);self.assertEqual(decoded['supplied_snapshots'],{'msr':0x201,'esr':0x102,'ear':0x103});self.assertFalse(decoded['session_bound'])
 def test_no_physical_claim_and_unknown_event_refusal(self):
  r=analyze();self.assertFalse(r['hardware_executed']);self.assertFalse(r['deployable']);self.assertFalse(r['session_bound'])
  with self.assertRaises(ValueError):apply([0]*16,('sleep',None,None))
