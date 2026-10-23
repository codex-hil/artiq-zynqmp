"""Observer map/Tcl/frame controls; LGPL-3.0-or-later."""
import sys,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_dma_observer_snapshot import parse,check_map
class Tests(unittest.TestCase):
 def test_map_and_actual_tcl(self):
  check_map(ROOT/'evidence/dma-observer-full-build-2026-10-23/csr-map.json')
  mock='''set argv {server 210383B7F02DA}
proc connect {args} {}
proc disconnect {} {}
proc after {args} {}
proc targets {args} {
 if {[lindex $args 0] eq "-set"} {return}
 return [list [dict create jtag_cable_serial 210383B7F02DA target_id 1]]
}
set reads {}
proc mrd {args} {
 global reads
 if {[lrange $args 0 2] ne {-address-space AP0 -value}} {error unsafe-read}
 lappend reads [lindex $args 3]
 return 0
}
'''
  mock+='source {'+str(ROOT/'scripts/probe_dma_observer.tcl')+'}\nif {$reads ne {0xa0003000 0xa0003004 0xa0003000 0xa0003004}} {error wrong-addresses}\n'
  r=subprocess.run(['tclsh'],input=mock,text=True,capture_output=True,timeout=5)
  self.assertEqual(r.returncode,0);self.assertFalse(r.stderr,r.stderr)
  result=parse(r.stdout);self.assertTrue(result['zero_count_observed']);self.assertFalse(result['destructive_test_allowed'])
  for bad in [r.stdout+r.stdout,r.stdout.replace('DMA_OBSERVER_END',''),r.stdout.replace('0xa0003004','0xa0003008'),r.stdout.replace('0x00000000','0x00000004')]:
   with self.assertRaises(ValueError):parse(bad)
if __name__=='__main__':unittest.main()
