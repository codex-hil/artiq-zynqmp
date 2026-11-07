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

class BoundedRing(unittest.TestCase):
    def test_full_preserves_published_and_recovers(self):
        from aux_receiver_bounded import BoundedReceiver
        d = Module()
        class Link:
            rx_aux_data = Signal(4)
            rx_aux_stb = Signal()
            rx_aux_frame = Signal()
        link = Link()
        d.submodules.receiver = r = BoundedReceiver(link, 32)
        port = r.mem.get_port(async_read=True)
        d.specials += port
        packets = [[0xabc00000 + 16*i+j for j in range(3)] for i in range(7)]
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
        def clear_error():
            yield r.aux_rx_error.re.eq(1)
            yield
            yield r.aux_rx_error.re.eq(0)
            for _ in range(8):
                yield
        def consume():
            yield r.aux_rx_present.re.eq(1)
            yield
            yield r.aux_rx_present.re.eq(0)
            for _ in range(12):
                yield
        def check_slot(slot, words):
            for index, word in enumerate(words):
                yield port.adr.eq(slot*256+index)
                yield
                self.assertEqual((yield port.dat_r), word)
        def test():
            for packet in packets:
                yield from send(packet)
            self.assertEqual((yield r.aux_rx_present.w), 1)
            self.assertEqual((yield r.aux_rx_error.w), 0)
            # Normal full-ring drop, then oversized drop in same uncommitted slot.
            for rejected in ([0xdeadbeef]*3, [0x12345678]*257):
                yield from send(rejected)
                self.assertEqual((yield r.aux_rx_error.w), 1)
                for slot, packet in enumerate(packets):
                    yield from check_slot(slot, packet)
                self.assertEqual((yield r.aux_read_pointer.w), 0)
                yield from clear_error()
                self.assertEqual((yield r.aux_rx_error.w), 0)
            yield from consume()
            self.assertEqual((yield r.aux_read_pointer.w), 1)
            fresh = [0xfedcba98, 0x76543210]
            yield from send(fresh)
            self.assertEqual((yield r.aux_rx_error.w), 0)
            yield from check_slot(7, fresh)
            for slot in range(1, 8):
                self.assertEqual((yield r.aux_rx_present.w), 1)
                self.assertEqual((yield r.aux_read_pointer.w), slot)
                yield from check_slot(slot, packets[slot] if slot < 7 else fresh)
                yield from consume()
            self.assertEqual((yield r.aux_rx_present.w), 0)
            self.assertEqual((yield r.aux_read_pointer.w), 0)
            self.assertEqual((yield r.aux_rx_error.w), 0)
        run_simulation(d, {'rtio_rx': test()}, clocks={'sys': 8, 'rtio_rx': 8})

if __name__ == '__main__':
    unittest.main()
