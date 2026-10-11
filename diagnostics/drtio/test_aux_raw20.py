"""Bounded AUX memory round trips through upstream framing and raw 8b/10b.

New test glue: LGPL-3.0-or-later. Simulation is not physical validation.
"""
import unittest
from migen import Module, Signal, Cat, passive
from migen.sim import run_simulation
from artiq.gateware.drtio.link_layer import LinkLayer
from artiq.gateware.drtio.aux_controller import DRTIOAuxController, max_packet
from raw20_codec import Raw20Codec
from protocol_probe import WordAligner


class AuxWire(Module):
    def __init__(self, offset=0):
        self.submodules.codec = Raw20Codec()
        self.submodules.aligner = WordAligner()
        self.submodules.link = LinkLayer(self.codec.encoder, self.codec.decoders)
        self.submodules.aux = DRTIOAuxController(self.link)
        previous = Signal(20)
        self.sync += previous.eq(self.codec.tx_raw)
        wire = Cat(previous, self.codec.tx_raw)
        self.comb += [self.aligner.input.eq(wire[offset:offset+20]),
                     self.codec.rx_raw.eq(self.aligner.output),
                     self.link.rx_ready.eq(self.aligner.aligned)]


class AuxRaw20Test(unittest.TestCase):
    def exercise(self, offset, traffic=False, overflow=False):
        dut = AuxWire(offset)
        tx, rx = dut.aux.transmitter, dut.aux.receiver

        def wait(csr, expected, limit=12000):
            for _ in range(limit):
                if bool((yield from csr.read())) == expected:
                    return
                yield
            self.fail('AUX/link timed out')

        def test():
            yield from wait(dut.link.rx_up, True)
            for _ in range(50): yield
            # More than eight packets validates ring pointer wrap, not just slot0.
            for number in range(10):
                size = (1, 3, 17)[number % 3]
                words = [((number+1)*0x1020304 ^ i*0x7654321) & 0xffffffff
                         for i in range(size)]
                for i, word in enumerate(words):
                    yield from dut.aux.bus.write(i, word)
                yield from tx.aux_tx_length.write(size*4)
                yield from tx.aux_tx.write(1)
                yield
                yield from wait(tx.aux_tx, False)
                yield from wait(rx.aux_rx_present, True)
                pointer = yield from rx.aux_read_pointer.read()
                self.assertEqual(pointer, number % 8)
                # RX aperture starts at 8192 bytes; each slot is 1024 bytes.
                base = (max_packet*8 + pointer*max_packet)//4
                received = []
                for i in range(size):
                    received.append((yield from dut.aux.bus.read(base+i)))
                self.assertEqual(received, words)
                self.assertEqual((yield from rx.aux_rx_error.read()), 0)
                yield from rx.aux_rx_present.write(1)
                for _ in range(12): yield
                self.assertFalse((yield from rx.aux_rx_present.read()))

            if overflow:
                for number in range(8):
                    yield from dut.aux.bus.write(0, 0xface0000 | number)
                    yield from tx.aux_tx_length.write(4)
                    yield from tx.aux_tx.write(1)
                    yield
                    yield from wait(tx.aux_tx, False)
                    for _ in range(16): yield
                self.assertTrue((yield from rx.aux_rx_error.read()))
                # Seven readable slots; the eighth must not overwrite them.
                for number in range(7):
                    pointer = yield from rx.aux_read_pointer.read()
                    base = (max_packet*8 + pointer*max_packet)//4
                    self.assertEqual((yield from dut.aux.bus.read(base)),
                                     0xface0000 | number)
                    yield from rx.aux_rx_present.write(1)
                    for _ in range(16): yield
                self.assertFalse((yield from rx.aux_rx_present.read()))
                yield from rx.aux_rx_error.write(1)
                for _ in range(16): yield
                self.assertFalse((yield from rx.aux_rx_error.read()))
                yield from dut.aux.bus.write(0, 0xc001cafe)
                yield from tx.aux_tx_length.write(4)
                yield from tx.aux_tx.write(1)
                yield
                yield from wait(tx.aux_tx, False)
                yield from wait(rx.aux_rx_present, True)
                pointer = yield from rx.aux_read_pointer.read()
                base = (max_packet*8 + pointer*max_packet)//4
                self.assertEqual((yield from dut.aux.bus.read(base)), 0xc001cafe)
                self.assertFalse((yield from rx.aux_rx_error.read()))

        @passive
        def rt_traffic():
            while True:
                yield dut.link.tx_rt_frame.eq(1)
                yield dut.link.tx_rt_data.eq(0x1234)
                for _ in range(9): yield
                yield dut.link.tx_rt_frame.eq(0)
                for _ in range(23): yield

        generators = [test()]
        if traffic: generators.append(rt_traffic())
        run_simulation(dut, generators, clocks={'sys':8, 'rtio_rx':(8,2)})

    def test_memory_ring(self): self.exercise(0)
    def test_rt_contention_and_alignment(self): self.exercise(7, True)

    def test_queue_overflow_and_recovery(self): self.exercise(3, overflow=True)
