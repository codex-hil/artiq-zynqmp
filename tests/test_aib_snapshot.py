"""Actual Tcl fixed-read budget and strict decoder controls. LGPL-3.0-or-later."""
import sys,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from decode_aib_state import parse
class Tests(unittest.TestCase):
 def capture(self,value=0):
  script='''set argv {server 210383B7F02DA}
proc connect {args} {}
proc disconnect {} {}
proc after {args} {}
proc targets {args} {if {[lindex $args 0] eq "-set"} {return};return [list [dict create jtag_cable_serial 210383B7F02DA target_id 1]]}
set reads 0
proc mrd {args} {
 global reads
 if {[llength $args]!=4 || [lrange $args 0 2] ne {-address-space AP0 -value}} {error read-shape}
 if {[lindex $args 3] ni {0xff413030 0xff413038 0xff413040}} {error address}
 incr reads
 return VALUE
}
'''.replace('VALUE',str(value))
  script+='source {'+str(ROOT/'scripts/probe_aib_state.tcl')+'}\nif {$reads!=8} {error budget}\n'
  r=subprocess.run(['tclsh'],input=script,text=True,capture_output=True,timeout=5);self.assertEqual(r.returncode,0);self.assertFalse(r.stderr,r.stderr);return r.stdout
 def test_actual_fixed_reads_and_no_write_permission(self):
  m=parse(self.capture());self.assertTrue(m['selected_inactive_observed']);self.assertFalse(m['isolation_write_allowed']);self.assertFalse(m['destructive_test_allowed'])
  self.assertFalse(parse(self.capture(0x10000))['selected_inactive_observed'])
 def test_malformed_changed_and_inconsistent(self):
  text=self.capture()
  for bad in [text+text,text.replace('0xff413038','0xff41303c'),text.replace('AIB_END',''),text.replace('request_after 0xff413030 0x00000000','request_after 0xff413030 0x00010000',1)]:
   with self.assertRaises(ValueError):parse(bad)
  changed=text.replace('AIB 1 ack 0xff413040 0x00000000','AIB 1 ack 0xff413040 0x00010000')
  self.assertFalse(parse(changed)['selected_inactive_observed'])
if __name__=='__main__':unittest.main()
