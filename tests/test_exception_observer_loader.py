"""Exception loader sequencing model; no hardware. LGPL-3.0-or-later."""
import subprocess
import unittest
from pathlib import Path
LIB=Path(__file__).resolve().parents[1]/'scripts/load_el3_exception_observer.tcl'
MOCK='''
set pc 0xfffc0bf4
set pstate 0x600002cd
set ctl 0xc00818
set halted 1
set vbar 0xfffc0000
set reject_vbar 0
set fault 0
set reads_after_write 0
set ran 0
set mode normal
set writes {}
proc targets {args} {
 global halted
 return [list [dict create name {Cortex-A53 #0} jtag_cable_serial 210383B7F02DA suspended $halted]]
}
proc after {args} {}
proc rrd {option args} {
 global pc pstate ctl vbar reject_vbar reads_after_write ran fault
 if {$option ne "-nvlist"} {error bad-option}
 set name [lindex $args end]
 switch $name {
  pc {set value $pc}
  cpsr {set value $pstate}
  sctlr_el3 {
   if {$args ne {sys 1 sctlr_el3}} {error wrong-control-path}
   set value $ctl
  }
  mpidr_el1 {
   if {$args ne {sys 0 mpidr_el1}} {error wrong-affinity-path}
   set value 0x80000000
  }
  vbar_el3 {
   if {$args ne {sys 12 vbar_el3}} {error wrong-vector-path}
   set value $vbar
   if {$vbar == 0xfffc8000} {incr reads_after_write; if {$reject_vbar} {set value 0}}
  }
  default {
   set values [dict create r0 12 r1 $ctl r2 0 r3 0 r4 0 r5 0 r6 0x2c0 r7 0x80000000 r8 0xfffe0000 r9 0xfffc8800 r14 4 r15 0x33 r16 12 r17 0xf2000053 r18 0 r19 0xfffc884c r20 0x600002cd r21 0x3c0]
   if {$fault} {dict set values r15 0xf3}
   set value [dict get $values $name]
  }
 }
 return [list $name [format %x $value]]
}
proc dow {elf} {global pc; set pc 0xfffc8800; puts DOWNLOADED}
proc rwr {args} {
 global vbar pc writes
 lappend writes $args
 if {[lrange $args 0 end-1] eq {sys 12 vbar_el3}} {set vbar [lindex $args end]} elseif {[lindex $args 0] eq "pc"} {set pc [lindex $args end]} else {error unexpected-write}
}
proc con {} {
 global ran halted vbar reads_after_write pc fault
 if {$vbar != 0xfffc8000 || $reads_after_write < 2} {error vector-not-ready}
 set ran 1;set halted 0
 if {$fault} {set pc 0xfffc8878} else {set pc 0xfffc8834}
 puts CONTINUED
}
proc stop {} {global halted;set halted 1}
'''


class LoaderTests(unittest.TestCase):
 def run_model(self,changes=''):
  text=f'source {{{LIB}}}\n'+MOCK+changes+'\nif {[catch {exception_observer::run observer.elf 0xfffc0bf4 $mode} message]} {puts "FAIL $message"}\nputs "WRITES $writes"\n'
  p=subprocess.run(['tclsh'],input=text,text=True,capture_output=True,timeout=5)
  self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(p.stderr,p.stderr)
  return p.stdout
 def test_normal_does_not_mask_a(self):
  out=self.run_model()
  self.assertIn('EXCEPTION_OBSERVER_NORMAL_COMPLETE',out)
  self.assertNotIn('FAIL',out)
  self.assertEqual(out.count('EXCEPTION_RESUME_STATE '),10)
  self.assertIn('daif 704',out)
  self.assertIn('WRITES {sys 12 vbar_el3 0xfffc8000}',out)
 def test_vbar_readback_failure_prevents_continue(self):
  out=self.run_model('set reject_vbar 1')
  self.assertIn('VBAR readback mismatch',out);self.assertNotIn('CONTINUED',out)
 def test_fault_is_never_normal_pass(self):
  out=self.run_model('set mode brk\nset fault 1')
  self.assertIn('EXCEPTION_CAPTURED',out);self.assertIn('EXCEPTION_REGISTER x17 4060086355',out)
  self.assertNotIn('EXCEPTION_OBSERVER_NORMAL_COMPLETE',out)
 def test_wrong_entry_prevents_download(self):
  for changes in ['set ctl 0xc0081c','set pstate 0x600001cd','set pstate 0x600002c5','set pc 0xfffc0c00']:
   with self.subTest(changes=changes):
    out=self.run_model(changes);self.assertIn('FAIL',out);self.assertNotIn('DOWNLOADED',out)


if __name__=='__main__':unittest.main()
