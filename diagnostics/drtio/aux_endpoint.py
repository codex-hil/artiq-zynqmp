"""Upstream AUX SRAM controller on PS clock, raw GTH link on GT clocks.

LGPL-3.0-or-later. Diagnostic only; simultaneous resets of all three domains
are required. No discovery/routing firmware or production satellite implied.
"""
from types import SimpleNamespace
from migen import Module, Signal, Cat, ClockDomainsRenamer, If
from migen.genlib.cdc import MultiReg
from misoc.interconnect.csr import CSRStatus
from artiq.gateware.drtio.link_layer import LinkLayerTX, LinkLayerRX
from artiq.gateware.drtio.aux_controller import DRTIOAuxController
from raw20_codec import Raw20Codec
from protocol_probe import WordAligner
from aux_tx_cdc import AuxTxCDC


class AuxEndpoint(Module):
    def __init__(self):
        self.tx_raw, self.rx_raw = Signal(20), Signal(20)
        self.submodules.codec = ClockDomainsRenamer({'sys': 'gth_tx'})(
            Raw20Codec(rx_domain='rtio_rx'))
        self.submodules.aligner = ClockDomainsRenamer('rtio_rx')(WordAligner())
        self.submodules.tx = ClockDomainsRenamer('gth_tx')(LinkLayerTX(self.codec.encoder))
        self.submodules.rx = ClockDomainsRenamer('rtio_rx')(LinkLayerRX(self.codec.decoders))
        self.submodules.bridge = AuxTxCDC()
        b = self.bridge
        self.link = SimpleNamespace(
            tx_aux_frame=b.input_frame, tx_aux_data=b.input_data, tx_aux_ack=b.input_ack,
            rx_aux_frame=self.rx.aux_frame, rx_aux_data=self.rx.aux_data,
            rx_aux_stb=Signal(), rx_up=CSRStatus(1, name='rx_up'),
            tx_rt_frame=self.tx.rt_frame, tx_rt_data=self.tx.rt_data)
        # Alignment can precede descrambler convergence. Discard startup
        # symbols instead of committing a spurious first RX SRAM packet.
        settled = Signal(7)
        ready = Signal()
        self.sync.rtio_rx += If(~self.aligner.aligned, settled.eq(0)).Elif(
            settled != 127, settled.eq(settled + 1))
        self.comb += ready.eq(settled == 127)
        self.rx_ready = ready  # RX-domain qualifier for the real RT backend.
        self.specials += MultiReg(ready, self.link.rx_up.status)
        self.submodules.aux = DRTIOAuxController(self.link)
        self.comb += [self.tx_raw.eq(self.codec.tx_raw),
                     self.aligner.input.eq(self.rx_raw),
                     self.codec.rx_raw.eq(self.aligner.output),
                     self.tx.aux_frame.eq(b.output_frame),
                     self.tx.aux_data.eq(b.output_data), b.output_ack.eq(self.tx.aux_ack),
                     self.link.rx_aux_stb.eq(self.rx.aux_stb & ready)]
