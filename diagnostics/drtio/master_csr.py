"""Separate Genesys-master PS CSR candidate; LGPL-3.0-or-later.

Full32-bit/40-bit-address AXI, native CSR banks and checked SLVERR completion.
Partial CSR writes are refused; optional AUX SRAM retains native byte enables. Clock/reset/GT/AUX firmware and unaligned/burst
ABI are not qualified.
"""
import json
from pathlib import Path
from migen import Module
from misoc.interconnect import csr_bus,wishbone2csr
from misoc.interconnect.csr import CSRStatus
from litex.soc.interconnect import wishbone
from litex.soc.interconnect.axi import AXIInterface,AXILiteInterface,AXI2AXILite
from aux_axi import CheckedAXILite2Wishbone

class GenesysMasterCSR(Module):
    BASE=0xa0000000
    IDENTITY=0x47534d31
    def __init__(self,tsc,kernel,backend,routing,aux=None):
        if tsc.glbl_fine_ts_width!=3 or not hasattr(kernel,'now') or kernel.now.size!=64:
            raise ValueError('Master CSR profile requires fine3 and now64 kernel initiator')
        profile=[CSRStatus(32,name='identity'),CSRStatus(32,name='fine_width'),CSRStatus(32,name='coarse_hz')]
        self.comb += [profile[0].status.eq(self.IDENTITY),profile[1].status.eq(3),profile[2].status.eq(125000000)]
        descriptions=[('kernel',0,kernel.get_csrs()),('profile',1,profile),('master',2,backend.get_csrs()),('routing',3,routing.get_csrs())]
        if aux is not None:
            descriptions.append(('aux',4,aux.get_csrs()))
        self.axi=AXIInterface(data_width=32,address_width=40,id_width=16)
        lite=AXILiteInterface(data_width=32,address_width=40)
        self.submodules.converter=AXI2AXILite(self.axi,lite)
        bus=wishbone.Interface(data_width=32,address_width=40,addressing='word')
        self.submodules.bridge=CheckedAXILite2Wishbone(lite,bus,self.BASE)
        if aux is not None:
            from aux_bus import AuxAddressRouter
            csr_input=wishbone.Interface(data_width=32,address_width=40,addressing='word')
            self.submodules.aux_router=router=AuxAddressRouter(csr_input,aux.bus)
            self.comb += bus.connect(router.bus)
            bus=csr_input
        self.submodules.wb2csr=w=wishbone2csr.WB2CSR(
            bus_wishbone=wishbone.Interface(data_width=32,address_width=40,addressing='word'),
            bus_csr=csr_bus.Interface(data_width=32,address_width=14))
        valid=(bus.adr < ((5 if aux is not None else 4)*0x800)//4) & (~bus.we | (bus.sel==15))
        self.comb += [w.wishbone.adr.eq(bus.adr),w.wishbone.dat_w.eq(bus.dat_w),
            w.wishbone.sel.eq(bus.sel),w.wishbone.we.eq(bus.we),
            w.wishbone.cyc.eq(bus.cyc & valid),w.wishbone.stb.eq(bus.stb & valid),
            bus.dat_r.eq(w.wishbone.dat_r),bus.ack.eq(w.wishbone.ack & valid),
            bus.err.eq(bus.cyc & bus.stb & ~valid)]
        buses=[];self.registers={}
        for label,bank_id,registers in descriptions:
            names=[c.name for c in registers]
            if len(names)!=len(set(names)):raise ValueError('Duplicate CSR names in '+label)
            csr=csr_bus.Interface(data_width=32,address_width=14)
            setattr(self.submodules,'bank_'+label,csr_bus.CSRBank(registers,bank_id,bus=csr))
            buses.append(csr);offset=self.BASE+bank_id*0x800
            for reg in registers:
                words=(reg.size+31)//32
                self.registers[label+'_'+reg.name]={'address':offset,'bits':reg.size,'words':words,'word_order':'big','word_bytes':4}
                offset+=words*4
            if offset>self.BASE+(bank_id+1)*0x800:raise ValueError('CSR bank overflow')
        self.submodules.interconnect=csr_bus.Interconnect(w.csr,buses)
    def write_map(self,path):
        Path(path).write_text(json.dumps({'kind':'genesys-master-candidate-not-local-rtio-abi','identity':self.IDENTITY,'fine_ts_width':3,'timestamp_unit_ps':1000,'coarse_hz':125000000,'csr_base':self.BASE,'registers':self.registers,'scope':'Aligned single-beat32-bit accesses; no AXI/GT/firmware hardware qualification'},indent=2)+'\n')
