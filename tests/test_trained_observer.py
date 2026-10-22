"""Trained observer composition controls, no hardware; LGPL-3.0-or-later."""
import subprocess
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_trained_observer import decode
ROOT=Path(__file__).resolve().parents[1]

MOCK='''
set argv [list server observer.elf 0xfffc0bf4 210383B7F02DA]
set halted 1
set phase fsbl
set bad 0
proc connect {args} {}
proc disconnect {} {}
proc configparams {args} {}
proc after {args} {}
proc targets {args} {
 global halted
 if {[lindex $args 0] eq "-set"} {return}
 return [list [dict create name {Cortex-A53 #0} jtag_cable_serial 210383B7F02DA suspended $halted target_id 1]]
}
proc stop {} {global halted; set halted 1}
proc dow {elf} {global phase; puts DOWNLOAD; set phase downloaded}
proc con {} {global phase halted; set phase observed; set halted 0}
proc rrd {option name} {
 global phase bad
 if {$phase eq "fsbl"} {
  set values [dict create pc fffc0bf4 currentel c sctlr_el3 0 daif 3c0 mpidr_el1 80000000]
  if {$bad} {dict set values sctlr_el3 4}
 } elseif {$phase eq "downloaded"} {set values [dict create pc fffc0000]} else {
  set values [dict create pc fffc0034 x0 c x1 0 x2 501 x3 0 x4 0 x5 0 x6 3c0 x7 80000000 x8 fffe0000 x9 fffc0000 x15 33]
 }
 return [list $name [dict get $values $name]]
}
'''

class TrainedTests(unittest.TestCase):
 def run_model(self,mutation=''):
  body=MOCK+mutation+'\nif {[catch {source {'+str(ROOT/'scripts/run_trained_observer.tcl')+'}} msg]} {puts "REJECT $msg"}\n'
  result=subprocess.run(['tclsh'],input=body,text=True,capture_output=True,timeout=5)
  self.assertEqual(result.returncode,0,result.stderr);self.assertFalse(result.stderr,result.stderr)
  return result.stdout
 def test_success(self):
  text=self.run_model();self.assertEqual(decode(text)['x15'],51)
  self.assertEqual(text.count('DOWNLOAD'),1)
 def test_admission_failure_never_downloads(self):
  text=self.run_model('set bad 1')
  self.assertIn('REJECT',text);self.assertNotIn('DOWNLOAD',text)
 def test_definitions_only_does_not_download(self):
  mock=MOCK.replace('proc rrd {option name}', 'proc rrd {option args}').replace('global phase bad', 'set name [lindex $args 0]; global phase bad').replace('210383B7F02DA]','210383B7F02DA definitions]',1).replace('global phase bad', 'global phase bad; if {$option eq "-defs"} {return {cpsr EL3_group}}; if {$name eq "cpsr"} {return {cpsr 3cd}}')
  body=mock+'\nif {[catch {source {'+str(ROOT/'scripts/run_trained_observer.tcl')+'}} msg]} {puts "REJECT $msg"}\n'
  r=subprocess.run(['tclsh'],input=body,text=True,capture_output=True,timeout=5)
  self.assertFalse(r.stderr);self.assertIn('FSBL_REGISTER_DEFINITIONS_END',r.stdout)
  self.assertNotIn('DOWNLOAD',r.stdout);self.assertNotIn('REJECT',r.stdout)
  self.assertEqual(r.stdout.count('FSBL_SYS_CHILD_END'),16);self.assertIn('FSBL_SYS_DEFINITIONS_END',r.stdout);self.assertIn('FSBL_CPSR_RAW 973',r.stdout)
 def test_bad_result_rejected(self):
  text=self.run_model()
  for changed in [text.replace('OBSERVER_REGISTER x15 51','OBSERVER_REGISTER x15 0'),text+ 'OBSERVER_PC 4294705204\n',text.replace('OBSERVER_REGISTER x0 12','OBSERVER_REGISTER x0 4')]:
   with self.assertRaises(ValueError):decode(changed)

if __name__=='__main__':unittest.main()
