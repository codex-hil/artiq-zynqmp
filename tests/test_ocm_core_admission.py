"""XSDB core-state admission model controls; LGPL-3.0-or-later."""
import subprocess,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
SOURCE=(REPO/'scripts/run_ocm_environment.tcl').read_text()
PROC=SOURCE[SOURCE.index('proc admit_core'):SOURCE.index('connect -url $server')]

class CoreAdmission(unittest.TestCase):
    def run_gate(self,scenario,allow=1):
        model='''
set calls 0
proc targets {args} {
 global scenario calls
 if {$scenario eq "missing"} {return [list [dict create]]}
 set suspended [expr {$scenario eq "stopped" || ($scenario eq "running" && $calls > 0)}]
 return [list [dict create suspended $suspended]]
}
proc stop {} {
 global scenario calls
 incr calls
 if {$scenario eq "por" || ($scenario eq "changing" && $calls == 1)} {error "The core is held in power-on-reset"}
 if {$scenario eq "error"} {error "Transport disconnected"}
}
'''
        text=f'set scenario {scenario}\n'+model+PROC+f'\nif {{[catch {{admit_core {allow}}} message]}} {{puts stderr $message;exit 1}}\nputs "CALLS $calls"\n'
        return subprocess.run(['tclsh'],input=text,capture_output=True,text=True,timeout=3)
    def test_suspended_running_and_confirmed_por(self):
        for scenario,marker,calls in [('stopped','SUSPENDED',0),('running','STOPPED_CONFIRMED',1),('por','HELD_POWER_ON_RESET_CONFIRMED',2)]:
            with self.subTest(scenario=scenario):
                r=self.run_gate(scenario);self.assertEqual(r.returncode,0,r.stderr)
                self.assertIn(marker,r.stdout);self.assertIn(f'CALLS {calls}',r.stdout)
    def test_uncertain_failed_or_post_reset_por_rejected(self):
        for scenario,allow in [('missing',1),('error',1),('changing',1),('unhalted',1),('por',0)]:
            with self.subTest(scenario=scenario,allow=allow):
                r=self.run_gate(scenario,allow);self.assertNotEqual(r.returncode,0)
