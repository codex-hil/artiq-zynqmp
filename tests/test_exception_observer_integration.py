"""Exception observer full Tcl dispatch/pins/restore controls. LGPL-3.0-or-later."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from test_exception_observer_loader import MOCK
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_trained_observer import decode_exception
from test_candidate_runtime_hw import observer_preflight,lifecycle
PLAN=ROOT/'evidence/el3-exception-observer-hardware-2026-10-22/resume-trace-inputs.json'


class IntegrationTests(unittest.TestCase):
 def output(self,fault=False):
  setup='''
set argv {server observer.elf 0xfffc0bf4 210383B7F02DA exception}
proc connect {args} {}
proc disconnect {} {}
proc configparams {args} {}
proc targets {args} {
 global halted
 if {[lindex $args 0] eq "-set"} {return}
 return [list [dict create name {Cortex-A53 #0} jtag_cable_serial 210383B7F02DA suspended $halted target_id 1]]
}
'''
  script=MOCK+setup+('set fault 1\n' if fault else '')+'if {[catch {source {'+str(ROOT/'scripts/run_trained_observer.tcl')+'}} msg]} {puts "ERROR $msg"}\n'
  p=subprocess.run(['tclsh'],input=script,text=True,capture_output=True,timeout=5)
  self.assertFalse(p.stderr,p.stderr);self.assertEqual(p.returncode,0)
  return p.stdout
 def test_full_normal_dispatch(self):
  text=self.output();self.assertNotIn('ERROR',text)
  self.assertEqual(decode_exception(text)['x6'],0x2c0)
 def test_fault_decode_failure_still_restores(self):
  text=self.output(True);self.assertIn('EXCEPTION_CAPTURED',text)
  calls=[]
  def cycle(which):
   calls.append(which)
   if which=='candidate':decode_exception(text)
   return 'restored'
  r=lifecycle(cycle)
  self.assertEqual(r['status'],'FAIL');self.assertEqual(r['restoration'],'PASS')
  self.assertEqual(calls,['candidate','restore'])
 def test_corrupt_or_duplicate_result_rejected(self):
  text=self.output()
  for altered in [text+text,text.replace('EXCEPTION_ARMED_VBAR 4294737920','EXCEPTION_ARMED_VBAR 0'),text.replace('EXCEPTION_REGISTER x15 51','EXCEPTION_REGISTER x15 243')]:
   with self.assertRaises(ValueError):decode_exception(altered)
 def test_actual_preflight_and_pin_rejections(self):
  info=json.loads(PLAN.read_text())
  files=json.loads((ROOT/'evidence/trained-observer-integration-2026-10-22/runtime-inputs.json').read_text())['files']
  self.assertTrue(observer_preflight(PLAN,files)['exception_observer'])
  variants=[]
  stale=copy.deepcopy(info);stale['script_sha256']['scripts/load_el3_exception_observer.tcl']='0'*64;variants.append(stale)
  missing=copy.deepcopy(info);del missing['script_sha256']['scripts/inject_rpc_fault.py'];variants.append(missing)
  mixed=copy.deepcopy(info);mixed['controls_only']=True;variants.append(mixed)
  for item in variants:
   with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'inputs.json';p.write_text(json.dumps(item))
    with self.assertRaises(ValueError):observer_preflight(p,files)


if __name__=='__main__':unittest.main()
