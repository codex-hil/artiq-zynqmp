"""Remote staging safety controls; no SSH or hardware; LGPL-3.0-or-later."""
import hashlib,json,sys,tempfile,unittest,shutil
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from remote_rtio_build import prepare,metadata,submit,collect,XCI

class SubmissionTests(unittest.TestCase):
    def fixture(self,root):
        source=root/'source';source.mkdir();rows=[]
        for name in ('top.v','top.xdc','top.tcl','top_route.tcl','top_bitstream.tcl','csr-map.json',XCI):
            path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}' if name.endswith(('.json','.xci')) else 'input')
            rows.append(dict(path=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        (source/'generation.json').write_text(json.dumps(dict(status='HDL_GENERATED_NOT_SYNTHESIZED',files=rows)))
        return source

    def test_prepare_is_offline_and_normalization_separate(self):
        with tempfile.TemporaryDirectory() as tmp,patch('remote_rtio_build.ssh') as ssh:
            root=Path(tmp);source=self.fixture(root);job=root/'safe-job';m=prepare(source,job,'normalize')
            ssh.assert_not_called();self.assertEqual(metadata(job),m)
            self.assertIn('.vivado-build.lock',(job/'run.sh').read_text())
            self.assertIn('NORMALIZED_REVIEW_REQUIRED',(job/'run.sh').read_text())
            self.assertNotIn('synth_design',(job/'normalize.tcl').read_text())
            with self.assertRaises(ValueError):prepare(source,job,'normalize')

    def test_stale_source_and_path_escape_rejected(self):
        for path in ('../private','/absolute'):
            with self.subTest(path=path),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);source=self.fixture(root);p=source/'generation.json';d=json.loads(p.read_text());d['files'][0]['path']=path;p.write_text(json.dumps(d))
                with self.assertRaises(ValueError):prepare(source,root/'job','build')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=self.fixture(root);(source/'top.v').write_text('tampered')
            with self.assertRaises(ValueError):prepare(source,root/'job','build')

    def test_external_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=self.fixture(root);outside=root/'external';outside.write_text('input');(source/'top.v').unlink();(source/'top.v').symlink_to(outside)
            with self.assertRaises(ValueError):prepare(source,root/'job','build')

    def test_normalized_ip_requires_exact_selected_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=self.fixture(root);xci=root/'selected.xci';xci.write_text('{"normalized":true}')
            with self.assertRaises(ValueError):prepare(source,root/'job1','build',xci,None)
            with self.assertRaises(ValueError):prepare(source,root/'job2','build',xci,'0'*64)
            digest=hashlib.sha256(xci.read_bytes()).hexdigest();prepare(source,root/'job3','build',xci,digest)
            data=json.loads((root/'job3/inputs.json').read_text());self.assertEqual(data['selected_normalized_xci_sha256'],digest)

    def test_failed_remote_job_preserves_logs_without_bitstream(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=self.fixture(root);job=root/'job';m=prepare(source,job,'build')
            remote=root/'remote';shutil.copytree(job,remote)
            (remote/'exit.json').write_text('{"returncode":1}')
            (remote/'console.log').write_text('ERROR: build failed')
            (remote/'state.txt').write_text('FAILED')
            names=list(m['upload_sha256'])+['exit.json','console.log','state.txt']
            hashes={n:hashlib.sha256((remote/n).read_bytes()).hexdigest() for n in names}
            output=root/'results'
            def rsync(*args,**kwargs):
                for name in names:
                    dest=output/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(remote/name,dest)
            with patch('remote_rtio_build.remote_hashes',return_value=hashes),patch('remote_rtio_build.subprocess.run',side_effect=rsync):
                result=collect(job,output)
            self.assertEqual(result['status'],'REMOTE_VIVADO_FAILED')
            self.assertIn('build failed',(output/'console.log').read_text())
            self.assertFalse((output/'top.bit').exists())

    def test_modified_job_rejected_before_ssh(self):
        with tempfile.TemporaryDirectory() as tmp,patch('remote_rtio_build.ssh') as ssh:
            root=Path(tmp);source=self.fixture(root);job=root/'job';prepare(source,job,'build');(job/'run.sh').write_text('changed')
            with self.assertRaises(ValueError):submit(job)
            ssh.assert_not_called()

if __name__=='__main__':unittest.main()
