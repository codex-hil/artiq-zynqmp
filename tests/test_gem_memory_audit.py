"""Linked memory audit rejection controls; LGPL-3.0-or-later."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_gem_memory import REQUIRED, symbols

class GemTests(unittest.TestCase):
    def fixture(self):
        return '\n'.join(f'{0x1000+i*0x100:016x} 0000000000000080 B {n}'
                         for i, n in enumerate(REQUIRED))
    def test_half_open_ranges(self):
        result = symbols(self.fixture())
        self.assertEqual(result[REQUIRED[0]]['end_exclusive'], 0x1080)
    def test_missing_duplicate_overlap_wrong_type_and_high_address(self):
        good = self.fixture()
        for bad in [good.split('\n', 1)[1], good + '\n' + good,
                    good.replace('0000000000001100', '0000000000001040'),
                    good.replace(' B ', ' T ', 1),
                    good.replace('0000000000001000', '0000000800000000')]:
            with self.assertRaises(ValueError):symbols(bad)

if __name__ == '__main__':unittest.main()
