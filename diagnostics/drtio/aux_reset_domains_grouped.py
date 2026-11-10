# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate fixed five-logical/three-physical reset-group candidate.

Parent must prove SYS/rio/rio_phy use the SAME physical clock signal and reset
policy. Confirmation flags are obligations, not automatic clock detection. One
shared masked-ready synchronizer/counter serves TX; PS and RX remain distinct.
No production/default selection or physical reset/CDC qualification is implied.
"""
from migen import Module,Signal
from aux_reset_domains_masked import AuxResetDomainsMasked

class AuxResetDomainsGrouped(Module):
    def __init__(self,*,control='control',shared_tx_clock_confirmed=False,
                 shared_reset_policy_confirmed=False):
        if shared_tx_clock_confirmed is not True or shared_reset_policy_confirmed is not True:
            raise ValueError('Explicit common TX clock and reset-policy proofs required')
        if control in ('ps','sys','rtio_rx','rio','rio_phy'):
            raise ValueError('Control must remain independent of target reset groups')
        self.request=Signal(reset=1);self.ready=Signal(5);self.reset_out=Signal(5)
        self.submodules.groups=g=AuxResetDomainsMasked(('ps','sys','rtio_rx'),control=control)
        self.comb+=g.request.eq(self.request)
        self.group_indices=(0,1,2,1,1)
        for index,group in enumerate(self.group_indices):
            self.comb += [self.ready[index].eq(g.ready[group]),
                          self.reset_out[index].eq(g.reset_out[group])]
