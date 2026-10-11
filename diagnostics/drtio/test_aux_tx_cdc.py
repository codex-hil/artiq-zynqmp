"""AUX packet CDC conservation with unrelated clocks; LGPL-3.0-or-later."""
import unittest
from migen import Module, passive
from migen.sim import run_simulation
from aux_tx_cdc import AuxTxCDC


class AuxTxCDCTest(unittest.TestCase):
    def exercise(self, sys_period, tx_period):
        d = Module()
        d.submodules.bridge = b = AuxTxCDC()
        packets = [[(i + n) & 15 for i in range(size)]
                   for n, size in enumerate((8, 136, 2048, 24))]
        received, current = [], []

        @passive
        def reader():
            cycle = 0
            in_packet = False
            while True:
                # Long RT arbitration stalls, including inside AUX packets.
                ack = cycle % 37 >= 19
                yield b.output_ack.eq(ack)
                yield
                if ack:
                    frame = (yield b.output_frame)
                    if frame:
                        in_packet = True
                        current.append((yield b.output_data))
                    elif in_packet:
                        received.append(list(current))
                        current.clear()
                        in_packet = False
                cycle += 1

        def writer():
            for data in packets:
                for value in data:
                    yield b.input_frame.eq(1)
                    yield b.input_data.eq(value)
                    yield
                    while not (yield b.input_ack): yield
                yield b.input_frame.eq(0)
                yield
                while not (yield b.input_ack): yield
                yield
                for _ in range(40000):
                    if not (yield b.busy): break
                    yield
                else: self.fail('Bridge failed to drain')
                for _ in range(8): yield
            self.assertEqual(received, packets)
        run_simulation(d, {'sys': writer(), 'gth_tx': reader()},
                       clocks={'sys': sys_period, 'gth_tx': (tx_period, 3)})

    def test_ps_faster(self): self.exercise(8, 14)
    def test_gth_faster(self): self.exercise(14, 8)
