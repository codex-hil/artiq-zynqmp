"""PS importer relocation and parameter admission controls; LGPL-3.0-or-later."""
import json,sys,tempfile,unittest,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_ps_import import prepare
from check_remote_rtio_build import sha


class PSImportTests(unittest.TestCase):
    def fixture(self,root):
        source=root/'source';source.mkdir();(source/'ip').mkdir()
        for name,value in {'mi_xci_files.txt':'/original/ip/ps.xci\n','mi_part.txt':'part\n','mi_bd_cells.txt':'ps\n','ip/ps.xci':json.dumps(dict(ip_inst=dict(parameters=dict(component_parameters=dict(CLOCK=[dict(value='125')])))))}.items():(source/name).write_text(value)
        (source/'ps').mkdir();(source/'ps/pins.txt').write_text('clock\n')
        self.receipt(source);return source

    def receipt(self,source):
        files={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file() and p.name!='retrieval.json'}
        (source/'retrieval.json').write_text(json.dumps(dict(sha256=files)))

    def test_copy_only_changes_index_preserves_original(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=self.fixture(root);before=(source/'mi_xci_files.txt').read_bytes();out=root/'view'
            report=prepare(source,'/original',out,source)
            self.assertEqual(report['comparison']['status'],'PS_PARAMETERS_AND_REPORTS_IDENTICAL')
            self.assertEqual((source/'mi_xci_files.txt').read_bytes(),before)
            self.assertEqual((out/'mi_xci_files.txt').read_text(),str(out/'ip/ps.xci')+'\n')
            with self.assertRaises(ValueError):prepare(source,'/original',out)

    def test_changed_external_missing_and_linked_inputs_rejected(self):
        for kind in ('changed','external','missing','linked'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
                root=Path(d);source=self.fixture(root)
                if kind=='changed':(source/'ip/ps.xci').write_text('changed')
                if kind=='external':
                    (source/'mi_xci_files.txt').write_text('/outside/ps.xci\n');self.receipt(source)
                if kind=='missing':(source/'ip/ps.xci').unlink()
                if kind=='linked':
                    p=source/'ip/ps.xci';p.unlink();p.symlink_to(source/'mi_part.txt')
                with self.assertRaises(ValueError):prepare(source,'/original',root/'view')
                self.assertFalse((root/'view').exists())

    def test_parameter_change_prevents_preparation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=self.fixture(root);baseline=root/'baseline';shutil.copytree(source,baseline)
            p=baseline/'ip/ps.xci';p.write_text(p.read_text().replace('125','156.25'))
            with self.assertRaisesRegex(ValueError,'differs'):prepare(source,'/original',root/'view',baseline)
            self.assertFalse((root/'view').exists())

if __name__=='__main__':unittest.main()
