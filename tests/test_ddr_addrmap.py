"""Recorded map inversion/collision guards, no HW; LGPL-3.0-or-later."""
import copy,json,sys,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
from decode_ddr_addrmap import geometry


class Addrmap(unittest.TestCase):
    def fixture(self):return json.loads((REPO/'evidence/ddrc-snapshot-2026-10-22/results.json').read_text())['registers']

    def test_recorded_single_rank_map(self):
        r=geometry(self.fixture());self.assertEqual((r['row_bits'],r['column_bits'],r['bank_bits'],r['bank_group_bits']),(16,10,2,1))
        self.assertEqual(r['programmed_bytes'],4*1024**3);self.assertEqual(r['hif_bits'],29)
        self.assertEqual(r['hif_to_dram']['3'],'bank_group0');self.assertFalse(r['destructive_test_allowed'])

    def test_highest_row_disabled_is_valid_smaller_geometry(self):
        r=self.fixture();r['ADDRMAP6']='0x0f070707'
        self.assertEqual(geometry(r)['programmed_bytes'],2*1024**3)

    def test_collisions_holes_grouped_rows_or_other_width_rejected(self):
        for name,value in [('ADDRMAP1','0x1f0901'),('ADDRMAP6','0x070f0707'),('ADDRMAP5','0x07070707'),('MSTR','0x81041010')]:
            r=self.fixture();r[name]=value
            with self.subTest(register=name),self.assertRaises(ValueError):geometry(r)

if __name__=='__main__':unittest.main()
