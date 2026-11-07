# SPDX-License-Identifier: LGPL-3.0-or-later
"""Control-domain reset admission candidate, not a board reset synchronizer.

Inputs must already be synchronized into control domain. Request must remain
asserted through a control edge. Per-domain ready must clear during reset and
assert only after that domain has restarted. Requester abandoned is a software/
PS handshake, NEVER evidence that earlier MMIO did not execute. No retry output.
External reset distribution/assertion/release and packet input gating required.
"""
from migen import Module, Signal, FSM, If, NextState


class AuxResetControl(Module):
    def __init__(self, domains=5):
        if not isinstance(domains,int) or isinstance(domains,bool) or domains<1:
            raise ValueError('Expected positive domain count')
        self.request=Signal(reset=1)
        self.domain_ready=Signal(domains)
        self.requester_abandoned=Signal()
        self.reset=Signal()
        self.admit=Signal()
        low_seen=Signal()
        abandonment_seen=Signal()
        self.submodules.fsm=fsm=FSM(reset_state='RESET')
        self.comb += [self.reset.eq(fsm.ongoing('RESET') | self.request),
                      self.admit.eq(fsm.ongoing('OPEN') & ~self.request &
                                    (self.domain_ready==(1<<domains)-1))]
        self.sync += If(self.request,
            low_seen.eq(0),abandonment_seen.eq(0)
        ).Elif(fsm.ongoing('RESET'),
            If(~self.requester_abandoned,low_seen.eq(1)),
            If(low_seen & self.requester_abandoned,abandonment_seen.eq(1))
        )
        fsm.act('RESET',
            If(~self.request & abandonment_seen & (self.domain_ready==0),
                NextState('WAIT_READY')))
        fsm.act('WAIT_READY',
            If(self.request,NextState('RESET')).Elif(
                self.domain_ready==(1<<domains)-1,NextState('OPEN')))
        fsm.act('OPEN',If(self.request,NextState('RESET')))
