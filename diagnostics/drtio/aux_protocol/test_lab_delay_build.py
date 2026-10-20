"""Map/source guard tests; LGPL-3.0-or-later."""
import copy,json,unittest
from pathlib import Path
from lab_delay_build import validate_map,source_overlay
ROOT=Path(__file__).resolve().parents[3]

class BuildTests(unittest.TestCase):
    def test_checked_map_and_mutations(self):
        mapping=json.loads((ROOT/'evidence/genesys-delay-metrics-hdl-2026-10-20/csr-map.json').read_text())
        self.assertEqual(validate_map(mapping),250000)
        for group in ('registers','nested','clock','cycles','missing','metrics'):
            m=copy.deepcopy(mapping)
            if group=='registers':m['registers']['dma_lab_delay_arm']['address']+=4
            if group=='nested':m['dma']['registers']['dma_lab_delay_cycles']['bits']=1
            if group=='clock':m['dma']['laboratory_read_delay']['ps_clock_source']['configured_hz']=100000000
            if group=='cycles':m['dma']['laboratory_read_delay']['cycles']=200000
            if group=='metrics':m['dma']['laboratory_read_delay']['independent_metrics']=False
            if group=='missing':del m['dma']['laboratory_read_delay']
            with self.assertRaises(ValueError):validate_map(m)
    def test_source_overlay_preserves_original_and_refuses_reapplication(self):
        p=ROOT/'diagnostics/drtio/aux_protocol/firmware.c';original=p.read_text()
        generated=source_overlay(original)
        self.assertEqual(p.read_text(),original)
        self.assertIn("if(command=='F')ddma_lab_request();",generated)
        self.assertIn('ddma_lab_runtime.h',generated)
        with self.assertRaises(ValueError):source_overlay(generated)
        with self.assertRaises(ValueError):source_overlay(original.replace('  ddma_poll();',''))
    def test_normal_native_wrapper_refuses_lab(self):
        import sys
        sys.path.insert(0,str(ROOT/'diagnostics/drtio'))
        from native_dma_session import validate
        with self.assertRaisesRegex(ValueError,'dedicated fault wrapper'):validate(None,{'lab_read_delay':True})
