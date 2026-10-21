"""Candidate lifecycle/lease negative controls, no hardware; LGPL-3.0-or-later."""
import copy,fcntl,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from test_candidate_runtime_hw import lifecycle,lease,bounded,preflight,REPO

class CandidateTests(unittest.TestCase):
    def test_success_restores_and_failure_restores(self):
        for fail in (False,True):
            seen=[]
            def cycle(name):
                seen.append(name)
                if fail and name=='candidate':raise RuntimeError('candidate failure')
                return '192.0.2.1'
            r=lifecycle(cycle)
            self.assertEqual(seen,['candidate','restore'])
            self.assertEqual(r['restoration'],'PASS')
            self.assertEqual(r['status'],'FAIL' if fail else 'PASS')

    def test_restore_failure_never_passes(self):
        def cycle(name):
            if name=='restore':raise RuntimeError('restore failure')
            return '192.0.2.1'
        r=lifecycle(cycle);self.assertEqual(r['status'],'FAIL');self.assertEqual(r['restoration'],'FAIL')

    def test_interrupt_still_restores(self):
        seen=[]
        def cycle(name):
            seen.append(name)
            if name=='candidate':raise KeyboardInterrupt()
            return '192.0.2.1'
        r=lifecycle(cycle);self.assertEqual(seen,['candidate','restore']);self.assertEqual(r['status'],'FAIL')

    def test_busy_prevents_body_and_lease_released(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'board.lock'
            with lease(path):
                with self.assertRaisesRegex(RuntimeError,'BUSY'):
                    with lease(path):self.fail('busy lease entered body')
            with lease(path) as fd:self.assertGreaterEqual(fd.fileno(),0)

    def test_timeout_child_killed_and_lock_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'board.lock'
            with lease(path) as fd:
                with self.assertRaises(subprocess.TimeoutExpired):
                    bounded([sys.executable,'-c','import time; print("started",flush=True); time.sleep(5)'],.1,os.environ.copy(),fd.fileno())
                with self.assertRaisesRegex(RuntimeError,'BUSY'):
                    with lease(path):self.fail('lease lost on timeout')

    def test_stale_artifact_rejected_before_report_check(self):
        m=json.loads((REPO/'evidence/candidate-jtag-plan-2026-10-21/inputs.json').read_text())
        m=copy.deepcopy(m);m['files']['candidate_pl']['sha256']='0'*64
        with patch('test_candidate_runtime_hw.check') as check:
            with self.assertRaisesRegex(ValueError,'hash mismatch'):preflight(m)
            check.assert_not_called()

if __name__=='__main__':unittest.main()
