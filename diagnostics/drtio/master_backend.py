"""Native master boundary for the Genesys/Kasli role reversal.

LGPL-3.0-or-later. Caller owns TSC/clock/reset domains and the encoded channel.
This is not AXI, firmware, AUX discovery or physical-link integration.
"""
from migen import Module
from artiq.gateware.drtio.core import DRTIOMaster


class GenesysMasterBackend(Module):
    def __init__(self, tsc, channel):
        # Standard Kasli satellite uses fine width3: 1ns timestamp units at
        # 125MHz coarse clock. Reject the old Genesys local-only width0 input.
        if tsc.glbl_fine_ts_width != 3:
            raise ValueError('Kasli satellite requires fine width3; reconcile host time units')
        if len(channel.encoder.k) != 2 or len(channel.decoders) != 2:
            raise ValueError('Initial master profile requires two symbols/raw20')
        self.submodules.native = native = DRTIOMaster(tsc, channel)
        self.cri = native.cri
        # References only: do not register native submodules a second time.
        self.rt_controller = native.rt_controller
        self.rt_packet = native.rt_packet
        self.link_layer = native.link_layer

    def get_csrs(self):
        return self.native.get_csrs()
