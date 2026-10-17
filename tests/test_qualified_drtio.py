"""Pinned launcher preflight tests, no board access; LGPL-3.0-or-later."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_qualified_drtio import validate,render

class QualifiedTests(unittest.TestCase):
    def fixture(self,directory):
        root=Path(directory);files=[]
        for name in ('runtime.bin','kasli/generated/genesys_drtio_master_v11/gateware/top.bit','proof.json','bit','csr','firmware','restore','cpu0','overlay/results.json'):
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps(dict(status='PASS',restoration='PASS')) if name=='proof.json' else 'artifact')
            files.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        digest=files[0]['sha256']
        observer={k:str(root/name) for k,name in dict(bitstream='bit',csr_map='csr',firmware='firmware',restore_bitstream='restore',cpu0='cpu0').items()}
        observer.update(native_ddma_catch=True,native_ddma_cursor=True,dma_cursor_overlay=str(root/'overlay'))
        return dict(schema=1,argv=['python',str(ROOT/'scripts/test_kasli03_netboot_hw.py'),
            '--download-runtime',str(root/'runtime.bin'),'--runtime-sha256',digest,
            '--build',str(root/'kasli'),'--sha256',digest,'--qualification',str(root/'proof.json')],
            artifacts=files,pass_proofs=[str(root/'proof.json')],observer=observer)

    def test_matching_profile_and_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=self.fixture(tmp);data,verified=validate(p,{})
            self.assertEqual(len(verified),9)
        self.assertEqual(render({'path':['{repo}/file']},{'repo':'/example'}),{'path':['/example/file']})

    def test_stale_missing_unpinned_digest_bad_proof_and_unguarded_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=self.fixture(tmp)
            variants=[]
            q=copy.deepcopy(p);q['artifacts'][0]['sha256']='0'*64;variants.append(q)
            q=copy.deepcopy(p);q['artifacts'][0]['path']=tmp+'/absent';variants.append(q)
            q=copy.deepcopy(p);q['artifacts']=q['artifacts'][1:];variants.append(q)
            q=copy.deepcopy(p);q['argv'][q['argv'].index('--runtime-sha256')+1]='f'*64;variants.append(q)
            q=copy.deepcopy(p);q['argv'][1]='/unlocked-programmer.py';variants.append(q)
            for q in variants:
                with self.subTest(profile=q),self.assertRaises(ValueError):validate(q,{})
            proof=Path(tmp)/'proof.json';proof.write_text(json.dumps(dict(status='FAIL',restoration='PASS')))
            p['artifacts'][2]['sha256']=hashlib.sha256(proof.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):validate(p,{})

    def test_default_only_preflights_and_execute_requires_restoration_pass(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from run_qualified_drtio import main
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);profile=root/'profile.json'
            profile.write_text(json.dumps(self.fixture(root/'artifacts')))
            output=root/'review'
            with patch('sys.argv',['runner','--profile',str(profile),'--output',str(output)]),\
                 patch('run_qualified_drtio.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='preflight',stderr='')) as run:
                main()
                self.assertEqual(run.call_count,1)
                self.assertEqual(run.call_args.args[0][-1],'--dry-run')
                self.assertFalse(json.loads((output/'review.json').read_text())['hardware_executed'])
            output=root/'execute'
            def child(argv,**kwargs):
                if argv[-1]=='--dry-run':return SimpleNamespace(returncode=0,stdout='',stderr='')
                results=output/'session/results.json';results.parent.mkdir()
                results.write_text(json.dumps(dict(status='PASS',restoration='FAIL')))
                return SimpleNamespace(returncode=0)
            with patch('sys.argv',['runner','--profile',str(profile),'--output',str(output),'--execute']),\
                 patch('run_qualified_drtio.subprocess.run',side_effect=child):
                with self.assertRaises(SystemExit) as error:main()
                self.assertEqual(error.exception.code,1)
                self.assertEqual(json.loads((output/'review.json').read_text())['status'],'WRAPPER_FAIL')

if __name__=='__main__':unittest.main()
