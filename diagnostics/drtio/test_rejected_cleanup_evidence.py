"""Reject missing/wrong/extra cleanup or playback evidence; LGPL-3.0-or-later."""
import unittest
from rejected_cleanup_evidence import cleanup_recovery_result

TEXT='''AUX_DDMA REPLY kind=179 id=42 succeeded=1
AUX_DDMA UPLOAD id=43 status=3 bytes=170
AUX_DDMA REPLY kind=177 id=43 succeeded=1
AUX_DDMA REPLY kind=181 id=43 succeeded=1
AUX_DDMA STATUS id=43 error=0
AUX_DDMA REPLY kind=179 id=43 succeeded=1'''

class CleanupEvidenceTests(unittest.TestCase):
    def test_exact_sequence_distinct_or_reused_id(self):
        for text in (TEXT,TEXT.replace('id=43','id=42')):
            self.assertEqual(cleanup_recovery_result(text,'',42)['native_ddma_rejected_cleanup'],'PASS')

    def test_missing_wrong_identity_nack_extra_reply_and_master_error(self):
        cases=[(TEXT.split('\n',1)[1],''),(TEXT.replace('id=42','id=44'),''),
            (TEXT.replace('succeeded=1','succeeded=0',1),''),
            (TEXT.replace('error=0','error=1'),''),
            (TEXT+'\nAUX_DDMA REPLY kind=179 id=42 succeeded=1',''),
            (TEXT,'Error erasing trace on DMA: error erasing DMA trace on satellite #0')]
        for text,master in cases:
            with self.subTest(text=text,master=master),self.assertRaises(RuntimeError):cleanup_recovery_result(text,master,42)

if __name__=='__main__':unittest.main()
