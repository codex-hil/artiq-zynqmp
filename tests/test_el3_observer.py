"""EL3 observer binary safety controls; LGPL-3.0-or-later."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_el3_observer import check, WORDS


def fixture():
    data = bytearray(184)
    data[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHIQQQIHHHHHH', data, 16, 2, 183, 1, 0xfffc0000, 64, 0, 0, 64, 56, 1, 0, 0, 0)
    struct.pack_into('<II6Q', data, 64, 1, 5, 120, 0xfffc0000, 0xfffc0000, 64, 64, 4)
    struct.pack_into('<16I', data, 120, *WORDS)
    return data


class ObserverTests(unittest.TestCase):
    def test_reviewed_image(self):
        self.assertFalse(check(fixture())['destructive_test_allowed'])

    def test_memory_store_rejected(self):
        data = fixture()
        struct.pack_into('<I', data, 120 + 12 * 4, 0xf9000000)  # STR X0,[X0]
        with self.assertRaises(ValueError): check(data)

    def test_layout_mutations_rejected(self):
        for offset, fmt, value in [(88, '<Q', 0), (104, '<Q', 128), (68, '<I', 7), (24, '<Q', 0)]:
            data = fixture()
            struct.pack_into(fmt, data, offset, value)
            with self.assertRaises(ValueError): check(data)


if __name__ == '__main__': unittest.main()
