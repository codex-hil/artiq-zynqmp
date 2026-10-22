"""Tcl fixed read allowlist and strict framing; LGPL-3.0-or-later."""
import subprocess
import contextlib
import io
import json
import tempfile
from unittest.mock import patch
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import capture_zdma_status as capture
from capture_zdma_status import parse
from plan_zdma_snapshot import BASES,OFFSETS
ROOT=Path(__file__).resolve().parents[1]


def frame():
 return 'ZDMA_BEGIN\n'+'\n'.join(f'ZDMA {s} {i} {n} 0x{b+o:08x} 0x00000000' for s in range(2) for i,b in enumerate(BASES) for n,o in OFFSETS.items())+'\nZDMA_END\n'


class CaptureTests(unittest.TestCase):
 def test_complete_frame_never_admits_writes(self):
  r=parse(frame());self.assertTrue(r['all_quiet_fields']);self.assertFalse(r['destructive_test_allowed'])
 def test_incomplete_duplicate_bad_address_order_rejected(self):
  text=frame();lines=text.splitlines()
  variants=[text.replace('ZDMA_END',''),text+text,'\n'.join(lines[:2]+lines[3:]),text.replace('0xfd50011c','0xfd500100'),text.replace('0x00000000','0x100000000',1)]
  swapped=list(lines);swapped[1],swapped[2]=swapped[2],swapped[1];variants.append('\n'.join(swapped))
  for variant in variants:
   with self.assertRaises(ValueError):parse(variant)
 def test_timeout_retains_partial_log_and_releases_lease(self):
  events=[]
  @contextlib.contextmanager
  def fake_lease():
   events.append('enter')
   try:
    with tempfile.TemporaryFile() as f:yield f
   finally:events.append('exit')
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'capture'
   argv=['capture','--inputs',str(ROOT/'evidence/zdma-capture-plan-2026-10-23/inputs.json'),'--output',str(out),'--execute','--server','fake']
   with contextlib.redirect_stdout(io.StringIO()),patch.object(sys,'argv',argv),patch.object(capture,'lease',fake_lease),patch.object(capture,'require_runtime_space'),patch.object(capture,'bounded',side_effect=subprocess.TimeoutExpired('fake',45,output='ZDMA_BEGIN\n')):
    self.assertEqual(capture.main(),1)
   self.assertEqual(events,['enter','exit'])
   self.assertEqual((out/'snapshot.log').read_text(),'ZDMA_BEGIN\n')
   self.assertEqual(json.loads((out/'results.json').read_text())['status'],'FAIL')
 def test_stale_execution_pin_rejected(self):
  inputs=json.loads((ROOT/'evidence/zdma-capture-plan-2026-10-23/inputs.json').read_text())
  inputs['script_sha256']['scripts/probe_zdma_status.tcl']='0'*64
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'inputs.json';p.write_text(json.dumps(inputs))
   with self.assertRaises(ValueError):capture.preflight(p)
 def test_real_tcl_script_only_reads_fixed_addresses(self):
  script='''
set argv {server 210383B7F02DA}
set count 0
proc connect {args} {}
proc disconnect {} {}
proc after {args} {}
proc targets {args} {
 if {[lindex $args 0] eq "-set"} {return}
 return [list [dict create jtag_cable_serial 210383B7F02DA target_id 1]]
}
proc mrd {args} {
 global count
 if {[lrange $args 0 2] ne {-address-space AP0 -value}} {error options}
 set a [lindex $args 3]
 if {($a & 0xffff) ni {284 512}} {error unsafe-offset}
 incr count
 return 0
}
'''+f'source {{{ROOT/"scripts/probe_zdma_status.tcl"}}}\nif {{$count != 64}} {{error count}}\n'
  p=subprocess.run(['tclsh'],input=script,text=True,capture_output=True,timeout=5)
  self.assertEqual(p.returncode,0);self.assertFalse(p.stderr,p.stderr)
  self.assertTrue(parse(p.stdout)['all_quiet_fields'])


if __name__=='__main__':unittest.main()
