"""OCM admission and child loader-failure controls, no hardware; LGPL-3.0-or-later."""
import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import MagicMock,patch
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
from test_candidate_runtime_hw import ocm_preflight,lifecycle
import run_ocm_environment as child


class OCMObservation(unittest.TestCase):
    def fixture(self,root):
        layout=json.loads((REPO/'evidence/ocm-environment-build-2026-10-22/layout.json').read_text());paths=list(layout['input_sha256'])
        elf=Path(paths[0]);symbols=REPO/paths[1]
        data=dict(elf=dict(path=str(elf),sha256=hashlib.sha256(elf.read_bytes()).hexdigest()),symbols=dict(path=str(symbols),sha256=hashlib.sha256(symbols.read_bytes()).hexdigest()),ps_init=dict(path=str(root/'ps.tcl'),sha256='unused'),script_sha256={n:hashlib.sha256((REPO/n).read_bytes()).hexdigest() for n in ('scripts/run_ocm_environment.py','scripts/run_ocm_environment.tcl')})
        (root/'ps.tcl').write_text('setup');data['ps_init']['sha256']=hashlib.sha256((root/'ps.tcl').read_bytes()).hexdigest()
        p=root/'manifest.json';p.write_text(json.dumps(data));return p,data

    def test_preflight_and_changed_script_pin_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,data=self.fixture(root);files=dict(candidate_ps_init=data['ps_init'])
            ocm_preflight(p,files)
            data['script_sha256']['scripts/run_ocm_environment.tcl']='0'*64;p.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'script'):ocm_preflight(p,files)

    def test_loader_failure_records_output_and_outer_restores(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,data=self.fixture(root);out=root/'capture';seen=[]
            argv=['observe','--server','fixture','--port','fixture','--elf',data['elf']['path'],'--symbols',data['symbols']['path'],'--ps-init',data['ps_init']['path'],'--output',str(out)]
            serial=MagicMock()
            def cycle(role):
                seen.append(role)
                if role=='candidate':
                    with patch.object(sys,'argv',argv),patch.object(child,'require_lease'),patch('serial.Serial',return_value=serial),patch.object(child.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'loader failed','')):
                        if child.main():raise RuntimeError('candidate failed')
                return 'restored'
            result=lifecycle(cycle);self.assertEqual(result['status'],'FAIL');self.assertEqual(result['restoration'],'PASS')
            self.assertEqual(seen,['candidate','restore']);self.assertIn('loader failed',(out/'load.log').read_text())

if __name__=='__main__':unittest.main()
