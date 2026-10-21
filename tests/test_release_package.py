"""Candidate integrity controls, no hardware access; LGPL-3.0-or-later."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_release_package import verify

class PackageTests(unittest.TestCase):
    def fixture(self,root):
        artifacts={};pins={}
        for name in ('fsbl','pmufw','bitstream','application','worker_boot','boot.bin'):
            path=root/name;path.write_bytes(('payload-'+name).encode())
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            artifacts[name]=dict(path=str(path),sha256=sha)
            if name in ('fsbl','pmufw','bitstream'):pins[name]=sha
        (root/'artifacts.json').write_text(json.dumps(dict(kind='packaged-artifacts-not-boot-proof',artifacts=artifacts)))
        return pins

    def test_valid_consistency_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);pins=self.fixture(root);result=verify(root,pins)
            self.assertEqual(result['status'],'CONSISTENCY_PASS_NOT_BOOT_PROOF')
            self.assertFalse(result['hardware_executed'])

    def test_modified_input_and_output_rejected(self):
        for name in ('application','boot.bin'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);pins=self.fixture(root);(root/name).write_bytes(b'tampered')
                with self.assertRaises(ValueError):verify(root,pins)

    def test_unpinned_baseline_and_incomplete_package_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);pins=self.fixture(root)
            with self.assertRaises(ValueError):verify(root,{})
            swapped=dict(pins,fsbl=pins['pmufw'],pmufw=pins['fsbl'])
            with self.assertRaises(ValueError):verify(root,swapped)
            p=root/'artifacts.json';data=json.loads(p.read_text());del data['artifacts']['pmufw'];p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):verify(root,pins)

if __name__=='__main__':unittest.main()
