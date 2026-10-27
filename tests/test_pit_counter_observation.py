"""Counter-only offline contract controls. LGPL-3.0-or-later."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'diagnostics/ddr'))
from pit_counter_observation import ADDRESSES, decode


class Tests(unittest.TestCase):
    def record(self, first=(0, 17, 0xffffffff, 20), second=(0, 16, 0, 21)):
        return {'version': 1, 'nonce': 7, 'samples': [
            {'sequence': n, 'address': ADDRESSES[n % 4], 'value': value}
            for n, value in enumerate(first + second)]}

    def test_changes_never_become_elapsed_time(self):
        result = decode(self.record(), 7)
        self.assertEqual([x['changed'] for x in result['counters']], [False, True, True, True])
        for key in ('elapsed_ticks', 'rollover_count', 'frequency_hz'):
            self.assertIsNone(result[key])
        self.assertFalse(result['physical_backend_ready'])
        self.assertFalse(result['destructive_test_allowed'])

    def test_aliasing_stalled_and_whole_period_indistinguishable(self):
        # Synthetic countdown modulo 16: zero, one and three periods alias.
        for elapsed in (0, 16, 48):
            values = (5,) * 4
            second = tuple((v - elapsed) % 16 for v in values)
            self.assertTrue(all(not x['changed'] for x in decode(self.record(values, second), 7)['counters']))
        # Same endpoints after 1 or 17 ticks: changed does not count wraps.
        self.assertEqual((5 - 1) % 16, (5 - 17) % 16)

    def test_write_only_and_unreviewed_addresses_rejected(self):
        for address in (0xffd40010, 0xffd40040, 0xffd40048, 0xff413030):
            record = self.record(); record['samples'][0]['address'] = address
            with self.assertRaises(ValueError): decode(record, 7)

    def test_frame_identity_order_and_types(self):
        baseline = self.record()
        mutations = []
        for field, value in [('nonce', 8), ('nonce', True), ('version', True), ('version', 2), ('extra', 0)]:
            r = copy.deepcopy(baseline); r[field] = value; mutations.append(r)
        for field, value in [('sequence', 1), ('sequence', False), ('value', -1), ('value', 1 << 32), ('value', True), ('extra', 0)]:
            r = copy.deepcopy(baseline); r['samples'][0][field] = value; mutations.append(r)
        r = copy.deepcopy(baseline); r['samples'].pop(); mutations.append(r)
        r = copy.deepcopy(baseline); r['samples'][0], r['samples'][1] = r['samples'][1], r['samples'][0]; mutations.append(r)
        for record in mutations:
            with self.assertRaises(ValueError): decode(record, 7)
        for nonce in (0, True, -1, 1 << 64):
            with self.assertRaises(ValueError): decode(baseline, nonce)


if __name__ == '__main__':
    unittest.main()
