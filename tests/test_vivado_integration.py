"""Exercise actual instance-side wiring, including nonzero bus offsets."""
import sys
import unittest
from pathlib import Path

from migen import Module
from migen.sim import run_simulation

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "boards/genesys_zu-5ev/1_gateware"))
from vivado_integration import BdCell


class PinWiring(unittest.TestCase):
    def check_direction(self, direction, left, right, value):
        cell = BdCell.__new__(BdCell)
        cell._glue = {}
        public = cell._import_pin_undef({
            "NAME": "bus", "DIR": direction, "LEFT": str(left),
            "RIGHT": str(right), "DEFAULT_DRIVER": "",
        })
        internal = cell._glue["bus"]
        self.assertEqual(len(internal), left - right + 1)
        dut = Module()
        dut.submodules.cell = cell

        def stimulus():
            if direction == "I":
                yield public.eq(value)
                yield
                self.assertEqual((yield internal), value)
            else:
                yield internal.eq(value)
                yield
                self.assertEqual((yield public), value)

        run_simulation(dut, stimulus())

    def test_input_scalar(self):
        self.check_direction("I", 0, 0, 1)

    def test_input_bus(self):
        self.check_direction("I", 31, 0, 0x12345678)

    def test_input_offset(self):
        self.check_direction("I", 15, 8, 0xA5)

    def test_output_bus(self):
        self.check_direction("O", 31, 0, 0x12345678)

    def test_output_offset(self):
        self.check_direction("O", 15, 8, 0xA5)


if __name__ == "__main__":
    unittest.main()
