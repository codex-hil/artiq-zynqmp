"""RX-clock RTIO backend with whole-packet TX replies; LGPL-3.0-or-later.

Lab transport only: caller resets sys/rtio_rx/gth_tx together. No production
AUX acknowledgements, deterministic PHY latency, or timestamp compensation.
"""
from types import SimpleNamespace
from migen import Module, Signal, Cat, If, ClockDomainsRenamer
from aux_tx_cdc import AuxTxCDC
from satellite_backend import SatelliteBackend
from monitor import GrayCounter


class RTReplyCDC(Module):
    """Admit complete replies only when the existing packet bridge is idle.

    RTPacketSatellite has no TX backpressure. A reply arriving while busy is
    dropped as a whole and latches fault. Oversize/overflow also latches fault;
    callers must reject the run and perform common reset, never report success.
    The128-byte capacity exceeds the supported upstream RT response formats.
    """
    def __init__(self):
        self.frame, self.data = Signal(), Signal(16)
        self.fault = Signal()
        self.submodules.bridge = b = ClockDomainsRenamer({'sys':'rtio_rx'})(
            AuxTxCDC(width=16, max_bytes=128))
        previous, admitted = Signal(), Signal()
        start = self.frame & ~previous
        self.comb += [b.input_data.eq(self.data),
            b.input_frame.eq(self.frame & (admitted | (start & b.input_ack))),
            b.output_ack.eq(1)]
        self.sync.rtio_rx += [previous.eq(self.frame),
            If(start, admitted.eq(b.input_ack)),
            If(~self.frame, admitted.eq(0)),
            If((start & ~b.input_ack) | (admitted & self.frame & ~b.input_ack),
               self.fault.eq(1))]
        self.output_frame, self.output_data = b.output_frame, b.output_data


class SatelliteTransport(Module):
    def __init__(self, endpoint, output_pad, input_pad=None, glbl_fine_ts_width=0, dma_cri=None):
        # All RTIO state follows recovered RX directly; no free-running PS
        # elastic-buffer crossing can silently drop request words/TSC loads.
        self.packet_link = link = SimpleNamespace(
            rx_rt_frame=Signal(), rx_rt_data=Signal(16),
            tx_rt_frame=Signal(), tx_rt_data=Signal(16))
        self.submodules.backend = ClockDomainsRenamer({'sys':'rtio_rx'})(
            SatelliteBackend(link, output_pad, input_pad, glbl_fine_ts_width, dma_cri=dma_cri))
        self.submodules.replies = replies = RTReplyCDC()
        self.comb += [link.rx_rt_frame.eq(endpoint.rx.rt_frame & endpoint.rx_ready),
            link.rx_rt_data.eq(endpoint.rx.rt_data),
            replies.frame.eq(link.tx_rt_frame), replies.data.eq(link.tx_rt_data),
            endpoint.tx.rt_frame.eq(replies.output_frame),
            endpoint.tx.rt_data.eq(replies.output_data)]
        self.submodules.load_events = GrayCounter('rtio_rx')
        self.comb += self.load_events.enable.eq(self.backend.packet.tsc_load)
        # This count crosses to PS/sys only after the actual TSC load edge.
        self.tsc_load_count = self.load_events.value
        self.reply_fault = replies.fault  # RX domain; synchronize before PS use.

        self.rtio_error_flags = Signal(3)
        self.rtio_error_flags.attr.add("keep")
        self.sync.rtio_rx += If(self.backend.rtio_reset,
            self.rtio_error_flags.eq(0)).Else(self.rtio_error_flags.eq(self.rtio_error_flags | Cat(
                self.backend.async_errors.sequence_error,
                self.backend.async_errors.collision, self.backend.async_errors.busy)))
