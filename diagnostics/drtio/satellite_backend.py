"""Real RT packet/SED/TTL backend for the Genesys laboratory diagnostic.

LGPL-3.0-or-later. Entire backend uses sys; caller must provide synchronous
packet words or an explicitly tested transport crossing. No AUX reset service.
"""
from migen import Module, Signal, ClockDomainsRenamer, ResetInserter, If
from artiq.gateware.drtio.core import SyncRTIO
from artiq.gateware.rtio.tsc import TSC
from artiq.gateware.rtio.channel import Channel
from artiq.gateware.rtio.phy.ttl_simple import Output, Input
from satellite_packet import CheckedRTPacketSatellite
from artiq.gateware.rtio import cri


class SatelliteBackend(Module):
    def __init__(self, packet_link, output_pad, input_pad=None, glbl_fine_ts_width=0, dma_membus=None, dma_cri=None):
        self.rtio_reset, self.phy_reset = Signal(), Signal()
        self.reset_applied, self.phy_reset_applied = Signal(), Signal()
        self.submodules.tsc = TSC(glbl_fine_ts_width=glbl_fine_ts_width)
        self.submodules.phy = ClockDomainsRenamer({'rio_phy':'sys'})(
            ResetInserter(['rio_phy'])(Output(output_pad)))
        source = Input(input_pad) if input_pad is not None else Output(Signal())
        self.submodules.input_phy = ClockDomainsRenamer({'rio':'sys','rio_phy':'sys'})(
            ResetInserter(['rio','rio_phy'] if input_pad is not None else ['rio_phy'])(source))
        self.submodules.rtio = ClockDomainsRenamer({'rio':'sys'})(ResetInserter(['rio'])(SyncRTIO(
            self.tsc, [Channel.from_phy(self.phy), Channel.from_phy(self.input_phy)],
            lane_count=8, fifo_depth=128)))
        packet_cri = self.rtio.cri
        if dma_membus is not None and dma_cri is not None:
            raise ValueError('Choose local DMA bus or external DMA CRI')
        if dma_membus is not None:
            # Optional same-clock laboratory path only. Reuse the qualified
            # M-Labs AXI DMA port and native switch, not a new trace decoder.
            # The caller must own all transactions and switch only while idle.
            # Do not reset AXI DMA with queue reset: outstanding reads must drain.
            from zynqmp_dma import DMA
            self.submodules.dma = DMA(dma_membus)
            dma_cri = self.dma.cri
        if dma_cri is not None:
            packet_cri = cri.Interface()
            self.submodules.cri_switch = cri.CRISwitch(
                [packet_cri, dma_cri], self.rtio.cri)
        self.submodules.packet = CheckedRTPacketSatellite(packet_link, packet_cri)
        self.comb += [self.tsc.load.eq(self.packet.tsc_load),
            self.tsc.load_value.eq(self.packet.tsc_load_value),
            self.rtio.reset_rio.eq(self.rtio_reset),
            self.phy.reset_rio_phy.eq(self.phy_reset),
            self.input_phy.reset_rio_phy.eq(self.phy_reset),
            self.packet.reset.eq(self.rtio_reset)]
        if input_pad is not None:
            self.comb += self.input_phy.reset_rio.eq(self.rtio_reset)
        # Apply reset before merging domains, mirroring upstream satellite:
        # queue/input-control reset preserves output PHY state; PHY reset is
        # separate. TSC, packet serializer and reply CDC never reset here.
        for request, applied in ((self.rtio_reset,self.reset_applied),
                                 (self.phy_reset,self.phy_reset_applied)):
            held = Signal(2)
            self.sync += [If(request,
                If(held != 3, held.eq(held + 1))).Else(held.eq(0)),
                applied.eq(request & (held == 3))]
        # Output's reset-less pad register needs extra edges to follow reset
        # pad_k; both applied flags require four complete backend clock edges.
        self.async_errors = self.rtio.async_errors
