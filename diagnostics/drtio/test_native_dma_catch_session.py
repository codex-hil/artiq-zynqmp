"""Same-kernel catch requires both exact AUX paths; LGPL-3.0-or-later."""
import unittest
from native_dma_catch_session import catch_result
LOG='NATIVE_DDMA_CAUGHT_PASS\nNATIVE_DDMA_PHYSICAL_PASS edges=8 width_mu=8000 period_mu=80000 first_delta_mu=1000120'
AUX='''AUX_DDMA UPLOAD id=42 status=1 bytes=1010
AUX_DDMA REPLY kind=177 id=42 succeeded=1
AUX_DDMA UPLOAD id=42 status=2 bytes=44
AUX_DDMA REPLY kind=177 id=42 succeeded=0
AUX_DDMA REPLY kind=179 id=42 succeeded=1
AUX_DDMA UPLOAD id=43 status=3 bytes=170
AUX_DDMA REPLY kind=177 id=43 succeeded=1
AUX_DDMA REPLY kind=181 id=43 succeeded=1
AUX_DDMA STATUS id=43 error=0
AUX_DDMA REPLY kind=179 id=43 succeeded=1'''
MASTER='DDMA upload rejected: DRTIO error: error adding DMA trace on satellite #0'
class CatchTests(unittest.TestCase):
    def test_exact_catch_and_recovery(self):
        self.assertEqual(catch_result(LOG,AUX,MASTER)['native_ddma_edges'],8)
    def test_missing_catch_wrong_width_no_nack_no_cleanup_and_abort(self):
        cases=[(LOG.replace('NATIVE_DDMA_CAUGHT_PASS',''),AUX,MASTER),
               (LOG.replace('width_mu=8000','width_mu=8008'),AUX,MASTER),
               (LOG,AUX.replace('succeeded=0','succeeded=1'),MASTER),
               (LOG,AUX.replace('kind=179 id=42 succeeded=1','kind=179 id=42 succeeded=0'),MASTER),
               (LOG,AUX,MASTER+' session aborted:'),
               (LOG+' ConnectionResetError',AUX,MASTER)]
        for log,aux,master in cases:
            with self.subTest(log=log,aux=aux,master=master),self.assertRaises(RuntimeError):catch_result(log,aux,master)
if __name__=='__main__':unittest.main()
