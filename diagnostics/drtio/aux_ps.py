"""PS AXI, AUX CSR/SRAM and coherently reset GT endpoint; LGPL-3.0-or-later."""
from migen import Module, ClockDomain, ClockSignal, Signal, ClockDomainsRenamer, ResetInserter, Mux
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.genlib.cdc import MultiReg
from migen.fhdl.structure import _Assign
from misoc.interconnect import csr_bus, wishbone2csr
from misoc.interconnect.csr import CSRStatus, CSRStorage
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

    def __init__(self, extra_banks=(), output_pad=None, input_pad=None):
        self.reset = Signal(reset=1)
        self.clock_domains.cd_aux_sys = ClockDomain('aux_sys')
        self.clock_domains.cd_aux_tx = ClockDomain('aux_tx')
        self.clock_domains.cd_aux_rx = ClockDomain('aux_rx')
        for domain, source in ((self.cd_aux_sys,'sys'),
                               (self.cd_aux_tx,'gth_tx'),(self.cd_aux_rx,'gth_rx')):
            self.comb += domain.clk.eq(ClockSignal(source))
            self.specials += AsyncResetSynchronizer(domain,self.reset)
        e = AuxEndpoint()
        transport = None
        if output_pad is not None:
            from satellite_transport import SatelliteTransport
            e.submodules.satellite = transport = SatelliteTransport(e, output_pad, input_pad, glbl_fine_ts_width=3)
        elif input_pad is not None:
            raise ValueError('Satellite input requires an output pad')
        self.submodules.endpoint = ClockDomainsRenamer(
            {'sys':'aux_sys','gth_tx':'aux_tx','rtio_rx':'aux_rx'})(e)
        self.satellite = transport
        self.tx_raw, self.rx_raw = e.tx_raw, e.rx_raw
        self.bridge_busy = CSRStatus(1,name='bridge_busy')
        self.rx_up = CSRStatus(1,name='rx_up')
        self.in_reset = CSRStatus(1,name='in_reset')
        self.comb += [self.bridge_busy.status.eq(e.bridge.busy),
                     self.rx_up.status.eq(e.link.rx_up.status),
                     self.in_reset.status.eq(self.reset)]
        self.csrs = e.aux.get_csrs()+[self.bridge_busy,self.rx_up,self.in_reset]
        if transport is not None:
            self.tsc_load_count = CSRStatus(32, name='tsc_load_count')
            self.rt_reply_fault = CSRStatus(1, name='rt_reply_fault')
            self.rtio_error_flags = CSRStatus(3, name='rtio_error_flags')
            self.rtio_spread_enable = CSRStorage(1, name='rtio_spread_enable')
            self.comb += transport.backend.rtio.sed_spread_enable.eq(self.rtio_spread_enable.storage)
            fault, errors = Signal(), Signal(3)
            self.specials += [MultiReg(transport.reply_fault, fault),
                              MultiReg(transport.rtio_error_flags, errors)]
            self.comb += [self.tsc_load_count.status.eq(Mux(self.reset,0,transport.tsc_load_count)),
                self.rt_reply_fault.status.eq(fault & ~self.reset),
                self.rtio_error_flags.status.eq(Mux(self.reset,0,errors))]
            self.csrs += [self.tsc_load_count,self.rt_reply_fault,self.rtio_error_flags,self.rtio_spread_enable]
        self.submodules.wb2csr = w = wishbone2csr.WB2CSR(
            bus_wishbone=wishbone.Interface(data_width=32,address_width=40,addressing='word'),
            bus_csr=csr_bus.Interface(data_width=32,address_width=14))
        bank_bus=csr_bus.Interface(data_width=32,address_width=14)
        self.submodules.bank = csr_bus.CSRBank(self.csrs,self.BANK,bus=bank_bus)
        buses=[bank_bus]
        self.extra_banks=[]
        for name,bank_id,description in extra_banks:
            bus=csr_bus.Interface(data_width=32,address_width=14)
            bank=csr_bus.CSRBank(description,bank_id,bus=bus)
            setattr(self.submodules,'bank_'+name,bank)
            self.extra_banks.append((name,bank_id,description))
            buses.append(bus)
        self.submodules.csr_interconnect=csr_bus.Interconnect(w.csr,buses)
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
