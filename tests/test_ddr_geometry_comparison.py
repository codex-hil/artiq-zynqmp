"""Synthetic SPD versus captured controller agreement; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
from compare_ddr_geometry import compare

class GeometryComparison(unittest.TestCase):
    def fixture(self):
        d=bytearray(128);d[2]=12;d[3]=3;d[4]=0x45;d[5]=0x21;d[12]=2;d[13]=3
        return d,(REPO/'evidence/ddrc-snapshot-2026-10-22/snapshot.log').read_text()
    def test_matching_synthetic_spd_never_grants_physical_proof(self):
        d,s=self.fixture();r=compare(d,s)
        self.assertTrue(r['geometry_matches']);self.assertEqual(r['crc'],'NOT_VERIFIED')
        self.assertEqual(r['physical_capacity'],'NOT_VERIFIED');self.assertFalse(r['destructive_test_allowed'])
    def test_valid_smaller_module_and_two_ranks_rejected(self):
        d,s=self.fixture();d[4]=0x44;d[5]=0x19
        r=compare(d,s);self.assertFalse(r['geometry_matches']);self.assertFalse(r['fields']['row_bits']['equal'])
        d,s=self.fixture();d[12]|=8
        r=compare(d,s);self.assertFalse(r['geometry_matches']);self.assertFalse(r['fields']['ranks']['equal'])
    def test_missing_or_invalid_input_rejected(self):
        d,s=self.fixture()
        for raw,snapshot in [(d[:20],s),(d,'')]:
            with self.assertRaises(ValueError):compare(raw,snapshot)
