# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated RX progress interlock candidate, NOT integrated or physically qualified.

Single outstanding toggle challenge avoids free-running counter sampling alias.
Control clock must remain live. Parent holds rearm during coordinated reset and
abandonment; no independent RX reset is permitted while admitted. Rearm must not
be derived from RX status. Timeout is a functional parameter, not qualified HW
latency. Physical synchronizers/reset/skew and fault->admission CDC need review.
"""
from migen import Module, Signal, If
from migen.genlib.cdc import MultiReg

class MasterRXProgress(Module):
    def __init__(self, timeout_cycles=32, *, control='control', rx='rtio_rx'):
        if (not isinstance(timeout_cycles,int) or isinstance(timeout_cycles,bool)
                or timeout_cycles<4 or control==rx):
            raise ValueError('Distinct clocks and integer timeout >=4 required')
        self.rearm=Signal(reset=1)
        self.fault=Signal()
        self.allowed=Signal()
        self.request=Signal()
        self.response=Signal()
        request_rx=Signal();response_control=Signal()
        self.specials += [MultiReg(self.request,request_rx,rx),
                          MultiReg(self.response,response_control,control)]
        rx_sync=getattr(self.sync,rx)
        rx_sync += self.response.eq(request_rx)
        age=Signal(max=timeout_cycles)
        fresh=Signal(2)
        complete=Signal()
        self.comb += [complete.eq(response_control==self.request),
                      self.allowed.eq(~self.rearm & ~self.fault & (fresh==2))]
        control_sync=getattr(self.sync,control)
        control_sync += [
            If(complete,self.request.eq(~self.request),age.eq(0)
            ).Elif(age<timeout_cycles-1,age.eq(age+1)),
            If(self.rearm,self.fault.eq(0),fresh.eq(0),age.eq(0)
            ).Elif(~self.fault,
                If(~complete & (age==timeout_cycles-1),self.fault.eq(1)
                ).Elif(complete & (fresh<2),fresh.eq(fresh+1)))]
