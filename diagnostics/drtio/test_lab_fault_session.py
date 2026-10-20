"""Synthetic parent orchestration; no serial/network/JTAG. LGPL-3.0-or-later."""
import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from lab_fault_session import probe
from test_active_dma_fault_evidence import AUX,KERNEL

class UART:
    in_waiting=0
    def read(self,n):return b''
class SessionTests(unittest.TestCase):
    def test_existing_parent_context_and_evidence_wiring(self):
        with tempfile.TemporaryDirectory() as name:
            out=Path(name);(out/'dio-device-db.py').write_text('device_db = {}\n')
            session=SimpleNamespace(lab_fault_mode='active',lease_fd=1,output=out,result={},
                config=dict(artiq_python='python3',dma_cursor_overlay='/synthetic-overlay'))
            text='AUX_DDMA LAB_BASELINE ar=0 rlast=0 edges=6\n'+AUX.replace(
                'AUX_DDMA LAB_COMPLETE','AUX_DDMA LAB_METRICS ar=2 rlast=2 edges=6\nAUX_DDMA LAB_COMPLETE')
            text=text.replace('accepted=3','accepted=1').replace('completed=2','completed=0').replace('completed=3','completed=1')
            raw=bytearray()
            def child(*args,**kwargs):
                self.assertEqual(kwargs['lease_fd'],1)
                self.assertEqual(kwargs['timeout'],60)
                raw.extend(text.encode());return KERNEL
            with patch('lab_fault_session.idle_probe',return_value={'lab_idle_samples':[{'epoch':7,'edges':6}]}),\
                 patch('lab_fault_session.run_child',side_effect=child),\
                 patch('lab_fault_session.post_fault',return_value={'lab_fault_poststate':'PASS'}):
                probe(session,'synthetic-host',UART(),raw)
            self.assertEqual(session.result['lab_active_fault'],'PASS')
            self.assertNotIn('restoration',session.result)
            self.assertEqual(session.result['lab_active_evidence']['restoration'],'PARENT_MUST_VERIFY')
    def test_requires_active_parent_lease_context(self):
        for session in [SimpleNamespace(config={},output=Path('.'),lab_fault_mode='idle'),
                        SimpleNamespace(config={},output=Path('.'),lab_fault_mode='active')]:
            with self.assertRaises(ValueError):probe(session,'host',UART(),bytearray())
