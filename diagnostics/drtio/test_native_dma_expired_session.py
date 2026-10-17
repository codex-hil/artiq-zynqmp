"""Expired-start failure is not an arbitrary kernel error; LGPL-3.0-or-later."""
import unittest
from native_dma_expired_session import expired_result
LOG='NATIVE_DDMA_EXPIRED_START_CAUGHT_PASS\nNATIVE_DDMA_PHYSICAL_PASS edges=8 width_mu=8000 period_mu=80000 first_delta_mu=1000120'
MASTER='DDMA playback rejected: DRTIO error: error playing back DMA trace on satellite #0'
AUX='''AUX_DDMA UPLOAD id=42 status=3 bytes=170
AUX_DDMA REPLY kind=177 id=42 succeeded=1
AUX_DDMA REPLY kind=181 id=42 succeeded=0
AUX_DDMA REPLY kind=181 id=42 succeeded=1
AUX_DDMA STATUS id=42 error=0
AUX_DDMA REPLY kind=179 id=42 succeeded=1'''
class ExpiredTests(unittest.TestCase):
    def test_exact_admission_rejection_and_recovery(self):
        self.assertEqual(expired_result(LOG,AUX,MASTER)['native_ddma_edges'],8)
    def test_wrong_evidence(self):
        cases=[(LOG.replace('NATIVE_DDMA_EXPIRED_START_CAUGHT_PASS',''),AUX,MASTER),
               (LOG,AUX.replace('succeeded=0','succeeded=1'),MASTER),
               (LOG,AUX.replace('bytes=170','bytes=1054'),MASTER),
               (LOG,AUX.replace('error=0','error=1'),MASTER),
               (LOG,AUX.replace('kind=179 id=42','kind=179 id=43'),MASTER),
               (LOG,AUX+'\nAUX_DDMA STATUS id=42 error=0',MASTER),
               (LOG,AUX,MASTER+' session aborted:'),(LOG+' ConnectionResetError',AUX,MASTER)]
        for log,aux,master in cases:
            with self.subTest(log=log,aux=aux,master=master),self.assertRaises(RuntimeError):expired_result(log,aux,master)
if __name__=='__main__':unittest.main()
