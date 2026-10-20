"""Offline failure telemetry checks. LGPL-3.0-or-later."""
import unittest
from aux_startup_status import REGISTERS, script, parse


class StatusTests(unittest.TestCase):
    def test_script_reads_only_selected_words_after_identity_check(self):
        mapping = {'registers': {n: {'words': 1, 'address': 0xa0000000+4*i}
                                 for i, n in enumerate(REGISTERS)}}
        text = script(mapping)
        self.assertEqual(text.count('mrd -value'), len(REGISTERS))
        self.assertNotIn('mwr', text)
        self.assertNotIn('rst ', text)
        self.assertLess(text.index('Exact Genesys target missing'), text.index('mrd -value'))
        mapping['registers']['aux_rx_up']['words'] = 2
        with self.assertRaises(ValueError): script(mapping)

    def test_incomplete_duplicate_or_out_of_range_not_accepted(self):
        text = ''.join('AUX_STARTUP_STATUS %s %d\n' % (n, i)
                       for i, n in enumerate(REGISTERS))+'AUX_STARTUP_STATUS_COMPLETE\n'
        self.assertEqual(parse(text)['registers']['aux_rx_up'], 6)
        for bad in (text.replace('aux_rx_up 6\n', ''),
                    text+'AUX_STARTUP_STATUS aux_rx_up 1\n',
                    text.replace('aux_rx_up 6', 'aux_rx_up 4294967296')):
            with self.assertRaises(ValueError): parse(bad)
