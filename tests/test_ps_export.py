"""PS export preparation and result admission; LGPL-3.0-or-later."""
import json,sys,tempfile,unittest,shutil
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from remote_rtio_build import prepare_ps,metadata,submit,collect,sha


class PSExportTests(unittest.TestCase):
    def source(self,root):
        source=root/'source';source.mkdir()
        for n in ('vivado_script.tcl','migen_integration.tcl','zynq_ultra_ps_e_0.properties.tcl'):(source/n).write_text('source')
        return source

    def test_preparation_is_offline_bounded_and_immutable(self):
        with tempfile.TemporaryDirectory() as d,patch('remote_rtio_build.ssh') as ssh:
            root=Path(d);job=root/'job';m=prepare_ps(self.source(root),job)
            ssh.assert_not_called();self.assertEqual(metadata(job),m)
            runner=(job/'run.sh').read_text();self.assertIn('flock 9',runner);self.assertIn('local-rtio-dma',runner)
            self.assertNotIn('\\\\n',runner)
            (job/'vivado_script.tcl').write_text('changed')
            with self.assertRaises(ValueError):submit(job)
            ssh.assert_not_called()
            with self.assertRaises(ValueError):prepare_ps(root/'source',job)

    def test_missing_and_linked_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=self.source(root);p=source/'vivado_script.tcl';p.unlink()
            with self.assertRaises(ValueError):prepare_ps(source,root/'missing')
            p.symlink_to(source/'migen_integration.tcl')
            with self.assertRaises(ValueError):prepare_ps(source,root/'linked')

    def test_incomplete_success_cannot_be_approved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);job=root/'job';m=prepare_ps(self.source(root),job);remote=root/'remote';shutil.copytree(job,remote)
            (remote/'exit.json').write_text('{"returncode":0}');(remote/'console.log').write_text('incomplete')
            hashes={p.name:sha(p) for p in remote.iterdir() if p.is_file()};out=root/'out'
            def transfer(*args,**kwargs):
                for name in hashes:shutil.copyfile(remote/name,out/name)
            with patch('remote_rtio_build.export_hashes',return_value=hashes),patch('remote_rtio_build.subprocess.run',side_effect=transfer):r=collect(job,out)
            self.assertEqual(r['status'],'RESULT_CHECK_FAILED');self.assertTrue((out/'console.log').exists())

if __name__=='__main__':unittest.main()
