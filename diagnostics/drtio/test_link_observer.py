"""Offline wire/CDC controls for receive-only observer; LGPL-3.0-or-later."""
import unittest
from migen import Module, Signal, Cat, ClockDomain, ClockDomainsRenamer
from migen.sim import run_simulation
from artiq.gateware.drtio.link_layer import LinkLayerTX
from raw20_codec import Raw20Codec
from link_observer import LinkObserver


class Wire(Module):
    def __init__(self, offset):
        self.clock_domains.cd_gth_tx = ClockDomain('gth_tx')
        self.clock_domains.cd_gth_rx = ClockDomain('gth_rx')
        self.submodules.source = ClockDomainsRenamer('gth_tx')(Raw20Codec(rx_domain='gth_rx'))
        self.submodules.tx = ClockDomainsRenamer('gth_tx')(LinkLayerTX(self.source.encoder))
        self.submodules.observer = LinkObserver()
        previous = Signal(20)
        self.sync.gth_tx += previous.eq(self.source.tx_raw)
        stream = Cat(previous, self.source.tx_raw)
        self.comb += self.observer.rx_raw.eq(stream[offset:offset+20])


class ObserverTests(unittest.TestCase):
    def exercise(self, offset):
        dut = Wire(offset)
        o = dut.observer
        def run():
            for _ in range(100): yield
            self.assertEqual((yield o.alignment.status) & 1, 1)
            # Ignore acquisition artifacts until explicit measurement enable.
            for counter in o.counts.values():
                self.assertEqual((yield counter.value), 0)
            yield o.enable.storage.eq(1)
            for _ in range(20): yield
            # Arbitrary values, deliberately unrelated to ProtocolProbe pattern.
            yield dut.tx.rt_frame.eq(1)
            for value in (0x1234, 0xdead, 0, 0xffff, 0x5678):
                yield dut.tx.rt_data.eq(value)
                yield
            yield dut.tx.rt_frame.eq(0)
            for _ in range(30): yield
            yield dut.tx.aux_frame.eq(1)
            for value in (3, 0, 15, 7):
                yield dut.tx.aux_data.eq(value)
                yield
                while not (yield dut.tx.aux_ack): yield
            yield dut.tx.aux_frame.eq(0)
            for _ in range(80): yield
            self.assertEqual((yield o.rt_frames.status), 1)
            self.assertEqual((yield o.rt_words.status), 5)
            self.assertEqual((yield o.aux_frames.status), 1)
            self.assertEqual((yield o.aux_words.status), 4)
            yield o.enable.storage.eq(0)
            for _ in range(20): yield
            yield dut.tx.rt_frame.eq(1)
            for _ in range(30): yield
            yield dut.tx.rt_frame.eq(0)
            for _ in range(30): yield
            self.assertEqual((yield o.rt_words.status), 5)
        run_simulation(dut, {'gth_tx':run()},
                       clocks={'sys':13, 'gth_tx':8, 'gth_rx':(8, 2)})

    def test_all_twenty_bit_offsets_and_disabled_counting(self):
        for offset in range(20):
            with self.subTest(offset=offset): self.exercise(offset)


if __name__ == '__main__': unittest.main()
