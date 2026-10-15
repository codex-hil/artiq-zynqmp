"""Receive-only raw20 ARTIQ framing counters (LGPL-3.0-or-later).

Traffic presence is not packet/CRC validation, link-up, or synchronization.
Caller must reset the RX domain on transceiver reset/loss of readiness: the
laboratory comma aligner otherwise retains its first acquired offset.
"""
from migen import Module, Signal, Cat, If, ClockDomainsRenamer
from migen.genlib.cdc import MultiReg
from misoc.interconnect.csr import AutoCSR, CSRStorage, CSRStatus
from artiq.gateware.drtio.link_layer import LinkLayerRX
from raw20_codec import Raw20Codec
from protocol_probe import WordAligner
from monitor import GrayCounter


class LinkObserver(Module, AutoCSR):
    def __init__(self):
        self.rx_raw = Signal(20)
        self.enable = CSRStorage(1, name='enable')
        self.alignment = CSRStatus(6, name='alignment')
        self.submodules.aligner = ClockDomainsRenamer('gth_rx')(WordAligner())
        self.submodules.codec = ClockDomainsRenamer('gth_tx')(Raw20Codec(rx_domain='gth_rx'))
        self.submodules.rx = ClockDomainsRenamer('gth_rx')(LinkLayerRX(self.codec.decoders))
        self.comb += [self.aligner.input.eq(self.rx_raw),
                      self.codec.rx_raw.eq(self.aligner.output)]
        enabled = Signal()
        self.specials += [MultiReg(self.enable.storage, enabled, odomain='gth_rx'),
            MultiReg(Cat(self.aligner.aligned, self.aligner.offset), self.alignment.status)]
        self.counts = {}
        for kind in ('rt', 'aux'):
            frame = getattr(self.rx, kind + '_frame')
            strobe = 1 if kind == 'rt' else self.rx.aux_stb
            previous = Signal()
            self.sync.gth_rx += If(strobe, previous.eq(frame))
            for suffix, event in [('words', frame & strobe),
                                   ('frames', frame & ~previous & strobe)]:
                name = kind + '_' + suffix
                counter = GrayCounter('gth_rx')
                setattr(self.submodules, name + '_count', counter)
                self.comb += counter.enable.eq(event & enabled & self.aligner.aligned)
                reg = CSRStatus(32, name=name)
                setattr(self, name, reg)
                self.comb += reg.status.eq(counter.value)
                self.counts[name] = counter
