"""Offline receipt faults and explicit double-snapshot limits. LGPL-3.0-or-later."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'diagnostics/ddr'))
from pit_publication import accept


class Tests(unittest.TestCase):
    def record(self, complete=1, version=1, nonce=0x123456789abcdef0):
        return struct.pack('<IIQ8I', complete, version, nonce, *range(8))

    def test_complete_high_nonce_and_no_permit(self):
        data = self.record()
        result = accept(data, data, 0x123456789abcdef0)
        self.assertEqual(result['counters'][3]['second'], 7)
        self.assertFalse(result['physical_backend_ready'])
        self.assertFalse(result['destructive_test_allowed'])

    def test_every_changed_byte_rejected(self):
        data = self.record()
        for index in range(48):
            changed = bytearray(data); changed[index] ^= 1
            with self.assertRaises(ValueError):
                accept(data, bytes(changed), 0x123456789abcdef0)

    def test_uncommitted_wrong_identity_version_shape(self):
        for data in [self.record(complete=0), self.record(complete=2),
                     self.record(version=2), self.record(nonce=7),
                     self.record()[:-1], self.record() + b'\x00']:
            with self.assertRaises(ValueError): accept(data, data, 0x123456789abcdef0)
        data = bytearray(self.record())
        with self.assertRaises(ValueError): accept(data, data, 0x123456789abcdef0)

    def test_double_sampling_cannot_detect_aba_or_stale_visibility(self):
        # An intervening replacement or unseen writes can leave equal snapshots.
        # Acceptance deliberately retains no hardware/visibility admission.
        old = self.record()
        result = accept(old, old, 0x123456789abcdef0)
        self.assertIn('unqualified', result['publication'])
        self.assertIsNone(result['elapsed_ticks'])


if __name__ == '__main__':
    unittest.main()
