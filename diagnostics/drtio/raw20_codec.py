"""ARTIQ's existing software 8b/10b codec for a raw 20-bit GT interface.

The caller supplies TX/sys and recovered RX clocks, transceiver reset/ready
and verified comma/word alignment. Readiness/reset inputs must already be
synchronized to sys (the upstream LinkLayer readiness FSM domain). This module is not a GT reset sequencer,
a clock cleaner, or a deterministic-latency PHY.
"""
from migen import Module, Signal, Cat, ClockDomainsRenamer
from misoc.cores.code_8b10b import Encoder, Decoder
from artiq.gateware.drtio.core import ChannelInterface


class Raw20Codec(Module):
    def __init__(self, rx_domain="rtio_rx"):
        self.tx_raw = Signal(20)
        self.rx_raw = Signal(20)
        self.rx_reset_done = Signal()
        self.rx_clock_active = Signal()
        self.word_aligned = Signal()
        self.rx_reset = Signal()
        # Match the established ARTIQ GTP/GTX wire representation: lane zero
        # occupies bits 0..9; each symbol is serialized least-significant first.
        self.submodules.encoder = Encoder(2, True)
        self.decoders = []
        for lane in range(2):
            decoder = Decoder(True)
            self.submodules += ClockDomainsRenamer(rx_domain)(decoder)
            self.decoders.append(decoder)
            self.comb += decoder.input.eq(self.rx_raw[10*lane:10*(lane+1)])
        self.channel = ChannelInterface(self.encoder, self.decoders)
        self.comb += [
            self.tx_raw.eq(Cat(*self.encoder.output)),
            self.channel.rx_ready.eq(self.rx_reset_done & self.rx_clock_active
                                     & self.word_aligned & ~self.rx_reset),
        ]
