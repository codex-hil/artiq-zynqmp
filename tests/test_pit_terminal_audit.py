"""Exact terminal opcode/escape negative controls. LGPL-3.0-or-later."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_pit_terminal_audit import check


def fixture(words=(0xb8220004, 0xba020004, 0xb800fffc), machine=189, entry=0):
    ident = b'\x7fELF\x01\x01\x01' + bytes(9)
    header = struct.pack('<HHIIIIIHHHHHH', 2, machine, 1, entry, 52, 0, 0, 52, 32, 1, 0, 0, 0)
    payload = struct.pack('<' + 'I' * len(words), *words)
    program = struct.pack('<8I', 1, 84, 0, 0, len(payload), len(payload), 7, 4)
    return ident + header + program + payload


class Tests(unittest.TestCase):
    def test_exact_loop_has_no_hardware_admission(self):
        self.assertFalse(check(fixture())['deployable'])

    def test_changed_or_escaping_instructions(self):
        for words in [(0x80000000, 0xba020004, 0xb800fffc),
                      (0xb8220004, 0x80000000, 0xb800fffc),
                      (0xb8220004, 0xba020004, 0xb8000004),
                      (0xb8220004, 0xba020004, 0xb60f0008),
                      (0xb8220004, 0xba020004, 0xb800fffc, 0x80000000)]:
            with self.assertRaises(ValueError): check(fixture(words))
        for data in [fixture(machine=40), fixture(entry=4), fixture()[:-1]]:
            with self.assertRaises(ValueError): check(data)


if __name__ == '__main__':
    unittest.main()
