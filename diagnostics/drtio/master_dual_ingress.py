# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated dual AXI ingress reset assembly; no PS primitive/clock source.

HPM0 is resettable target, HPM1 always-live management. Parent must wire all
reset_out bits to target domains and gate packet admission. No shared AXI decoder.
"""
from migen import Module,ClockDomainsRenamer,Signal
from migen.genlib.cdc import MultiReg
from litex.soc.interconnect.axi import AXIInterface,AXI2AXILite
from aux_reset_control import AuxResetControl
from aux_reset_domains import AuxResetDomains
from aux_reset_management import AuxResetManagement
from master_axi_admission import MasterAXIAdmission

class MasterDualIngress(Module):
    def __init__(self,target,*,domains=('ps','sys','rtio_rx','rio','rio_phy'),
                 ps='ps',management='management',control='control',shape_fault=None):
        domains=tuple(domains)
        if ps not in domains or management in domains or control in domains:
            raise ValueError('Target PS must reset; management/control must remain live')
        self.submodules.coordinator=c=ClockDomainsRenamer(control)(AuxResetControl(len(domains)))
        self.submodules.releases=r=AuxResetDomains(domains,control=control)
        self.submodules.management=m=AuxResetManagement(c,management=management,control=control,
                                                     shape_fault=shape_fault)
        self.comb += [r.request.eq(c.reset),c.domain_ready.eq(r.ready)]
        self.reset_out=r.reset_out
        self.admit=c.admit
        self.management_axi=AXIInterface(data_width=32,address_width=40,id_width=16)
        self.submodules.converter=ClockDomainsRenamer(management)(AXI2AXILite(self.management_axi,m.axi))
        self.submodules.target_gate=g=MasterAXIAdmission(target)
        admitted=Signal()
        self.specials+=MultiReg(c.admit,admitted,ps)
        self.comb += g.enable.eq(admitted & ~r.reset_out[domains.index(ps)])
        self.target_axi=g.axi
