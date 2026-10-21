"""ELF payload and proof-binding controls; no bootgen/HW; LGPL-3.0-or-later."""
import hashlib,json,struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from package_local_candidate import match_worker,verify_proof


def elf(wide,machine,entry,segments):
    hs,ps=(64,56) if wide else (52,32);pos=hs+ps*len(segments);headers=[];payload=b''
    ident=b'\x7fELF'+bytes([2 if wide else 1,1,1])+b'\0'*9
    if wide:header=struct.pack('<HHIQQQIHHHHHH',2,machine,1,entry,hs,0,0,hs,ps,len(segments),0,0,0)
    else:header=struct.pack('<HHIIIIIHHHHHH',2,machine,1,entry,hs,0,0,hs,ps,len(segments),0,0,0)
    for address,data,memsize in segments:
        headers.append(struct.pack('<II6Q',1,7,pos,address,address,len(data),memsize,4) if wide else struct.pack('<8I',1,pos,address,address,len(data),memsize,7,4))
        pos+=len(data);payload+=data
    return ident+header+b''.join(headers)+payload


class PackageTests(unittest.TestCase):
    def test_exact_worker_and_mismatch(self):
        worker=elf(False,40,0x20200000,[(0x20200000,b'tested',64)])
        bridge=elf(True,183,0x20000000,[(0x20000000,b'boot',4),(0x20200000,b'tested',6)])
        self.assertEqual(match_worker(worker,bridge)['status'],'EXACT_TESTED_WORKER_PAYLOAD')
        for bad in (bridge[:-1]+b'X',bridge[:20],elf(True,183,0x20000000,[(0x20000000,b'boot',0x100000),(0x20200000,b'tested',6)])):
            with self.subTest(bad=bad[:20]),self.assertRaises((ValueError,struct.error)):match_worker(worker,bad)

    def test_proof_binding_and_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);artifact=root/'artifact';artifact.write_bytes(b'actual')
            m=root/'manifest.json';m.write_text(json.dumps(dict(cable='210383B7F02DA',files=dict(candidate_pl=dict(path=str(artifact),sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())))))
            proof=dict(status='PASS',restoration='PASS',hardware_executed=True,extended=True,cable='210383B7F02DA',manifest_sha256=hashlib.sha256(m.read_bytes()).hexdigest())
            p=root/'proof.json';p.write_text(json.dumps(proof));verify_proof(m,p)
            for key,value in [('restoration','FAIL'),('manifest_sha256','0'*64),('extended',False)]:
                bad=dict(proof);bad[key]=value;p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):verify_proof(m,p)
            p.write_text(json.dumps(proof));artifact.write_bytes(b'tampered')
            with self.assertRaises(ValueError):verify_proof(m,p)

if __name__=='__main__':unittest.main()
