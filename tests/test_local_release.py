"""Release chain negative admission controls; LGPL-3.0-or-later."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import verify_local_release as release


class ReleaseControls(unittest.TestCase):
    def test_package_rejects_unbound_proof(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);manifest=p/'manifest';manifest.write_text('{}');proof=p/'proof';proof.write_text('{}')
            (p/'release.json').write_text(json.dumps(dict(manifest_sha256='wrong',extended_jtag_proof_sha256=release.sha(proof))))
            with self.assertRaisesRegex(ValueError,'proof binding'):
                release.bind_package(p,manifest,proof,{})

    def test_package_rejects_substituted_role(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);manifest=p/'manifest';manifest.write_text('{}');proof=p/'proof';proof.write_text('{}')
            (p/'release.json').write_text(json.dumps(dict(manifest_sha256=release.sha(manifest),extended_jtag_proof_sha256=release.sha(proof))))
            (p/'artifacts.json').write_text(json.dumps(dict(artifacts=dict(fsbl=dict(path='/not-read',sha256='substitute')))))
            with self.assertRaisesRegex(ValueError,'role mismatch: fsbl'):
                release.bind_package(p,manifest,proof,dict(candidate_fsbl=dict(sha256='qualified')))

    def test_changed_configuration_cannot_reach_package_pass(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'inputs').write_text('{}');(p/'top.bit').write_bytes(b'changed')
            files=dict(candidate_pl=dict(path=str(p/'top.bit')))
            config=dict(candidate_manifest=str(p/'manifest'),hardware_proof=str(p/'proof'),source_build=d,build_inputs=str(p/'inputs'))
            with patch.object(release,'verify_proof',return_value=files),patch.object(release,'check',return_value={}),patch.object(release,'compare',return_value=dict(status='CONFIGURATION_BYTES_DIFFER')),patch.object(release,'bind_package') as package:
                with self.assertRaisesRegex(ValueError,'differs from qualified'):
                    release.verify(config)
                package.assert_not_called()

if __name__=='__main__':unittest.main()
