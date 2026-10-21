"""Board substitution/lease scope controls, no hardware. LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from kasli_board_identity import identity,locks
class BoardTests(unittest.TestCase):
    def test_kasli01_avoids_secure_link_leases(self):
        self.assertEqual(identity('KASLI01')['dna'],0x007865085f704854)
        names=locks('KASLI01',True)
        self.assertEqual(len(names),2)
        self.assertTrue(any('genesys-' in n for n in names))
        self.assertFalse(any('KASLI03' in n or 'KASLI04' in n for n in names))
        self.assertNotEqual(identity('KASLI01')['mac'],identity('KASLI03')['mac'])
    def test_legacy_scope_preserved_unknown_board_refused(self):
        self.assertEqual(len(locks('KASLI03',True)),4)
        with self.assertRaises(ValueError):locks('KASLI02',True)

    def test_kasli04_exact_scope(self):
        self.assertEqual(identity('KASLI04')['dna'],0x006c440674704854)
        self.assertEqual(locks('KASLI04',True),[
            '/home/codex-hil/.cache/genesys-210383B7F02DA.lock',
            '/home/codex-hil/.cache/kasli-KASLI04.lock'])
