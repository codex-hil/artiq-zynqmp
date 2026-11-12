# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate release-request retention candidate, no default integration change.

Parent supplies a control reset with asynchronous assertion and release only
on fresh control edges. Holding release request through that reset lets the
registered coordinator assume reset ownership before control-reset deassertion.
No combinational feedback to control reset is permitted. Clock return alone
is not requester abandonment or permission to retry target transactions.
"""
from migen import Module,Signal
class AuxResetRetention(Module):
 def __init__(self,coordinator_reset,control_reset):
  self.request=Signal(reset=1)
  self.comb+=self.request.eq(coordinator_reset | control_reset)
