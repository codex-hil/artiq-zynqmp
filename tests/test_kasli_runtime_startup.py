"""Bounded runtime startup controls. LGPL-3.0-or-later."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'diagnostics/kasli-master'))
from runtime_startup import execute


class StartupTest(unittest.TestCase):
    def test_two_upload_clock_switch_flow(self):
        chunks = iter([b'ARTIQ runtime starting\nswitching sys clock, rebooting...\nWaiting for connections...',
                       b'ARTIQ runtime starting\nclocking has already been set up\nnetwork addresses: MAC=lab'])
        uart = SimpleNamespace(read=lambda size: next(chunks))
        first, second = Mock(), Mock()
        report = {}
        with patch('runtime_startup.socket.socket', return_value=second):
            execute(first, uart, bytearray(), b'payload', 'fe80::1', 2, Mock(), report)
        self.assertEqual(first.sendall.call_args_list[0].args, (b'B',))
        self.assertEqual(second.sendall.call_args_list[-1].args, (b'B',))
        second.close.assert_called_once()
        self.assertEqual(report['runtime_boot_commands'], 2)
        self.assertTrue(report['clock_switch_reboot_observed'])
        self.assertEqual(report['runtime_startup'], 'PASS')

    def test_panic_is_not_startup_success(self):
        report = {}
        uart = SimpleNamespace(read=lambda size: b'ARTIQ runtime starting\npanic at rtio_clocking.rs')
        with self.assertRaisesRegex(RuntimeError, 'panic/halt'):
            execute(Mock(), uart, bytearray(), b'x', 'fe80::1', 2, Mock(), report)
        self.assertNotIn('runtime_startup', report)
