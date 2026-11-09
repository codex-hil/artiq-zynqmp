# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate masked-ready candidate; default AuxResetDomains is unchanged.

Local reset asynchronously masks the exported ready level even with no source
clock. Synchronized release requires two source edges; the local synchronous
ready/count clear during those edges before reset can drop. Fresh ready then
requires the original count sequence. This source-level argument requires
physical CDC/reset timing qualification; mask is not a timing waiver.

Control clock must remain live. Parent must distribute each reset_out to the
corresponding target domain and keep admission disabled until coordinator admit.
Private release clocks follow source clocks; no clock-stop watchdog included.
Async assertion, synchronized release primitives need physical qualification.
"""
from migen import Module, Signal, ClockDomain, ClockSignal, If
from migen.genlib.cdc import MultiReg
from migen.genlib.resetsync import AsyncResetSynchronizer


class AuxResetDomainsMasked(Module):
    def __init__(self, domains, *, control='sys'):
        domains=tuple(domains)
        if not domains or len(set(domains))!=len(domains) or control in domains:
            raise ValueError('Distinct target domains and separate live control required')
        self.request=Signal(reset=1)
        self.ready=Signal(len(domains))
        self.reset_out=Signal(len(domains))
        self.release_domains=[]
        for index,name in enumerate(domains):
            cd=ClockDomain('aux_release_'+name)
            self.clock_domains+=cd
            self.release_domains.append(cd)
            self.comb += [cd.clk.eq(ClockSignal(name)),self.reset_out[index].eq(cd.rst)]
            self.specials+=AsyncResetSynchronizer(cd,self.request)
            count=Signal(2)
            local_ready=Signal()
            sync=getattr(self.sync,cd.name)
            sync += If(count!=3,count.eq(count+1)).Else(local_ready.eq(1))
            self.specials+=MultiReg(local_ready & ~cd.rst,self.ready[index],control)
