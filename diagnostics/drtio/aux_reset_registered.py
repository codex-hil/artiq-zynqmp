# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate registered control-output candidate; no production selection.

Adds one control edge before reset/status transitions reach external domains.
Management must hold commands through acknowledgement; no short-pulse support.
Consumers must use this reset and these statuses consistently, not mix raw and
registered signals. Not a physical CDC or glitch/metastability signoff.
"""
from migen import Module,Signal

class AuxResetRegistered(Module):
    def __init__(self,coordinator,*,control='control'):
        self.request=coordinator.request
        self.requester_abandoned=coordinator.requester_abandoned
        self.reset=Signal(reset=1)
        self.admit=Signal()
        self.abandonment_ready=Signal()
        sync=getattr(self.sync,control)
        sync += [self.reset.eq(coordinator.reset),
                 self.admit.eq(coordinator.admit & ~coordinator.reset),
                 self.abandonment_ready.eq(coordinator.abandonment_ready & coordinator.reset)]
