# SPDX-License-Identifier: LGPL-3.0-or-later
"""Separate always-live AXI-Lite management aperture candidate.

Must bypass target admission gate/reset. Three aligned32bit registers only;
parent full AXI decode and physical reset topology are not supplied here.
"""
from migen import Module, Signal, ClockDomainsRenamer, Cat, If
from litex.soc.interconnect import wishbone
from litex.soc.interconnect.axi import AXILiteInterface
from aux_axi import CheckedAXILite2Wishbone
from aux_reset_commands import AuxResetCommands

class AuxResetManagement(Module):
    BASE=0xa0020000
    IDENTITY=0x47524d31
    def __init__(self,coordinator,*,management='management',control='control'):
        self.axi=AXILiteInterface(data_width=32,address_width=40)
        self.submodules.commands=h=AuxResetCommands(coordinator,management=management,control=control)
        b=wishbone.Interface(data_width=32,address_width=40,addressing='word')
        self.submodules.bridge=ClockDomainsRenamer(management)(
            CheckedAXILite2Wishbone(self.axi,b,self.BASE))
        command=Signal(2,reset=1)
        self.comb += [h.request.eq(command[0]),h.abandoned.eq(command[1])]
        active=b.cyc & b.stb
        valid_read=b.adr<3
        valid_write=(b.adr==1) & (b.sel==15) & (b.dat_w<4)
        valid=(~b.we & valid_read) | (b.we & valid_write)
        self.comb += [b.ack.eq(active & valid),b.err.eq(active & ~valid),b.dat_r.eq(0),
            If(b.adr==0,b.dat_r.eq(self.IDENTITY)).Elif(b.adr==1,b.dat_r.eq(command)).Elif(
                b.adr==2,b.dat_r.eq(Cat(h.reset_status,h.abandonment_ready,h.admit)))]
        sync=getattr(self.sync,management)
        sync += If(active & b.we & valid_write,command.eq(b.dat_w))
