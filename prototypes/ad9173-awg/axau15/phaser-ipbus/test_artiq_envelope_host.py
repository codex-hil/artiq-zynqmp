"""Host semantics only; run with the shared artiq-host Python, not Migen.

These tests invoke undecorated functions and mock only RTIO syscalls. They
do not establish NAC3 compilation, scheduling, or physical link behaviour.
"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import artiq_envelope as driver


class DriverTest(unittest.TestCase):
    def setUp(self):
        self.device = driver.PhaserEnvelope(SimpleNamespace(get=lambda _: object()), 7)

    def call(self, name, *args):
        return getattr(driver.PhaserEnvelope, name).__wrapped__(self.device, *args)

    def test_command_encoding_and_token_boundaries(self):
        with patch.object(driver, 'rtio_output') as output:
            for token in (0, 123, 0x3fffffff):
                self.call('start', token)
                output.assert_called_with(7 << 8, (token << 2) | 1)
            for token in (-1, 0x40000000):
                output.reset_mock()
                with self.assertRaises(ValueError):
                    self.call('start', token)
                output.assert_not_called()
            self.call('abort')
            output.assert_called_with(7 << 8, 2)
            self.call('query')
            output.assert_called_with(7 << 8, 0)

    def test_raw_responses_preserve_fifo_order(self):
        values = [0x10, 0x13, 0x20, 0x04]
        with patch.object(driver, 'rtio_input_timestamped_data', side_effect=[(0, value) for value in values]) as read:
            self.assertEqual([self.call('read_response', 1000) for _ in values], values)
            self.assertEqual(read.call_count, len(values))
            read.assert_called_with(1000, 7)

    def test_accepted_response_preserves_state(self):
        for response in (0, 0x10, 0x20, 0x30):
            with self.subTest(response=response):
                with patch.object(driver, 'rtio_input_timestamped_data', return_value=(0, response)) as read:
                    self.assertEqual(self.call('check_response', 1000), response)
                    read.assert_called_once_with(1000, 7)

    def test_rejections_and_malformed_responses_are_consumed_once(self):
        cases = [(1, 'command'), (2, 'not armed'), (3, 'Stale'),
                 (4, 'disabled'), (5, 'Unknown'), (15, 'Unknown'),
                 (0x13, 'Stale'), (0x40, 'Invalid'), (-1, 'Invalid'),
                 (0x100, 'Invalid')]
        for response, message in cases:
            with self.subTest(response=response):
                with patch.object(driver, 'rtio_input_timestamped_data', return_value=(0, response)) as read:
                    with self.assertRaisesRegex(ValueError, message):
                        self.call('check_response', 1000)
                    read.assert_called_once_with(1000, 7)

    def test_timeout_is_not_a_success_or_a_retry(self):
        for method in ('read_response', 'check_response'):
            with patch.object(driver, 'rtio_input_timestamped_data', return_value=(-1, 0)) as read:
                with patch.object(driver, 'rtio_output') as output:
                    with self.assertRaisesRegex(ValueError, 'response timeout'):
                        self.call(method, 1000)
                    read.assert_called_once_with(1000, 7)
                    output.assert_not_called()

    def test_invalid_deadline_does_not_consume_response(self):
        for method in ('read_response', 'check_response'):
            with patch.object(driver, 'rtio_input_timestamped_data') as read:
                with self.assertRaisesRegex(ValueError, 'deadline'):
                    self.call(method, -1)
                read.assert_not_called()

    def test_absolute_deadline_is_passed_without_truncation(self):
        for deadline in (0, 2**40 + 123):
            for method in ('read_response', 'check_response'):
                with patch.object(driver, 'rtio_input_timestamped_data', return_value=(0, 0x10)) as read:
                    self.assertEqual(self.call(method, deadline), 0x10)
                    read.assert_called_once_with(deadline, 7)

    def test_transport_failure_is_not_hidden_or_retried(self):
        for method in ('read_response', 'check_response'):
            with patch.object(driver, 'rtio_input_timestamped_data', side_effect=RuntimeError('link')) as read:
                with self.assertRaisesRegex(RuntimeError, 'link'):
                    self.call(method, 1000)
                read.assert_called_once_with(1000, 7)


if __name__ == '__main__':
    unittest.main()
