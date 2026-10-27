"""Offline layout conflict controls. LGPL-3.0-or-later."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_pit_slot_layout import check

TEXT = '''ffdd8060 B __bss_start
ffddbe58 00000030 B pit_capture_slot_layout_probe
ffddbeb0 B __bss_end
ffddc7cc B _stack_end
ffddd7d0 B _stack
ffdd8160 00000020 b artiq_pmu_request
ffdd81a8 00000040 b artiq_pmu_guard
'''


class Tests(unittest.TestCase):
    def test_slot_and_no_admission(self):
        self.assertFalse(check(TEXT)['physical_backend_ready'])

    def test_conflicts_and_malformed_slot(self):
        for text in [TEXT.replace('00000030', '00000020'),
                     TEXT.replace('be58', 'be59'),
                     TEXT.replace('00000030 B', '00000030 D'),
                     TEXT.replace('ffddc7cc', 'ffddbe60'),
                     TEXT.replace('ffddd7d0', 'ffddf700'),
                     TEXT + 'ffddbe60 00000004 B foreign_owner\n',
                     TEXT + 'ffddbe58 00000030 B pit_capture_slot_layout_probe\n',
                     TEXT.replace('ffddbeb0 B __bss_end\n', '')]:
            with self.assertRaises(ValueError): check(text)


if __name__ == '__main__':
    unittest.main()
