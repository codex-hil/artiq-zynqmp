"""Reset/profile safety controls for lab restore. LGPL-3.0-or-later."""
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'diagnostics/kasli-master'))
from clock_restore import exercise


class RestoreTest(unittest.TestCase):
    def run_model(self, fail_register=None):
        snapshot = json.loads((ROOT / 'evidence/kasli03-clock-snapshot-2026-10-13/results.json').read_text())
        plan = json.loads((ROOT / 'evidence/kasli03-clock-restore-plan-2026-10-14.json').read_text())
        regs = {int(k): value[0] for k, value in snapshot['registers'].items()}
        now, writes, frame = [0.0], [], []
        class Bus:
            def start(self): frame.clear()
            def stop(self): pass
            def put(self, value):
                frame.append(value)
                if len(frame) < 3: return True
                reg = frame[1]
                writes.append((reg, value))
                if reg == fail_register: return False
                if reg == 136:
                    if value == 0x80:
                        for item in plan['configuration_to_compare_then_restore']:
                            regs[item['register']] = 0
                    return value != 0x80  # Expected reset-value NACK.
                regs[reg] = value
                return True
            def read(self, address, register, length):
                return bytes([0 if register == 136 else regs[register]])
        def counter():
            value = int(now[0] * 125e6) & 0xffffffff
            return value ^ (value >> 1)
        comm = SimpleNamespace(regs=SimpleNamespace(**{
            key: SimpleNamespace(read=lambda v=value: v)
            for key, value in [('eem_enable', 0), ('gtp_control', 0), ('diag_sfp_outputs', 7)]}))
        comm.regs.diag_si_gray = SimpleNamespace(read=counter)
        report = {}
        with patch('clock_restore.time.monotonic', side_effect=lambda: now[0]), patch(
                'clock_restore.time.sleep', side_effect=lambda delay: now.__setitem__(0, now[0] + delay)):
            if fail_register is None:
                exercise(comm, Bus(), snapshot['registers'], plan, report)
            else:
                with self.assertRaisesRegex(RuntimeError, 'value NACK'):
                    exercise(comm, Bus(), snapshot['registers'], plan, report)
        return report, writes

    def test_restore_and_expected_reset_nack(self):
        report, writes = self.run_model()
        self.assertTrue(report['restoration_profile_validated'])
        self.assertEqual(writes[0], (136, 0x80))
        self.assertEqual(writes[-1], (136, 0x40))
        self.assertFalse({129, 130, 134, 135} & {reg for reg, value in writes})
        self.assertEqual(report['output_hz_against_host'], [125e6] * 3)

    def test_configuration_nack_is_not_accepted_or_reset_repeated(self):
        report, writes = self.run_model(25)
        self.assertEqual(writes.count((136, 0x80)), 1)
        self.assertEqual(writes.count((25, 192)), 6)  # Three attempts plus one bounded recovery.
        self.assertNotEqual(report['profile_restoration'], 'PASS')
        self.assertNotIn('restoration_profile_validated', report)
