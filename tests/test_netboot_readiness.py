"""Connect-only bounded readiness controls. LGPL-3.0-or-later."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from netboot_readiness import wait

class ReadinessTests(unittest.TestCase):
    def test_delayed_success_and_deadline(self):
        now=[0.0];calls=[]
        def sleep(seconds):now[0]+=seconds
        def connect(timeout):
            calls.append(timeout);now[0]+=timeout
            if len(calls)<3:raise TimeoutError('not ready')
            return 'retained connection'
        result,connection=wait(connect,15,clock=lambda:now[0],sleep=sleep)
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(connection,'retained connection')
        self.assertEqual(len(result['attempts']),3)
        now[0]=0
        def fail(timeout):now[0]+=timeout;raise TimeoutError('not ready')
        result,connection=wait(fail,5,clock=lambda:now[0],sleep=sleep)
        self.assertEqual(result['status'],'FAIL')
        self.assertLessEqual(result['elapsed_seconds'],5)
        with self.assertRaises(ValueError):wait(connect,46)
    def test_no_payload_action_or_unbounded_fast_retry(self):
        now=[0.0]
        def fail(timeout):raise ConnectionRefusedError('refused')
        def sleep(seconds):now[0]+=seconds
        result,connection=wait(fail,45,clock=lambda:now[0],sleep=sleep)
        self.assertEqual(len(result['attempts']),15)
