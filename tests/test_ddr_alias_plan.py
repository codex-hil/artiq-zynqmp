"""Offline sparse-plan boundary controls; LGPL-3.0-or-later."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import plan_ddr_alias_probes as p


class AliasPlanTests(unittest.TestCase):
    def test_gap_is_never_flattened(self):
        self.assertEqual(p.physical(0x7fffffc0), 0x7fffffc0)
        self.assertEqual(p.physical(0x80000000), 0x800000000)
        self.assertEqual(p.physical(0xffffffc0), 0x87fffffc0)
        report = p.plan()
        addresses = [int(x['physical_start'], 16) for x in report['probes']]
        self.assertEqual(len(addresses), len(set(addresses)))
        for address in addresses:
            self.assertTrue(any(lo <= address and address + 64 <= hi for lo, hi in p.WINDOWS))
        self.assertFalse(report['destructive_test_allowed'])

    def test_address_bit_coverage(self):
        report = p.plan()
        offsets = {int(x['logical_offset'], 16) for x in report['probes']}
        self.assertIn(0, offsets)
        self.assertEqual({x['bit'] for x in report['logical_address_bit_pairs']}, set(range(6, 32)))
        for b in range(6, 32):
            self.assertIn(1 << b, offsets)

    def test_invalid_offsets_reject(self):
        for offset in (-64, 1, 0x100000000, True, '0'):
            with self.assertRaises(ValueError):
                p.physical(offset)


if __name__ == '__main__':
    unittest.main()
