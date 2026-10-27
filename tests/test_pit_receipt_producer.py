"""Derived metadata and stale/caller-promotion negatives. LGPL-3.0-or-later."""
import hashlib
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'diagnostics/ddr'))
from pit_receipt_producer import ReceiptProducer
from pit_terminal_receipt import accept

IMAGE = b'offline image bytes, not hardware or bootable ELF'
SAMPLES = struct.pack('<IIQ8I', 1, 1, 7, *range(8))


class Tests(unittest.TestCase):
    def producer(self):
        p = ReceiptProducer(IMAGE, 7); p.checked_irq(0x106, 0x104); return p

    def test_content_hashes_derived_and_round_trip(self):
        p=self.producer();p.sample_result('COMPLETE',SAMPLES);data=p.finish(0x104)
        result=accept(data,data,7,hashlib.sha256(IMAGE).hexdigest(),SAMPLES)
        self.assertEqual(result['status'],'CAPTURE_COMPLETE')
        self.assertFalse(result['sleep_proven'])
        with self.assertRaises(ValueError):accept(data,data,7,hashlib.sha256(IMAGE+b'changed').hexdigest(),SAMPLES)
        with self.assertRaises(ValueError):p.finish(0x104)

    def test_failure_or_late_irq_never_promoted(self):
        for outcome,raw,final,status in [('READ_FAILED',None,0x104,'READ_FAILED'),
            ('PUBLICATION_UNKNOWN',SAMPLES,0x104,'PUBLICATION_UNKNOWN'),
            ('COMPLETE',SAMPLES,0x106,'IRQ_UNPROVEN'),('COMPLETE',SAMPLES,None,'IRQ_UNPROVEN')]:
            p=self.producer();p.sample_result(outcome,raw);data=p.finish(final)
            result=accept(data,data,7,hashlib.sha256(IMAGE).hexdigest(),raw)
            self.assertEqual(result['status'],status)
            self.assertFalse(result['destructive_test_allowed'])

    def test_no_initial_irq_proof_no_samples(self):
        for before,after in [(None,None),(0x106,0x106),(None,0x104)]:
            p=ReceiptProducer(IMAGE,7);p.checked_irq(before,after)
            with self.assertRaises(ValueError):p.sample_result('COMPLETE',SAMPLES)
            p.sample_result('IRQ_UNPROVEN');data=p.finish(None)
            self.assertEqual(accept(data,data,7,hashlib.sha256(IMAGE).hexdigest())['status'],'IRQ_UNPROVEN')

    def test_order_types_and_wrong_sample_identity(self):
        p=ReceiptProducer(IMAGE,7)
        with self.assertRaises(ValueError):p.sample_result('COMPLETE',SAMPLES)
        with self.assertRaises(ValueError):p.finish(0x104)
        p.checked_irq(0x106,0x104)
        with self.assertRaises(ValueError):p.checked_irq(0x106,0x104)
        for outcome,raw in [('CAPTURE_COMPLETE',SAMPLES),('READ_FAILED',SAMPLES),
                            ('COMPLETE',None),('COMPLETE',bytearray(SAMPLES)),
                            ('COMPLETE',struct.pack('<IIQ8I',1,1,8,*range(8)))]:
            with self.assertRaises(ValueError):p.sample_result(outcome,raw)
        p.sample_result('COMPLETE',SAMPLES)
        with self.assertRaises(ValueError):p.finish(True)
        with self.assertRaises(ValueError):p.finish(0x104)
        for image in (b'',bytearray(IMAGE),bytes(1024*1024+1)):
            with self.assertRaises(ValueError):ReceiptProducer(image,7)


if __name__=='__main__':unittest.main()
