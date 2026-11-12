# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate retained grouped release candidate; default classes unchanged.

Control reset must assert asynchronously and release on fresh control edges.
Retention gates only target-domain reset release; GT, management and admission
must retain their independently reviewed parent connections. No automatic
abandonment, retry, physical CDC or reset-timing qualification is supplied.
"""
from migen import Module,Signal,ResetSignal
from aux_reset_domains_grouped import AuxResetDomainsGrouped
from aux_reset_retention import AuxResetRetention
class AuxResetDomainsRetained(Module):
 def __init__(self,*,control='control',shared_tx_clock_confirmed=False,shared_reset_policy_confirmed=False):
  self.submodules.groups=g=AuxResetDomainsGrouped(control=control,
   shared_tx_clock_confirmed=shared_tx_clock_confirmed,
   shared_reset_policy_confirmed=shared_reset_policy_confirmed)
  self.request=Signal(reset=1)
  self.submodules.retention=h=AuxResetRetention(self.request,ResetSignal(control))
  self.comb+=g.request.eq(h.request)
  self.ready=g.ready;self.reset_out=g.reset_out
  self.group_indices=g.group_indices
