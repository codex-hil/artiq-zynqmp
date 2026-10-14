"""Diagnostic bitbang timing overlay. LGPL-3.0-or-later.

Reuses RNG-RPI bus transactions; adds explicit 100us phase hold and a late
sample, comparable to upstream ARTIQ half_period. Not a hardware fix claim.
"""
import time
from i2c import I2C


class SettledI2C(I2C):
    def __init__(self, bus):
        super().__init__(bus)
        self.previous_scl = 0
        self.previous_sda = 1

    def set(self, scl, sda):
        # Separate falling clock from changing data; preserve data hold.
        if self.previous_scl and not scl and sda != self.previous_sda:
            super().set(0, self.previous_sda)
            time.sleep(0.0001)
        value = super().set(scl, sda)
        time.sleep(0.0001)
        self.previous_scl, self.previous_sda = scl, sda
        if scl:
            value = self.b.regs.i2c_r.read()
            if not value & 2:
                raise TimeoutError('SCL low at settled sample')
        return value
