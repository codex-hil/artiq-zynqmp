"""Connection loss must not count as structured DMAError; LGPL-3.0-or-later."""
import unittest
from structured_dma_evidence import structured_rejection_result

HOST='DMAError: Failed to upload distributed DMA trace'
MASTER='DDMA upload rejected: error adding DMA trace on satellite #0'

class StructuredTests(unittest.TestCase):
    def test_structured_exception(self):
        self.assertEqual(structured_rejection_result(HOST,MASTER,'')['native_ddma_host_exception'],'DMAError')

    def test_missing_error_transport_loss_abort_and_unclean_recovery(self):
        for h,m,r in [('timeout',MASTER,''),(HOST,'link lost',''),
                      (HOST+' ConnectionResetError',MASTER,''),
                      (HOST,MASTER+' session aborted: error',''),
                      (HOST,MASTER,'Previous kernel did not cleanly finish')]:
            with self.subTest(host=h,master=m,recovery=r),self.assertRaises(RuntimeError):structured_rejection_result(h,m,r)

if __name__=='__main__':unittest.main()
