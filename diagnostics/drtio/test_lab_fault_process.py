"""Synthetic subprocess and fake UART only; LGPL-3.0-or-later."""
import os,sys,tempfile,unittest
from pathlib import Path
from lab_fault_process import run

CHILD='''import json,os,time
from pathlib import Path
p=Path(os.environ['ARTIQ_DDMA_LAB_HANDSHAKE'])
r=dict(schema=1,token='a'*32,request='arm-native-ddma-delay',cycles=250000)
(p/'arm-request.json').write_text(json.dumps(r))
for i in range(200):
 if (p/'arm-ack.json').exists():break
 time.sleep(.01)
else:raise RuntimeError('no ack')
print('SYNTHETIC_CHILD_PASS')
'''
class UART:
    in_waiting=0
    timeout=.2
    def __init__(self,reply=b'AUX_DDMA LAB_ARM result=0 cycles=250000\r\n'):
        self.writes=[];self.reply=reply;self.pending=b''
    def write(self,b):self.writes.append(b);self.pending=self.reply;return len(b)
    def read(self,n):b=self.pending;self.pending=b'';return b

class PumpTests(unittest.TestCase):
    def test_success_one_arm_complete_ack_and_child_log(self):
        with tempfile.TemporaryDirectory() as name,open(os.devnull,'rb') as lease:
            p=Path(name);u=UART();raw=bytearray()
            result=run([sys.executable,'-c',CHILD],directory=p/'handshake',log=p/'child.log',uart=u,raw=raw,lease_fd=lease.fileno(),timeout=3)
            self.assertIn('SYNTHETIC_CHILD_PASS',result);self.assertEqual(u.writes,[b'F'])
            self.assertTrue((p/'handshake/arm-ack.json').exists())
    def test_refused_arm_or_timeout_never_acknowledges(self):
        for reply in [b'AUX_DDMA LAB_ARM result=-1 cycles=250000\n',b'']:
            with tempfile.TemporaryDirectory() as name,open(os.devnull,'rb') as lease:
                p=Path(name);u=UART(reply)
                with self.assertRaises((RuntimeError,TimeoutError)):
                    run([sys.executable,'-c',CHILD],directory=p/'handshake',log=p/'child.log',uart=u,raw=bytearray(),lease_fd=lease.fileno(),timeout=.3)
                self.assertFalse((p/'handshake/arm-ack.json').exists())
    def test_bad_request_no_uart_write(self):
        with tempfile.TemporaryDirectory() as name,open(os.devnull,'rb') as lease:
            p=Path(name);u=UART()
            with self.assertRaises(ValueError):
                run([sys.executable,'-c',CHILD.replace("token='a'*32","token='bad'")],directory=p/'handshake',log=p/'child.log',uart=u,raw=bytearray(),lease_fd=lease.fileno(),timeout=3)
            self.assertFalse(u.writes)
