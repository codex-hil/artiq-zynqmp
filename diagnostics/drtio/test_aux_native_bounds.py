# SPDX-License-Identifier: LGPL-3.0-or-later
"""Characterize pinned native receiver; oversized acceptance is a failure finding."""
import unittest
from migen import Module, Signal
from migen.sim import run_simulation
from artiq.gateware.drtio.aux_controller import Receiver


class NativeBounds(unittest.TestCase):
    receiver_type = Receiver
    bounded = False

    def exercise(self, count):
        d = Module()
        class Link:
            rx_aux_data = Signal(4)
            rx_aux_stb = Signal()
            rx_aux_frame = Signal()
        link = Link()
        d.submodules.receiver = r = self.receiver_type(link, 32)
        port = r.mem.get_port(async_read=True)
        d.specials += port
        def send(words):
            yield link.rx_aux_stb.eq(1)
            yield link.rx_aux_frame.eq(1)
            for word in words:
                for nibble in range(8):
                    yield link.rx_aux_data.eq((word >> (4*nibble)) & 15)
                    yield
            yield link.rx_aux_frame.eq(0)
            yield
            yield link.rx_aux_stb.eq(0)
            for _ in range(30):
                yield
        def test():
            words = [0x12340000+i for i in range(count)]
            yield from send(words)
            rejected = self.bounded and count > 256
            self.assertEqual((yield r.aux_rx_present.w), int(not rejected))
            self.assertEqual((yield r.aux_rx_error.w), int(rejected))
            yield port.adr.eq(0)
            yield
            self.assertEqual((yield port.dat_r), words[256] if count > 256 and not self.bounded else words[0])
            yield port.adr.eq(254)
            yield
            self.assertEqual((yield port.dat_r), words[254])
            # Acknowledge and receive a later valid packet in the next slot.
            yield r.aux_rx_error.re.eq(1)
            yield
            yield r.aux_rx_error.re.eq(0)
            yield r.aux_rx_present.re.eq(1)
            yield
            yield r.aux_rx_present.re.eq(0)
            for _ in range(30):
                yield
            self.assertEqual((yield r.aux_rx_present.w), 0)
            yield from send([0xabcdef01])
            self.assertEqual((yield r.aux_rx_present.w), 1)
            self.assertEqual((yield r.aux_read_pointer.w), 0 if rejected else 1)
            yield port.adr.eq(0 if rejected else 256)
            yield
            self.assertEqual((yield port.dat_r), 0xabcdef01)
            self.assertEqual((yield r.aux_rx_error.w), 0)
        # Same ideal periods isolate receiver length semantics from CDC claims.
        run_simulation(d, {'rtio_rx': test()}, clocks={'sys': 8, 'rtio_rx': 8})

    def test_1020_bytes(self): self.exercise(255)
    def test_1024_bytes(self): self.exercise(256)
    def test_1028_bytes_characterizes_unflagged_overwrite(self): self.exercise(257)

class BoundedCases(NativeBounds):
    from aux_receiver_bounded import BoundedReceiver
    receiver_type = BoundedReceiver
    bounded = True

    def test_2048_bytes_discard_through_eop(self): self.exercise(512)

if __name__ == '__main__':
    unittest.main()
