"""Real Tcl exact-PMU halt/download ordering, no HW; LGPL-3.0-or-later."""
import subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def run_mock(self,allow):
  script='''set argv {server baseline.elf 210383B7F02DA}
set hardware_halted 0
set downloads 0
set resumed 0
proc connect {args} {}
proc disconnect {} {}
proc after {args} {}
proc targets {args} {
 global hardware_halted
 if {[lindex $args 0] eq "-set"} {return}
 return [list [dict create name {MicroBlaze PMU} jtag_cable_serial 210383B7F02DA target_id 4 suspended $hardware_halted]]
}
proc stop {} {global hardware_halted allow;set hardware_halted $allow}
proc dow {elf} {
 global hardware_halted downloads
 if {!$hardware_halted || $elf ne "baseline.elf"} {error unsafe-download}
 incr downloads
}
proc con {} {global downloads resumed;if {$downloads != 1} {error unsafe-resume};set resumed 1}
'''
  script+=f'set allow {int(allow)}\n'
  script+='set code [catch {source {'+str(ROOT/'scripts/restart_pmu_for_restore.tcl')+'}} message]\nputs "RESULT $code $downloads $resumed"\n'
  r=subprocess.run(['tclsh'],input=script,text=True,capture_output=True,timeout=5)
  self.assertFalse(r.stderr,r.stderr);return r.stdout
 def test_ordered_bootstrap(self):
  text=self.run_mock(True);self.assertIn('PMU_RESTORE_BOOTSTRAP_STARTED',text);self.assertIn('RESULT 0 1 1',text)
 def test_unconfirmed_halt_never_downloads(self):
  text=self.run_mock(False);self.assertNotIn('PMU_RESTORE_BOOTSTRAP_STARTED',text);self.assertIn('RESULT 1 0 0',text)
if __name__=='__main__':unittest.main()
