"""DDR bank parser guards; no hardware; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from plan_ddr_diagnostic import banks


class DDRPlan(unittest.TestCase):
    def text(self,low='0 0 0 0x7ff00000 0 0x7ff00000 0 0x100000',high='8 0 0 0x80000000'):
        return f'psu_ddr_0: memory@0 {{reg=<{low}>;}}; psu_ddr_1: memory@800000000 {{reg=<{high}>;}};'

    def test_noncontiguous_banks_and_adjacent_low_segments(self):
        self.assertEqual(banks(self.text()),[(0,0x80000000),(0x800000000,0x880000000)])

    def test_overlap_zero_misalignment_and_missing_rejected(self):
        for text in (self.text(high='0 64 0 64'),self.text(high='8 0 0 0'),self.text(high='8 1 0 64'),self.text(high='8 0 0'),self.text().replace('psu_ddr_1','other')):
            with self.subTest(text=text),self.assertRaises(ValueError):banks(text)

if __name__=='__main__':unittest.main()
