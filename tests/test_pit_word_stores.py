"""Actual store opcode negatives, independent of disassembly. LGPL-3.0-or-later."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_pit_word_stores import check


def elf(word):
    ident = b'\x7fELF\x01\x01\x01' + bytes(9)
    head = struct.pack('<HHIIIIIHHHHHH', 2, 189, 1, 0, 52, 0, 0, 52, 32, 1, 0, 0, 0)
    ph = struct.pack('<8I', 1, 84, 0, 0, 4, 4, 7, 4)
    return ident + head + ph + struct.pack('<I', word)


class Tests(unittest.TestCase):
    def test_word_immediate_and_indexed_allowed(self):
        for word in (0xf8c1002c, 0xd8c42800):
            self.assertEqual(check(elf(word), '00000000 00000004 T pit_profile_entry_audit')['word_store_sites'], 1)

    def test_all_subword_store_forms_rejected(self):
        for word in (0xd0c42800, 0xd4c42800, 0xf0c1002c, 0xf4c1002c):
            with self.assertRaisesRegex(ValueError, 'subword'):
                check(elf(word), '00000000 00000004 T pit_profile_entry_audit')


if __name__ == '__main__':
    unittest.main()
