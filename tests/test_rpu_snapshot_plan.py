"""RPU observation admission controls; LGPL-3.0-or-later."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from plan_rpu_snapshot import REGISTERS, decode, expression


class RpuTests(unittest.TestCase):
    def test_fields_never_admit_ddr(self):
        z = dict.fromkeys(REGISTERS, 0)
        r = decode([z, z])
        self.assertTrue(r['stable'])
        self.assertFalse(r['destructive_test_allowed'])
        self.assertEqual(r['ownership'], 'NOT_PROVEN')
        s = dict(z, global_control=8, r50_config=1, r51_status=32,
                 reset_control=6, clock_control=0x3000000)
        r = decode([z, s])
        self.assertFalse(r['stable'])
        row = r['samples'][1]
        self.assertTrue(row['split_bit'])
        self.assertTrue(row['cores'][0]['ncpuhalt_bit'])
        self.assertFalse(row['cores'][0]['reset_control_bit'])
        self.assertTrue(row['cores'][1]['reset_control_bit'])
        self.assertTrue(row['cores'][1]['nvalreset_bit'])
        self.assertTrue(row['amba_reset_bit'])
    def test_missing_extra_bool_range_reject(self):
        z = dict.fromkeys(REGISTERS, 0)
        for bad in [[], [z], [z, {}], [z, dict(z, extra=0)],
                    [z, dict(z, r50_status=True)], [z, dict(z, r50_status=-1)],
                    [z, dict(z, r50_status=1 << 32)]]:
            with self.assertRaises(ValueError):
                decode(bad)
    def test_macro_is_exact_and_unique(self):
        self.assertEqual(expression('#define X ((u32)0X00000008U)', 'X'), '0X00000008U')
        for text in ['', '#define X 1\n#define X 2']:
            with self.assertRaises(ValueError):
                expression(text, 'X')


if __name__ == '__main__':
    unittest.main()
