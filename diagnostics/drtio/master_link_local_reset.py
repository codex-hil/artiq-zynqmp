# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate local-reset-only link boundary; requires a parent reset contract.

Caller must prove reset_request asserts local SYS reset independently of the
SYS clock, local release is synchronized, and admission starts zero and remains
zero through reset/fresh domain acknowledgements. This flag is an obligation,
not automatic proof. Removes duplicate requested-status CDC and its INIT
mismatch, but can reopen earlier than the original boundary. Not equivalent
under arbitrary inputs; no default adoption or physical qualification.
"""
from migen import Module,Signal,ResetSignal
from migen.genlib.cdc import MultiReg
class MasterLinkLocalReset(Module):
 def __init__(self,codec,admit,reset_request,status,*,parent_reset_contract_confirmed=False):
  if parent_reset_contract_confirmed is not True:
   raise ValueError('Explicit parent asynchronous assertion/synchronized release/admission contract required')
  self.gt_reset_request=reset_request
  self.allowed=Signal();permit=Signal()
  reset_done=Signal();clock_active=Signal();aligned=Signal()
  self.specials += [MultiReg(admit,permit,'sys'),MultiReg(status.reset_done,reset_done,'sys'),
                    MultiReg(status.clock_active,clock_active,'sys'),MultiReg(status.aligned,aligned,'sys')]
  self.comb += [self.allowed.eq(permit & ~ResetSignal('sys')),codec.rx_reset.eq(~self.allowed),
               codec.rx_reset_done.eq(reset_done),codec.rx_clock_active.eq(clock_active),codec.word_aligned.eq(aligned)]
