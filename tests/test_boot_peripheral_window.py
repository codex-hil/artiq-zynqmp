"""Boot-window negative controls; LGPL-3.0-or-later."""
import copy
import json
import tempfile
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from plan_peripheral_dma_snapshot import decode,REGISTERS
from check_boot_peripheral_window import check

class WindowTests(unittest.TestCase):
 def test_zero_is_necessary_not_sufficient(self):
  z=dict.fromkeys(REGISTERS,0);r=check(decode([z,z]))
  self.assertTrue(r['necessary_fields_pass']);self.assertFalse(r['destructive_test_allowed'])
 def test_each_active_master_and_unstable_reject(self):
  z=dict.fromkeys(REGISTERS,0)
  for n,values in [('gem0_network_control',[4,8]),('sd1_present_state',[1,2,4,256,512]),('qspi_dma_status',[1,2,32,65536])]:
   for v in values:
    s=dict(z,**{n:v})
    self.assertFalse(check(decode([s,s]))['necessary_fields_pass'])
    self.assertFalse(check(decode([z,s]))['necessary_fields_pass'])
  for bad in [{},{'samples':[{},{}],'stable':True}]:
   self.assertFalse(check(bad)['necessary_fields_pass'])


 def test_parent_nested_pins_and_failure_restore(self):
  from test_candidate_runtime_hw import observer_preflight,lifecycle
  root=Path(__file__).resolve().parents[1]
  path=root/'evidence/boot-pmu-integration-2026-10-23/inputs.json'
  info=json.loads(path.read_text())
  files=json.loads((root/'evidence/trained-observer-integration-2026-10-22/runtime-inputs.json').read_text())['files']
  self.assertTrue(observer_preflight(path,files)['peripheral_inputs'])
  for change in ['digest','mode','script']:
   bad=copy.deepcopy(info)
   if change=='digest':bad['peripheral_inputs']['sha256']='0'*64
   elif change=='mode':bad['exception_brk']=True
   else:del bad['script_sha256']['scripts/check_boot_peripheral_window.py']
   with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'bad.json';p.write_text(json.dumps(bad))
    with self.assertRaises(ValueError):observer_preflight(p,files)
  calls=[]
  def cycle(which):
   calls.append(which)
   if which=='candidate':raise ValueError('active peripheral window')
   return 'restored'
  result=lifecycle(cycle)
  self.assertEqual(result['status'],'FAIL')
  self.assertEqual(result['restoration'],'PASS')
  self.assertEqual(calls,['candidate','restore'])

if __name__=='__main__':unittest.main()
