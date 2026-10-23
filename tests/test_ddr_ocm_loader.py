"""Real Tcl OCM-only read allowlist and report controls; LGPL-3.0-or-later."""
import json,sys,tempfile,subprocess,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_ddr_ocm_model import parse,preflight
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_real_tcl_fixed_ocm_reads_and_no_other_writes(self):
  tag=(~(0x87ffffff8^0xa53dd4c0dec0ffee))&0xffffffffffffffff
  words=[16,0,16,0,0x7ffffff8,8,tag&0xffffffff,tag>>32,tag&0xffffffff,tag>>32,3,0]
  script='source {'+str(ROOT/'scripts/load_ddr_ocm_model.tcl')+'}\n'
  script+='''proc fsbl_entry::selected_halted {} {}
proc fsbl_entry::observe_pair {terminal} {
 if {$terminal != 0xfffc8834} {error wrong-predecessor}
 return [list [dict create cpsr 13 sctlr_el3 0 daif 0x2c0 mpidr_el1 0]]
}
set resumed 0
proc fsbl_entry::register {name} {
 global resumed
 if {$name eq "pc"} {return [expr {$resumed ? 0xfffc888c : 0xfffc8800}]}
 if {$name eq "sys 12 vbar_el3"} {return 0xfffc8000}
 if {$name eq "x15"} {return 51}
 return 0
}
proc exception_observer::unchanged_controls {before} {}
proc exception_observer::halt {} {}
proc dow {elf} {if {$elf ne "model.elf"} {error wrong-elf}}
proc rwr {args} {if {$args ne {sys 12 vbar_el3 0xfffc8000}} {error wrong-write}}
proc con {} {global resumed;set resumed 1}
proc after {args} {}
set reads 0
'''
  script+='set words {'+' '.join(str(w) for w in words)+'}\n'
  script+='''proc mrd {args} {
 global reads words
 if {[lindex $args 0] ne "-value"} {error wrong-access}
 set address [lindex $args 1]
 if {$reads < 12} {
  if {$address != 0xfffc8cf0+4*$reads} {error wrong-address}
  set value [lindex $words $reads]
 } else {
  if {$reads != 12 || $address != 0xfffc8d20} {error wrong-result}
  set value 0
 }
 incr reads;return $value
}
ddr_model::run model.elf
if {$reads != 13} {error wrong-count}
'''
  r=subprocess.run(['tclsh'],input=script,text=True,capture_output=True,timeout=5)
  self.assertEqual(r.returncode,0);self.assertFalse(r.stderr,r.stderr)
  self.assertFalse(parse(r.stdout)['destructive_test_allowed'])
  for text in [r.stdout+r.stdout,r.stdout.replace('DDR_MODEL_END',''),r.stdout.replace('DDR_MODEL_RESULT 0x00000000','DDR_MODEL_RESULT 0x00000001'),r.stdout.replace(str(0xfffc888c),str(0xfffc88b4))]:
   with self.assertRaises(ValueError):parse(text)
 def test_actual_image_and_stale_pin(self):
  path=ROOT/'evidence/ddr-model-brk-integration-2026-10-23/model-inputs.json';preflight(path,ROOT)
  m=json.loads(path.read_text());m['elf']['sha256']='0'*64
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'bad.json';p.write_text(json.dumps(m))
   with self.assertRaises(ValueError):preflight(p,ROOT)
if __name__=='__main__':unittest.main()
