"""Actual offline artifact admission, no UART or JTAG. LGPL-3.0-or-later."""
import copy,json,tempfile,unittest
from pathlib import Path
from lab_fault_admission import validate
ROOT=Path('/srv/codex-hil-data/artiq-zynqmp')

class AdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=ROOT/'build-vivado/genesys-delay-metrics-route-2026-10-20'
        cls.fwdir=ROOT/'build/native-ddma-lab-idle-firmware-2026-10-20'
        if not (cls.build/'results.json').exists():raise unittest.SkipTest('Prepared-host lab artifacts absent')
    def values(self):
        cfg=dict(lab_fault_mode='idle',lab_fault_ack='native-underflow-no-reuse',native_ddma_mode='idle',
                 reset_test=True,dio_test=True,snapshot_test=True,bitstream=str(self.build/'top.bit'),
                 firmware=str(self.fwdir/'aux-firmware.elf'),csr_map=str(self.build/'csr-map.json'))
        return cfg,json.loads((self.fwdir/'results.json').read_text()),json.loads((self.build/'csr-map.json').read_text())
    def test_actual_idle_artifacts_and_stale_source_controls(self):
        c,f,m=self.values();self.assertEqual(validate(c,f,m)['mode'],'idle')
        for group,key in [('lab_sources','ddma_lab_runtime.h'),('ddma_sources','ddma_backend.h')]:
            bad=copy.deepcopy(f);bad[group][key]='0'*64
            with self.assertRaises(ValueError):validate(c,bad,m)
        bad=copy.deepcopy(f);bad['c_source_sha256']='0'*64
        with self.assertRaises(ValueError):validate(c,bad,m)
    def test_explicit_scope_and_missing_idle_proof(self):
        c,f,m=self.values()
        for patch in [dict(lab_fault_ack=''),dict(host_dma_test=True),dict(native_ddma_mode='playback')]:
            with self.assertRaises(ValueError):validate(c|patch,f,m)
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'proof.json';p.write_text('{}')
            with self.assertRaises(ValueError):validate(c|dict(lab_fault_mode='active',native_ddma_mode='playback',lab_idle_qualification=str(p)),f,m)

    def test_actual_guarded_parent_idle_preflight_and_active_refusal(self):
        path=ROOT/'build/lab-idle-observer-2026-10-20.json'
        if not path.exists():self.skipTest('Prepared parent idle config absent')
        from external_session import ExternalSession
        cfg=json.loads(path.read_text())
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'config.json';p.write_text(json.dumps(cfg))
            self.assertEqual(ExternalSession(p,Path(name)/'output').lab_fault_mode,'idle')
            for patch in [dict(lab_fault_mode='active'),dict(lab_fault_ack='')]:
                p.write_text(json.dumps(cfg|patch))
                with self.assertRaises(ValueError):ExternalSession(p,Path(name)/'output')
