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
