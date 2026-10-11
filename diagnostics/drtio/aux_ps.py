"""PS AXI, AUX CSR/SRAM and coherently reset GT endpoint; LGPL-3.0-or-later."""
from migen import Module, ClockDomain, ClockSignal, Signal, ClockDomainsRenamer, ResetInserter
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.fhdl.structure import _Assign
from misoc.interconnect import csr_bus, wishbone2csr
from misoc.interconnect.csr import CSRStatus
from litex.soc.interconnect import wishbone
from litex.soc.interconnect.axi import AXIInterface, AXILiteInterface, AXI2AXILite
from aux_endpoint import AuxEndpoint
from aux_bus import AuxAddressRouter, AUX_OFFSET, AUX_BYTES
from aux_axi import CheckedAXILite2Wishbone


class AuxPS(Module):
    """Standalone integration block; reset is asynchronous to all domains.

    Drive reset from system reset OR GT reset/not-ready; hold through clock
    stop/restart. Its three private domains assert reset together and release
    synchronously to their clocks. PS AXI/CSR logic remains alive during reset.
    Transactions in flight across reset must be aborted by the host/firmware.
    """
    BASE = 0xa0000000
    BANK = 3

    def __init__(self):
        self.reset = Signal(reset=1)
        self.clock_domains.cd_aux_sys = ClockDomain('aux_sys')
        self.clock_domains.cd_aux_tx = ClockDomain('aux_tx')
        self.clock_domains.cd_aux_rx = ClockDomain('aux_rx')
        for domain, source in ((self.cd_aux_sys,'sys'),
                               (self.cd_aux_tx,'gth_tx'),(self.cd_aux_rx,'gth_rx')):
            self.comb += domain.clk.eq(ClockSignal(source))
            self.specials += AsyncResetSynchronizer(domain,self.reset)
        self.submodules.endpoint = e = ClockDomainsRenamer(
            {'sys':'aux_sys','gth_tx':'aux_tx','rtio_rx':'aux_rx'})(AuxEndpoint())
        self.tx_raw, self.rx_raw = e.tx_raw, e.rx_raw
        self.bridge_busy = CSRStatus(1,name='bridge_busy')
        self.rx_up = CSRStatus(1,name='rx_up')
        self.in_reset = CSRStatus(1,name='in_reset')
        self.comb += [self.bridge_busy.status.eq(e.bridge.busy),
                     self.rx_up.status.eq(e.link.rx_up.status),
                     self.in_reset.status.eq(self.reset)]
        self.csrs = e.aux.get_csrs()+[self.bridge_busy,self.rx_up,self.in_reset]
        self.submodules.wb2csr = w = wishbone2csr.WB2CSR(
            bus_wishbone=wishbone.Interface(data_width=32,address_width=40,addressing='word'),
            bus_csr=csr_bus.Interface(data_width=32,address_width=14))
        self.submodules.bank = csr_bus.CSRBank(self.csrs,self.BANK,bus=w.csr)
        # Pinned MiSoC CSRStorage pads aligned readback with hi-alignment
        # zeros instead of alignment zeros. Fix only this finalized CSR.
        length=e.aux.transmitter.aux_tx_length
        readback=[statement for statement in length._fragment.comb
                  if isinstance(statement,_Assign) and
                  statement.l is length.simple_csrs[0].w]
        if len(readback)!=1 or length.alignment_bits!=2:
            raise ValueError('Unsupported AUX length CSR readback shape')
        readback[0].r=length.storage_full & ~3
        # CSRBank owns the finalized CSRStorage module on the PS clock,
        # so its state needs an explicit reset as well as endpoint domains.
        ResetInserter()(length)
        self.comb += length.reset.eq(self.reset)
        self.submodules.router = r = AuxAddressRouter(w.wishbone,e.aux.bus)
        self.axi = AXIInterface(data_width=32,address_width=40,id_width=16)
        lite = AXILiteInterface(data_width=32,address_width=40)
        self.submodules.converter = AXI2AXILite(self.axi,lite)
        self.submodules.bridge = CheckedAXILite2Wishbone(lite,r.bus,self.BASE)

    def memory_map(self):
        address=self.BASE+self.BANK*0x800
        regs={}
        for csr in self.csrs:
            words=(csr.size+31)//32
            regs[csr.name]={'address':address,'words':words,'bits':csr.size}
            address+=4*words
        return {'kind':'aux-integration-map-not-hardware-evidence',
                'registers':regs,'aux_sram':{'base':self.BASE+AUX_OFFSET,
                'size':AUX_BYTES,'rx_offset':8192,'slot_size':1024,'slots':8}}
