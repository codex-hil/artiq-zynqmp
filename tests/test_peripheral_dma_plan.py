"""Peripheral field and header rejection controls; LGPL-3.0-or-later."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from plan_peripheral_dma_snapshot import REGISTERS, FIELDS, decode, plan

class PeripheralTests(unittest.TestCase):
    def test_enabled_gem_never_claims_idle(self):
        s = dict.fromkeys(REGISTERS, 0)
        s.update(gem0_network_control=12, sd1_present_state=0x307,
                 qspi_dma_status=0xffff)
        r = decode([s, s]); row = r['samples'][0]
        self.assertTrue(row['gem_rx_enabled'] and row['gem_tx_enabled'])
        self.assertTrue(row['sd_command_inhibit'] and row['sd_write_active'])
        self.assertEqual(row['qspi_dma_outstanding'], 15)
        self.assertEqual(row['qspi_dma_fifo_level'], 255)
        self.assertEqual(row['qspi_dma_unacknowledged_done'], 7)
        self.assertFalse(r['destructive_test_allowed'])
        self.assertEqual(r['ownership'], 'NOT_PROVEN')
    def test_missing_and_changed_samples(self):
        s = dict.fromkeys(REGISTERS, 0)
        self.assertFalse(decode([s, dict(s, sd1_present_state=1)])['stable'])
        for bad in [[s], [s, {}], [s, dict(s, qspi_dma_status=True)],
                    [s, dict(s, qspi_dma_status=1 << 32)]]:
            with self.assertRaises(ValueError):decode(bad)
    def test_all_changed_fields_and_missing_headers_reject(self):
        headers = {n: ''.join(f'#define {k} 0x{v:x}U\n' for k, v in fields.items())
                   for n, fields in FIELDS.items()}
        self.assertFalse(plan(headers)['hardware_executed'])
        for n, fields in FIELDS.items():
            for field, value in fields.items():
                changed = dict(headers)
                changed[n] = changed[n].replace(f'#define {field} 0x{value:x}U',
                                               f'#define {field} 0x{value ^ 1:x}U')
                with self.assertRaises(ValueError):plan(changed)
        with self.assertRaises(ValueError):plan({})

if __name__ == '__main__':unittest.main()
