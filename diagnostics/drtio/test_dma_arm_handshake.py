"""No hardware; synthetic guarded-wrapper acknowledgements. LGPL-3.0-or-later."""
import json,tempfile,unittest
from pathlib import Path
from dma_arm_handshake import request,wait

class HandshakeTests(unittest.TestCase):
    def test_request_ack_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name);token=request(p)
            self.assertEqual(json.loads((p/'arm-request.json').read_text())['token'],token)
            with self.assertRaises(FileExistsError):request(p)
            (p/'arm-ack.json').write_text(json.dumps(dict(schema=1,token=token,status='ARMED_UART_VERIFIED',cycles=250000)))
            wait(p,token,timeout=0)
            with self.assertRaises(ValueError):request(p)
            with self.assertRaises(ValueError):wait(p,'stale',timeout=0)
    def test_missing_ack_times_out_and_invalid_ack_refused(self):
        with tempfile.TemporaryDirectory() as name:
            token=request(name)
            with self.assertRaises(TimeoutError):wait(name,token,timeout=0)
            (Path(name)/'arm-ack.json').write_text('{}')
            with self.assertRaises(ValueError):wait(name,token,timeout=0)
            with self.assertRaises(ValueError):wait(name,token,timeout=31)
