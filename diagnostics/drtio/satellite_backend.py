"""Real RT packet/SED/TTL backend for the Genesys laboratory diagnostic.

LGPL-3.0-or-later. Entire backend uses sys; caller must provide synchronous
packet words or an explicitly tested transport crossing. No AUX reset service.
"""
from migen import Module, Signal, ClockDomainsRenamer
from artiq.gateware.drtio.core import SyncRTIO
from artiq.gateware.rtio.tsc import TSC
from artiq.gateware.rtio.channel import Channel
from artiq.gateware.rtio.phy.ttl_simple import Output, Input
from satellite_packet import CheckedRTPacketSatellite


class SatelliteBackend(Module):
    def __init__(self, packet_link, output_pad, input_pad=None, glbl_fine_ts_width=0):
        self.submodules.tsc = TSC(glbl_fine_ts_width=glbl_fine_ts_width)
        self.submodules.phy = ClockDomainsRenamer({'rio_phy': 'sys'})(Output(output_pad))
        self.submodules.input_phy = ClockDomainsRenamer({'rio': 'sys', 'rio_phy': 'sys'})(
            Input(input_pad) if input_pad is not None else Output(Signal()))
        self.submodules.rtio = ClockDomainsRenamer({'rio': 'sys'})(SyncRTIO(
            self.tsc, [Channel.from_phy(self.phy), Channel.from_phy(self.input_phy)],
            lane_count=8, fifo_depth=128))
        self.submodules.packet = CheckedRTPacketSatellite(packet_link, self.rtio.cri)
        self.comb += [self.tsc.load.eq(self.packet.tsc_load),
                     self.tsc.load_value.eq(self.packet.tsc_load_value)]
        # Intentionally preserve upstream timestamp conventions and diagnostics.
        self.async_errors = self.rtio.async_errors
