"""Session/image/sample binding and no sleep-proof controls. LGPL-3.0-or-later."""
import hashlib
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'diagnostics/ddr'))
from pit_terminal_receipt import FORMAT, MAGIC, accept

IMAGE = '12' * 32
SAMPLES = struct.pack('<IIQ8I', 1, 1, 7, *range(8))


def record(status=4, samples=SAMPLES, **changes):
    fields = dict(commit=1, magic=MAGIC, version=1, status=status, nonce=7,
                  checked=0x80000104, final=0x80000104, image=bytes.fromhex(IMAGE),
                  sample=hashlib.sha256(samples).digest() if samples is not None else bytes(32))
    fields.update(changes)
    return FORMAT.pack(*fields.values())


class Tests(unittest.TestCase):
    def test_complete_is_not_sleep_or_hardware_proof(self):
        data = record(); result = accept(data, data, 7, IMAGE, SAMPLES)
        self.assertEqual(FORMAT.size, 96)
        self.assertEqual(result['status'], 'CAPTURE_COMPLETE')
        self.assertFalse(result['sleep_proven'])
        self.assertFalse(result['hardware_executed'])
        self.assertFalse(result['destructive_test_allowed'])

    def test_errors_and_commit_can_coexist(self):
        for status in (1, 2, 3):
            for samples in (None, SAMPLES):
                data = record(status, samples, final=0x80000106)
                result = accept(data, data, 7, IMAGE, samples)
                self.assertIsNone(result['samples'])
                self.assertFalse(result['sleep_proven'])

    def test_wrong_binding_or_claim_rejected(self):
        data = record()
        for args in [(data, data, 8, IMAGE, SAMPLES), (data, data, 7, '34'*32, SAMPLES),
                     (data, data, 7, IMAGE, None), (data, data, 7, IMAGE, bytes(48)),
                     (data, data[:-1], 7, IMAGE, SAMPLES), (bytearray(data), data, 7, IMAGE, SAMPLES)]:
            with self.assertRaises(ValueError): accept(*args)
        for changes in [dict(commit=0), dict(magic=0), dict(version=2), dict(status=0),
                        dict(status=5), dict(final=0x80000106), dict(checked=0x80000106)]:
            bad = record(**changes)
            with self.assertRaises(ValueError): accept(bad, bad, 7, IMAGE, SAMPLES)
        for image in ('0'*64, 'AB'*32, '', True):
            with self.assertRaises(ValueError): accept(data, data, 7, image, SAMPLES)

    def test_sample_alone_or_wrong_nonce_never_terminal_receipt(self):
        with self.assertRaises(ValueError): accept(SAMPLES, SAMPLES, 7, IMAGE, SAMPLES)
        wrong = struct.pack('<IIQ8I', 1, 1, 8, *range(8))
        # Even a matching hash cannot override the sample's mismatched session.
        data = record(samples=wrong)
        with self.assertRaises(ValueError): accept(data, data, 7, IMAGE, wrong)


if __name__ == '__main__':
    unittest.main()
