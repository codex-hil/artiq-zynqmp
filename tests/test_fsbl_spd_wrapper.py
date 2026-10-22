"""SPD wrapper artifact pins and restoration on parser rejection; LGPL-3.0-or-later."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
from test_candidate_runtime_hw import spd_preflight,SPD_SCRIPTS,lifecycle
from decode_fsbl_spd_log import extract

class SPDWrapper(unittest.TestCase):
    def fixture(self):
        elf=Path('/srv/codex-hil-data/artiq-zynqmp/build-vivado/fsbl-spd-dump-20261022/app/build/zynqmp_fsbl.elf')
        item=dict(path=str(elf),sha256=hashlib.sha256(elf.read_bytes()).hexdigest())
        manifest=dict(fsbl_spd=dict(fsbl_sha256=item['sha256'],script_sha256={n:hashlib.sha256((REPO/n).read_bytes()).hexdigest() for n in SPD_SCRIPTS}))
        return manifest,dict(candidate_fsbl=item)
    def test_real_artifact_pin_and_changed_script_rejection(self):
        m,f=self.fixture();spd_preflight(m,f)
        m['fsbl_spd']['script_sha256']['scripts/decode_fsbl_spd_log.py']='0'*64
        with self.assertRaisesRegex(ValueError,'Changed SPD'):spd_preflight(m,f)
    def test_missing_manifest_and_wrong_fsbl_pin_rejected(self):
        m,f=self.fixture()
        with self.assertRaises(ValueError):spd_preflight({},f)
        m['fsbl_spd']['fsbl_sha256']='0'*64
        with self.assertRaises(ValueError):spd_preflight(m,f)
    def test_parser_rejection_always_runs_restoration(self):
        seen=[]
        def cycle(role):
            seen.append(role)
            if role=='candidate':extract('SPD_BASE_BEGIN bytes=128\ntruncated')
            return 'restored'
        r=lifecycle(cycle)
        self.assertEqual(r['status'],'FAIL');self.assertEqual(r['restoration'],'PASS')
        self.assertEqual(seen,['candidate','restore'])

if __name__=='__main__':unittest.main()
