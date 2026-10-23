"""CSU fields and fixed non-mutating Tcl controls; LGPL-3.0-or-later."""
import subprocess
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from plan_csu_dma_snapshot import ADDRESSES,decode
from capture_csu_core_state import parse,CORES
ROOT=Path(__file__).resolve().parents[1]


class CsuTests(unittest.TestCase):
 def test_fields_without_ack_or_error_claim(self):
  zero=dict.fromkeys(ADDRESSES,0)
  r=decode([zero,zero]);self.assertTrue(r['all_quiet_fields']);self.assertFalse(r['destructive_test_allowed'])
  for value in [1,2,32,0x10000]:
   s=dict.fromkeys(ADDRESSES,value)
   self.assertFalse(decode([s,s])['all_quiet_fields'])
  done=dict.fromkeys(ADDRESSES,0xe000)
  self.assertTrue(decode([done,done])['all_quiet_fields'])
  self.assertEqual(decode([done,done])['channels'][0]['unacknowledged_done'],[7,7])
 def test_changes_missing_and_invalid_reject(self):
  z=dict.fromkeys(ADDRESSES,0)
  self.assertFalse(decode([z,dict.fromkeys(ADDRESSES,0x2000)])['all_quiet_fields'])
  for samples in [[z],[z,{}],[z,dict.fromkeys(ADDRESSES,True)]]:
   with self.assertRaises(ValueError):decode(samples)
 def test_strict_frame_and_unknown_core_state(self):
  text='CSU_BEGIN\n'+''.join(f'CSU {s} 0x{a:08x} 0x00000000\n' for s in range(2) for a in ADDRESSES)+'CSU_END\n'+''.join(f'CORE_METADATA {n} MISSING_NOT_PROVEN\n' for n in CORES)
  r=parse(text);self.assertTrue(r['csu']['all_quiet_fields'])
  self.assertTrue(all(c['ownership']=='NOT_PROVEN' for c in r['cores']))
  for wrong in [text+text,text.replace('CSU_END',''),text.replace('0xffc80008','0xffc80014'),text.replace('CORE_METADATA Cortex-R5 #1 MISSING_NOT_PROVEN\n','')]:
   with self.assertRaises(ValueError):parse(wrong)
 def test_real_tcl_uses_only_four_status_reads(self):
  mock='''
set argv {server 210383B7F02DA}
set reads 0
proc connect {args} {}
proc disconnect {} {}
proc after {args} {}
proc targets {args} {
 if {[lindex $args 0] eq "-set"} {return}
 if {[lindex $args end] eq {name == "PSU"}} {return [list [dict create jtag_cable_serial 210383B7F02DA target_id 1]]}
 return {}
}
proc mrd {args} {
 global reads
 if {[lrange $args 0 2] ne {-address-space AP0 -value} || [lindex $args 3] ni {0xffc80008 0xffc80808}} {error unsafe-read}
 incr reads
 return 0
}
'''+f'source {{{ROOT/"scripts/probe_csu_core_state.tcl"}}}\nif {{$reads != 4}} {{error count}}\n'
  p=subprocess.run(['tclsh'],input=mock,text=True,capture_output=True,timeout=5)
  self.assertEqual(p.returncode,0);self.assertFalse(p.stderr,p.stderr)
  self.assertEqual(p.stdout.count('MISSING_NOT_PROVEN'),6)
  self.assertTrue(parse(p.stdout)['csu']['all_quiet_fields'])


if __name__=='__main__':unittest.main()
