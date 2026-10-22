"""Artifact relocation preserves data or retains originals on failure; LGPL-3.0-or-later."""
import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
import relocate_completed_builds as relocation
class Relocation(unittest.TestCase):
    def fixture(self,d):
        p=Path(d);source=p/'source';source.mkdir();(source/'data').write_bytes(b'\x00\xff\r\nartifact')
        (source/'exec').write_text('tool');(source/'exec').chmod(0o750);(source/'relative').symlink_to('data')
        return source,p/'destination',p/'report.gz'
    def test_verified_copy_and_original_paths(self):
        with tempfile.TemporaryDirectory() as d:
            src,dst,report=self.fixture(d);before=relocation.inventory(src);result=relocation.relocate(src,dst,report)
            self.assertTrue(src.is_symlink());self.assertEqual(relocation.inventory(src),before)
            self.assertEqual((src/'relative').read_bytes(),b'\x00\xff\r\nartifact')
            self.assertEqual(result['status'],'RELOCATED_VERIFIED_ORIGINAL_PATH_RETAINED')
    def test_corrupt_copy_keeps_original(self):
        with tempfile.TemporaryDirectory() as d:
            src,dst,report=self.fixture(d);original=relocation.shutil.copytree
            def corrupt(*args,**kwargs):
                original(*args,**kwargs);(dst/'data').write_bytes(b'wrong')
            with patch.object(relocation.shutil,'copytree',side_effect=corrupt):
                with self.assertRaisesRegex(ValueError,'verification'):relocation.relocate(src,dst,report)
            self.assertFalse(src.is_symlink());self.assertEqual((src/'data').read_bytes(),b'\x00\xff\r\nartifact')
    def test_failed_link_rolls_back_original_directory(self):
        with tempfile.TemporaryDirectory() as d:
            src,dst,report=self.fixture(d)
            with patch.object(Path,'symlink_to',side_effect=OSError('link failed')):
                with self.assertRaises(OSError):relocation.relocate(src,dst,report)
            self.assertTrue(src.is_dir());self.assertFalse(src.is_symlink());self.assertTrue(dst.is_dir())
            self.assertEqual(relocation.inventory(src),relocation.inventory(dst))
if __name__=='__main__':unittest.main()
