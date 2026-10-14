"""Delayed ACK control for diagnostic timing overlay. LGPL-3.0-or-later."""
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0, '/home/codex-hil/rng-rpi/kasli')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'diagnostics/kasli-master'))
try:
    from i2c import I2C
    from settled_i2c import SettledI2C
except ModuleNotFoundError:
    raise unittest.SkipTest("RNG-RPI diagnostic I2C dependency unavailable")


class PinReader:
    def __init__(self, samples):
        self.samples = iter(samples)
    def read(self):
        return next(self.samples)


class TimingTest(unittest.TestCase):
    def bus(self, samples):
        return SimpleNamespace(regs=SimpleNamespace(i2c_w=SimpleNamespace(write=lambda value: None),
                                                    i2c_r=PinReader(samples)))
    def test_delayed_ack_negative_control(self):
        # SCL is high throughout; ACK arrives only after the first sample.
        original = I2C(self.bus([3] * 9))
        self.assertFalse(original.put(0xd0))
        settled = SettledI2C(self.bus([3] * 17 + [2]))
        with patch('settled_i2c.time.sleep'):
            self.assertTrue(settled.put(0xd0))
    def test_true_nack_is_not_hidden(self):
        settled = SettledI2C(self.bus([3] * 18))
        with patch('settled_i2c.time.sleep'):
            self.assertFalse(settled.put(0xd0))
