"""PCAP real-Tcl allowlist and frame controls; LGPL-3.0-or-later."""
import sys,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from capture_pcap_controls import parse
class CaptureTests(unittest.TestCase):
 def test_real_tcl_eight_reads(self):
  mock='set argv {server 210383B7F02DA}\nproc connect {args} {}\nproc disconnect {} {}\nproc after {args} {}\nproc targets {args} {\n if {[lindex $args 0] eq "-set"} {return}\n return [list [dict create jtag_cable_serial 210383B7F02DA target_id 1]]\n}\nset reads 0\nproc mrd {args} {\n global reads\n if {[lrange $args 0 2] ne {-address-space AP0 -value} || [lindex $args 3] ni {0xffca3010 0xffca300c 0xffca3008 0xffca3004}} {error unsafe-read}\n incr reads\n return 0\n}\n'
  mock+='source {'+str(ROOT/'scripts/probe_pcap_controls.tcl')+'}\nif {$reads != 8} {error count}\n'
  r=subprocess.run(['tclsh'],input=mock,text=True,capture_output=True,timeout=5)
  self.assertEqual(r.returncode,0);self.assertFalse(r.stderr,r.stderr)
  self.assertTrue(parse(r.stdout)['stable'])
  self.assertFalse(parse(r.stdout)['destructive_test_allowed'])
  self.assertEqual(parse(r.stdout)['ownership'],'NOT_PROVEN')
  for bad in [r.stdout+r.stdout,r.stdout.replace('PCAP_CONTEXT_END',''),r.stdout.replace('ffca3010','ffca3014')]:
   with self.assertRaises(ValueError):parse(bad)
if __name__=='__main__':unittest.main()
