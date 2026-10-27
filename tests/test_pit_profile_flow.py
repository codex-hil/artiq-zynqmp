"""Consistent ELF/disassembly mutations of archived linked flow. LGPL-3.0-or-later."""
import re
import struct
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check_pit_profile_flow import check
ARCHIVE = ROOT / 'evidence/pmu-fresh-pit-audit-link-offline-2026-10-27'


def fixture(change=None, stale_disassembly=False):
    # Synthetic ELF containing only actual archived function bodies; not firmware.
    text = '\n'.join((ARCHIVE / (name + '.dis')).read_text() for name in
                     ('pit_terminal_audit', 'terminal_adapter', 'pit_profile_entry_audit'))
    symbols = (ARCHIVE / 'selected-symbols.txt').read_text() + 'ffdd2030 00000114 T memset\n'
    if change and not stale_disassembly:
        old, new = change
        assert old in text
        text = text.replace(old, new, 1)
    rows = [(int(a, 16), int(w, 16)) for a, w in re.findall(r'^([0-9a-f]+):\s+([0-9a-f]{8})', text, re.M)]
    base = min(a for a, _ in rows)
    payload = bytearray(max(a for a, _ in rows) - base + 4)
    for address, word in rows:
        struct.pack_into('<I', payload, address - base, word)
    if change and stale_disassembly:
        old, new = change
        a, w = re.match(r'([0-9a-f]+):\s+([0-9a-f]{8})', new).groups()
        struct.pack_into('<I', payload, int(a, 16) - base, int(w, 16))
    ident = b'\x7fELF\x01\x01\x01' + bytes(9)
    header = struct.pack('<HHIIIIIHHHHHH', 2, 189, 1, 0xffdc0050, 52, 0, 0, 52, 32, 1, 0, 0, 0)
    program = struct.pack('<8I', 1, 84, base, base, len(payload), len(payload), 7, 4)
    return ident + header + program + payload, symbols, text


class Tests(unittest.TestCase):
    def test_archived_scoped_flow(self):
        result = check(*fixture())
        self.assertEqual(result['abstract_callback_sites'], 9)
        self.assertFalse(result['deployable'])

    def test_consistent_control_mutations_rejected(self):
        mutations = [
            ('ffdcf1a8:\tb8220004 \tmbar\t1', 'ffdcf1a8:\t80000000 \tor r0,r0,r0'),
            ('ffdcf1bc:\tb9f4ffec \tbrlid\tr15, -20', 'ffdcf1bc:\tb9f4fff0 \tbrlid r15,-16'),
            ('ffdcf26c:\tb9f4ff48 \tbrlid\tr15, -184', 'ffdcf26c:\tb9f4ff4c \tbrlid r15,-180'),
            ('ffdcf1c4:\t3021ff5c \taddik\tr1, r1, -164', 'ffdcf1c4:\tb60f0008 \trtsd r15,8'),
            ('ffdcf1ec:\tbe080220 \tbeqid\tr8, 544', 'ffdcf1ec:\tbe087ffc \tbeqid r8,32764'),
            ('ffdcf25c:\t99fcb000 \tbrald\tr15, r22', 'ffdcf25c:\t99fc0800 \tbrald r15,r1'),
        ]
        for mutation in mutations:
            with self.assertRaises(ValueError): check(*fixture(mutation))
        with self.assertRaises(ValueError): check(*fixture(mutations[0], stale_disassembly=True))


if __name__ == '__main__':
    unittest.main()
