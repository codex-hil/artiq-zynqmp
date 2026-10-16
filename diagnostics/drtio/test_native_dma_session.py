"""Native DDMA preflight negatives, no hardware; LGPL-3.0-or-later."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from native_dma_session import validate


class ValidationTests(unittest.TestCase):
    def test_failed_proof_and_host_arming_rejected(self):
        root=Path(__file__).parent/'aux_protocol'
        names=('ddma_runtime.h','ddma_service.h','ddma_store.h','ddma_backend.h','ddma_a53.h','ddma_codec.h')
        fw={'ddma_sources':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}}
        s=SimpleNamespace(config={'native_ddma_mode':'idle'},host_dma_test=False,
            dio_test=True,snapshot_test=True,result={'bit_sha256':'bit','firmware_sha256':'fw'})
        validate(s,fw)
        s.config['native_ddma_rejection']=True
        with self.assertRaises(ValueError):validate(s,fw)
        s.config.pop('native_ddma_rejection')
        s.host_dma_test=True
        with self.assertRaises(ValueError):validate(s,fw)
        s.host_dma_test=False;s.config['native_ddma_mode']='playback'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'proof.json';s.config['ddma_idle_qualification']=str(p)
            p.write_text(json.dumps({'status':'FAIL','restoration':'PASS'}))
            with self.assertRaises(ValueError):validate(s,fw)
            proof={'status':'PASS','restoration':'PASS','external_rx':dict(restoration='PASS',dio_loopback='PASS',tsc_snapshot='PASS',bit_sha256='bit',firmware_sha256='fw')}
            p.write_text(json.dumps(proof));validate(s,fw)
            proof['external_rx']['firmware_sha256']='other';p.write_text(json.dumps(proof))
            with self.assertRaises(ValueError):validate(s,fw)


class LifecycleTests(unittest.TestCase):
    def test_physical_and_aux_conservation(self):
        from native_dma_session import lifecycle_result
        log='\n'.join(f'NATIVE_DDMA_LIFECYCLE_PASS phase={p} replay={r} edges=8 width_mu={8000*(p+1)} period_mu={80000+p*40000} first_delta_mu=1000120' for p in range(3) for r in range(3))
        lines=[]
        for id in (1,2,1):
            lines.append(f'AUX_DDMA REPLY kind=177 id={id} succeeded=1')
            for _ in range(3):
                lines.extend([f'AUX_DDMA REPLY kind=181 id={id} succeeded=1',f'AUX_DDMA STATUS id={id} error=0'])
            lines.append(f'AUX_DDMA REPLY kind=179 id={id} succeeded=1')
        text='\n'.join(lines)
        self.assertEqual(lifecycle_result(log,text)['native_ddma_edges'],72)
        for badlog,badtext in ((log.replace('width_mu=8000','width_mu=8008'),text),
                (log,text.replace('error=0','error=1',1)),(log,'\n'.join(lines[:-1]))):
            with self.assertRaises(RuntimeError):lifecycle_result(badlog,badtext)


class FragmentTests(unittest.TestCase):
    def test_two_exact_fragments_and_physical_capture(self):
        from native_dma_session import fragment_result
        log='NATIVE_DDMA_FRAGMENT_PASS edges=58 width_mu=8000 period_mu=16000 first_delta_mu=1000120'
        lines=['AUX_DDMA UPLOAD id=42 status=1 bytes=1010','AUX_DDMA REPLY kind=177 id=42 succeeded=1',
            'AUX_DDMA UPLOAD id=42 status=2 bytes=10','AUX_DDMA REPLY kind=177 id=42 succeeded=1',
            'AUX_DDMA REPLY kind=181 id=42 succeeded=1','AUX_DDMA STATUS id=42 error=0',
            'AUX_DDMA REPLY kind=179 id=42 succeeded=1']
        text='\n'.join(lines)
        self.assertEqual(fragment_result(log,text)['native_ddma_edges'],58)
        for bad in (text.replace('bytes=10\n','bytes=11\n'),text.replace('error=0','error=1'),
                    '\n'.join(lines[:-1]),text.replace('status=2','status=0')):
            with self.assertRaises(RuntimeError):fragment_result(log,bad)


class LongLifecycleTests(unittest.TestCase):
    def test_all_fragment_and_replay_counts_required(self):
        from native_dma_session import long_lifecycle_result
        log='\n'.join(f'NATIVE_DDMA_LONG_LIFECYCLE_PASS phase={p} replay={r} edges=58 width_mu={4000+p*2000} period_mu={16000+p*4000} first_delta_mu=1000120' for p in range(3) for r in range(3))
        lines=[]
        for id in (1,2,1):
            for status,length in ((1,1010),(2,10)):
                lines.extend([f'AUX_DDMA UPLOAD id={id} status={status} bytes={length}',f'AUX_DDMA REPLY kind=177 id={id} succeeded=1'])
            for _ in range(3):lines.extend([f'AUX_DDMA REPLY kind=181 id={id} succeeded=1',f'AUX_DDMA STATUS id={id} error=0'])
            lines.append(f'AUX_DDMA REPLY kind=179 id={id} succeeded=1')
        text='\n'.join(lines)
        self.assertEqual(long_lifecycle_result(log,text)['native_ddma_edges'],522)
        for badlog,badtext in ((log.replace('width_mu=4000','width_mu=4008'),text),
                (log,text.replace('bytes=1010','bytes=1009',1)),(log,text.replace('error=0','error=1',1)),
                (log,'\n'.join(lines[:-1]))):
            with self.assertRaises(RuntimeError):long_lifecycle_result(badlog,badtext)
