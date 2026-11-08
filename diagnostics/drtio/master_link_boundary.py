# SPDX-License-Identifier: LGPL-3.0-or-later
"""Candidate reset/admission boundary for Raw20Codec and physical GT status.

Raw status bits cross independently into native SYS. clock_active is an external
qualified indication, not a watchdog implemented here. GT reset follows held
reset request, NOT inverse admission: GT clocks must restart before admission.
Parent must connect gt_reset_request to the wizard's qualified reset controller.
"""
from migen import Module,Signal,ResetSignal
from migen.genlib.cdc import MultiReg

class MasterLinkBoundary(Module):
    def __init__(self,codec,admit,reset_request,status):
        self.gt_reset_request=reset_request
        self.allowed=Signal()
        permit=Signal();requested=Signal(reset=1)
        reset_done=Signal();clock_active=Signal();aligned=Signal()
        self.specials += [MultiReg(admit,permit,'sys'),
            MultiReg(reset_request,requested,'sys',reset=1),
            MultiReg(status.reset_done,reset_done,'sys'),
            MultiReg(status.clock_active,clock_active,'sys'),
            MultiReg(status.aligned,aligned,'sys')]
        self.comb += [self.allowed.eq(permit & ~requested & ~ResetSignal('sys')),
            codec.rx_reset.eq(~self.allowed),codec.rx_reset_done.eq(reset_done),
            codec.rx_clock_active.eq(clock_active),codec.word_aligned.eq(aligned)]
