"""Synthetic parser fixtures only; LGPL-3.0-or-later."""
import unittest
from active_dma_fault_evidence import validate
AUX='''AUX_DDMA LAB_ARM result=0 cycles=250000
AUX_DDMA REPLY kind=181 id=42 succeeded=1
AUX_DDMA LAB_ACTIVE id=42 accepted=3 completed=2 triggers=1
AUX_DDMA STATUS id=42 error=1
AUX_DDMA LAB_COMPLETE id=42 raw=4 channel=0 timestamp=0000000000002580 accepted=3 completed=3 faulted=1
'''
KERNEL='NATIVE_DDMA_ACTIVE_UNDERFLOW_CAUGHT_PASS'
class EvidenceTests(unittest.TestCase):
    def check(self,aux=AUX,kernel=KERNEL,**kw):
        args=dict(expected_timestamp=9600,edge_before=10,edge_after=10,read_requests=2,read_completions=2);args.update(kw)
        return validate(aux,kernel,**args)
    def test_synthetic_positive(self):self.assertEqual(self.check()['status'],'ACTIVE_FAULT_EVIDENCE_PASS')
    def test_negative_controls(self):
        variants=[AUX.replace('succeeded=1','succeeded=0'),AUX.replace('raw=4','raw=0'),
            AUX.replace('error=1','error=0'),AUX.replace('completed=3','completed=2'),
            AUX.replace('timestamp=0000000000002580','timestamp=0000000000002588'),
            AUX.replace('faulted=1','faulted=0'),AUX+AUX,AUX+'AUX_DDMA REPLY kind=181 id=42 succeeded=0\n',
            '\n'.join(reversed(AUX.splitlines())),AUX+'AUX_DDMA FAIL_CLOSED\n']
        for value in variants:
            with self.subTest(value=value),self.assertRaises(ValueError):self.check(aux=value)
        for kwargs in [dict(edge_after=11),dict(read_completions=1),dict(read_requests=0,read_completions=0),dict(edge_before=True),dict(kernel='DMAError')]:
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):self.check(**kwargs)
