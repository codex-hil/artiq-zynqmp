"""Real Tcl request write/read bounds and echo rejection; LGPL-3.0-or-later."""
import sys,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from pmu_request_candidate import parse
class Tests(unittest.TestCase):
 def test_real_tcl_only_request_writes(self):
  script='''set argv {server 210383B7F02DA 123 456}
proc connect {args} {}
proc disconnect {} {}
proc after {args} {}
proc targets {args} {
 if {[lindex $args 0] eq "-set"} {return}
 return [list [dict create jtag_cable_serial 210383B7F02DA target_id 1]]
}
set mem [dict create]
set writes 0
set committed 0
proc mwr {args} {
 global mem writes committed
 if {[lrange $args 0 1] ne {-address-space AP0} || [llength $args]!=4} {error bad-write}
 set addr [expr {[lindex $args 2]}];set v [lindex $args 3]
 if {$addr<0xffdd7e20 || $addr>0xffdd7e3c || ($addr&3)} {error address}
 dict set mem $addr $v;incr writes
 if {$addr==0xffdd7e20 && $v==2} {set committed 1}
}
proc mrd {args} {
 global mem committed
 if {[lrange $args 0 2] ne {-address-space AP0 -value}} {error bad-read}
 set addr [expr {[lindex $args 3]}]
 set count [expr {[llength $args]==5 ? [lindex $args 4] : 1}]
 if {$addr ni {4292705760 4292705716}} {error read-address}
 if {$count ni {1 8}} {error read-count}
 if {$addr==0xffdd7df4} {
  set echo [expr {$committed ? [list 2 123 456 1 0 1 0 0] : [list 0 0 0 0 0 0 0 0]}]
  return [lrange $echo 0 [expr {$count-1}]]
 }
 set out {}
 for {set i 0} {$i<$count} {incr i} {
  set key [expr {$addr+4*$i}]
  lappend out [expr {[dict exists $mem $key] ? [dict get $mem $key] : 0}]
 }
 return $out
}
'''
  # Numeric allowlist generated from literal documented image addresses.
  script=script.replace('{4292705760 4292705716}','{'+str(0xffdd7e20)+' '+str(0xffdd7df4)+'}')
  script+='source {'+str(ROOT/'scripts/probe_pmu_observe_request.tcl')+'}\nif {$writes != 9} {error write-count}\n'
  r=subprocess.run(['tclsh'],input=script,text=True,capture_output=True,timeout=5)
  self.assertEqual(r.returncode,0);self.assertFalse(r.stderr,r.stderr)
  nonce=123|(456<<32);self.assertFalse(parse(r.stdout,nonce)['destructive_test_allowed'])
  for bad in [r.stdout+r.stdout,r.stdout.replace('word6 0x00000000','word6 0x00000001'),r.stdout.replace('PMU_ECHO_END','')]:
   with self.assertRaises(ValueError):parse(bad,nonce)
  with self.assertRaises(ValueError):parse(r.stdout,nonce+1)
if __name__=='__main__':unittest.main()
