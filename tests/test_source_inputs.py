"""Retained source binding tamper controls; LGPL-3.0-or-later."""
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_source_inputs import verify,tree
from check_remote_rtio_build import sha


class SourceInputs(unittest.TestCase):
    def test_pinned_tree_rejects_change_extra_and_binding_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'tree';root.mkdir();f=root/'input';f.write_text('qualified');m=Path(d)/'binding.json'
            m.write_text(json.dumps(dict(trees=[dict(root=str(root),files={'input':sha(f)},exact_file_set=True)],equal_files=[])))
            expected=sha(m);self.assertEqual(verify(m,expected)['trees_checked'],1)
            f.write_text('changed')
            with self.assertRaisesRegex(ValueError,'Changed source input'):verify(m,expected)
            f.write_text('qualified');(root/'extra').write_text('extra')
            with self.assertRaisesRegex(ValueError,'file set'):verify(m,expected)
            m.write_text('{}')
            with self.assertRaisesRegex(ValueError,'manifest'):verify(m,expected)

    def test_escape_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=root/'real';f.write_text('data');(root/'linked').symlink_to(f)
            for name in ('../escape',str(f),'linked'):
                with self.subTest(name=name),self.assertRaises(ValueError):tree(root,{name:sha(f)})

if __name__=='__main__':unittest.main()
