# SPDX-License-Identifier: LGPL-3.0-or-later
"""Level handshake for an always-live management source, not resettable PL AXI.

Host holds request until reset status asserted; lowers request and abandonment,
waits abandonment_ready, then raises abandonment and waits admit. Management and
control must remain live; neither may reset its handshake storage mid-episode.
No software MMIO register bank, retry or cancellation proof is supplied.
"""
from migen import Module, Signal
from migen.genlib.cdc import MultiReg

class AuxResetCommands(Module):
    def __init__(self, coordinator, *, management='management', control='control'):
        if management==control:
            raise ValueError('Distinct declared management/control clocks required')
        self.request=Signal(reset=1)
        self.abandoned=Signal()
        self.reset_status=Signal(reset=1)
        self.abandonment_ready=Signal()
        self.admit=Signal()
        self.specials += [
            MultiReg(self.request,coordinator.request,control,reset=1),
            MultiReg(self.abandoned,coordinator.requester_abandoned,control),
            MultiReg(coordinator.reset,self.reset_status,management,reset=1),
            MultiReg(coordinator.abandonment_ready,self.abandonment_ready,management),
            MultiReg(coordinator.admit,self.admit,management)]
