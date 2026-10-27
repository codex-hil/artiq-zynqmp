"""Offline read failure, no retry and reentrancy controls. LGPL-3.0-or-later."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'diagnostics/ddr'))
from pit_counter_observation import ADDRESSES, OfflineCollector, decode


class Tests(unittest.TestCase):
    def test_complete_exact_read_order(self):
        calls = []
        def read(address):
            calls.append(address)
            return len(calls)
        result = OfflineCollector().collect(7, read)
        self.assertEqual(calls, list(ADDRESSES) * 2)
        self.assertEqual(result['status'], 'COMPLETE_OFFLINE')
        self.assertEqual(result['completed_reads'], 8)
        self.assertFalse(decode(result['record'], 7)['destructive_test_allowed'])

    def test_each_failure_position_stops_without_record_or_retry(self):
        for fail in range(8):
            for bad in (None, True, -1, 1 << 32, 'exception'):
                calls = []
                def read(address):
                    calls.append(address)
                    if len(calls) - 1 == fail:
                        if bad == 'exception':
                            raise OSError('synthetic bus failure')
                        return bad
                    return 0
                collector = OfflineCollector()
                result = collector.collect(7, read)
                self.assertEqual(len(calls), fail + 1)
                self.assertEqual(result['attempted_reads'], fail + 1)
                self.assertEqual(result['completed_reads'], fail)
                self.assertEqual(result['status'], 'INCOMPLETE')
                self.assertIsNone(result['record'])
                with self.assertRaises(ValueError): collector.collect(8, read)
                self.assertEqual(len(calls), fail + 1)

    def test_reentrant_attempt_rejected_before_nested_read(self):
        collector = OfflineCollector()
        nested = []
        def read(address):
            with self.assertRaises(ValueError):
                collector.collect(8, lambda a: nested.append(a))
            return 0
        self.assertEqual(collector.collect(7, read)['completed_reads'], 8)
        self.assertEqual(nested, [])

    def test_invalid_entry_does_not_consume_or_call(self):
        collector = OfflineCollector()
        calls = []
        for nonce in (0, True, -1, 1 << 64):
            with self.assertRaises(ValueError):
                collector.collect(nonce, lambda a: calls.append(a))
        with self.assertRaises(ValueError): collector.collect(7, None)
        self.assertEqual(calls, [])
        self.assertEqual(collector.collect(7, lambda a: 0)['completed_reads'], 8)


if __name__ == '__main__':
    unittest.main()
