"""Real Tcl external PMU RAM allowlist controls, no HW; LGPL-3.0-or-later."""
import sys,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from test_pmu_ram_access import parse
class Tests(unittest.TestCase):
 def test_real_tcl_two_ram_reads(self):
  t='''set argv {server 210383B7F02DA}
proc connect {args} {}
proc disconnect {} {}
proc after {args} {}
proc targets {args} {
 if {[lindex $args 0] eq "-set"} {return}
 return [list [dict create jtag_cable_serial 210383B7F02DA target_id 1]]
}
set reads 0
proc mrd {args} {
 global reads
 if {$args ne {-address-space AP0 -value 0xffdc0050}} {error wrong-read}
 incr reads;return 0x12345678
}
'''
  t+='source {'+str(ROOT/'scripts/probe_pmu_ram_access.tcl')+'}\nif {$reads != 2} {error count}\n'
  r=subprocess.run(['tclsh'],input=t,text=True,capture_output=True,timeout=5)
  self.assertEqual(r.returncode,0);self.assertFalse(r.stderr,r.stderr)
  self.assertFalse(parse(r.stdout,0x12345678)['destructive_test_allowed'])
  for bad in [r.stdout+r.stdout,r.stdout.replace('PMU_RAM_END',''),r.stdout.replace('ffdc0050','ffd40024'),r.stdout.replace('12345678','00000000')]:
   with self.assertRaises(ValueError):parse(bad,0x12345678)
if __name__=='__main__':unittest.main()
