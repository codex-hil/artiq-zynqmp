"""Rejection evidence must identify ACK/NACK, no playback; LGPL-3.0-or-later."""
import unittest
from native_dma_reject_session import rejection_result

AUX='''AUX_DDMA UPLOAD id=42 status=1 bytes=1010
AUX_DDMA REPLY kind=177 id=42 succeeded=1
AUX_DDMA UPLOAD id=42 status=2 bytes=44
AUX_DDMA REPLY kind=177 id=42 succeeded=0
'''
MASTER='session error: drtio aux error: error adding DMA trace on satellite #0'

class RejectionTests(unittest.TestCase):
    def test_exact_rejection(self):
        r=rejection_result(1,'host session closed',AUX,MASTER)
        self.assertEqual(r['native_ddma_rejected_bytes'],1054)

    def test_false_success_timeout_fault_and_playback_rejected(self):
        bad=[(0,'',AUX,MASTER),(-9,'',AUX,MASTER),
             (1,'NATIVE_DDMA_OVERSIZE_UNEXPECTED_ACCEPT',AUX,MASTER),
             (1,'timeout',AUX,'link lost'),
             (1,'',AUX.replace('bytes=44','bytes=10'),MASTER),
             (1,'',AUX.replace('status=2','status=3'),MASTER),
             (1,'',AUX.replace('id=42 status=2','id=43 status=2'),MASTER),
             (1,'',AUX.replace('succeeded=0','succeeded=1'),MASTER),
             (1,'',AUX+'AUX_DDMA REPLY kind=181 id=42 succeeded=1\n',MASTER),
             (1,'',AUX+'AUX_DDMA STATUS id=42 error=0\n',MASTER),
             (1,'',AUX+'AUX_FW PANIC',MASTER)]
        for row in bad:
            with self.subTest(row=row),self.assertRaises(RuntimeError):rejection_result(*row)

if __name__=='__main__':unittest.main()
