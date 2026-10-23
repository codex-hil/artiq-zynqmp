"""Same-boot collector controls; LGPL-3.0-or-later."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from collect_boot_masters import collect,preflight
from test_candidate_runtime_hw import observer_preflight
PLAN=ROOT/'evidence/boot-pcap-integration-2026-10-23/inputs.json'

class MasterTests(unittest.TestCase):
 def test_exact_inventory_and_pins(self):
  info=json.loads(PLAN.read_text())
  files=json.loads((ROOT/'evidence/trained-observer-integration-2026-10-22/runtime-inputs.json').read_text())['files']
  observer_preflight(PLAN,files)
  inventory=Path(info['master_inputs']['path'])
  self.assertEqual(set(preflight(inventory)),{'zdma','csu','rpu','apu','pcap'})
  bad=json.loads(inventory.read_text());bad['rpu']['sha256']='0'*64
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'bad.json';p.write_text(json.dumps(bad))
   with self.assertRaises(ValueError):preflight(p)
 def test_order_and_no_admission_even_when_quiet(self):
  info=json.loads(PLAN.read_text());calls=[]
  def xs(stage,script,server,cable):
   calls.append(script);self.assertEqual(cable,'210383B7F02DA');return script
  with patch('collect_boot_masters.zdma.parse',return_value={'all_quiet_fields':True}),patch('collect_boot_masters.csu.parse',return_value={'csu':{'all_quiet_fields':True}}),patch('collect_boot_masters.rpu.parse',return_value={'ownership':'NOT_PROVEN'}),patch('collect_boot_masters.apu.parse',return_value={'ownership':'NOT_PROVEN'}),patch('collect_boot_masters.pcap.parse',return_value={'sampled_read_write_idle':True}):
   r=collect(Path(info['master_inputs']['path']),xs,'server')
   self.assertEqual(r['not_observed'],['pmu']);self.assertEqual(r['pmu_ownership'],'NOT_PROVEN')
   self.assertTrue(r['necessary_dma_fields_pass']);self.assertFalse(r['destructive_test_allowed'])
  self.assertEqual(calls,['probe_zdma_status.tcl','probe_csu_core_state.tcl','probe_rpu_state.tcl','probe_apu_reset_state.tcl','probe_pcap_state.tcl'])
 def test_malformed_capture_aborts(self):
  info=json.loads(PLAN.read_text())
  with self.assertRaises(ValueError):collect(Path(info['master_inputs']['path']),lambda *a:'INCOMPLETE','server')

if __name__=='__main__':unittest.main()
