"""Offline source identity controls; LGPL-3.0-or-later."""
import subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from capture_release_sources import tree_snapshot,git_snapshot

class SourceTests(unittest.TestCase):
    def test_tree_stable_and_changed_content_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'file').write_text('one')
            a=tree_snapshot(root);self.assertEqual(a,tree_snapshot(root))
            (root/'file').write_text('two');self.assertNotEqual(a['inventory_sha256'],tree_snapshot(root)['inventory_sha256'])

    def test_symlink_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'link').symlink_to('/absent/outside')
            entry=tree_snapshot(root)['entries'][0]
            self.assertEqual(entry,dict(path='link',kind='symlink',target='/absent/outside'))

    def test_git_root_dirty_state_and_untracked_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def git(*args):subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            git('init');git('config','user.email','test@example.invalid');git('config','user.name','test')
            (root/'file').write_text('one');git('add','file');git('commit','-m','base')
            clean=git_snapshot(root);(root/'untracked').write_text('excluded')
            self.assertEqual(clean,git_snapshot(root))
            (root/'file').write_text('two');dirty=git_snapshot(root)
            self.assertNotEqual(clean['tracked_patch_sha256'],dirty['tracked_patch_sha256'])
            (root/'subdir').mkdir()
            with self.assertRaises(ValueError):git_snapshot(root/'subdir')

if __name__=='__main__':unittest.main()
