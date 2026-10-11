"""Bounded PS Wishbone decode for diagnostic AUX; LGPL-3.0-or-later."""
from migen import Module, If
from litex.soc.interconnect import wishbone

CSR_BYTES = 0x4000
AUX_OFFSET = 0x10000
AUX_BYTES = 0x4000


class AuxAddressRouter(Module):
    """Word-addressed AXI bridge bus -> CSR or upstream AUX SRAM.

    Input addresses are relative to the PS PL aperture. Never truncate the
    address before decoding: an invalid address must not alias valid SRAM.
    Unmapped active transactions terminate with ERR, so CPU accesses cannot
    wait forever. The upstream AUX's TX subwindow still repeats its SRAM;
    this router protects the outer 16 KiB aperture, not those native aliases.
    """
    def __init__(self, csr_bus, aux_bus):
        self.bus = b = wishbone.Interface(data_width=32, address_width=40,
                                         addressing='word')
        for slave in (csr_bus, aux_bus):
            self.comb += [slave.dat_w.eq(b.dat_w),
                          slave.sel.eq(b.sel), slave.we.eq(b.we),
                          slave.cyc.eq(0), slave.stb.eq(0)]
        # Subtract before narrowing the upstream 30-bit word address.
        self.comb += [csr_bus.adr.eq(b.adr),
                     aux_bus.adr.eq(b.adr - AUX_OFFSET // 4),
                     b.dat_r.eq(0), b.ack.eq(0), b.err.eq(0),
            If(b.adr < CSR_BYTES // 4,
                csr_bus.cyc.eq(b.cyc), csr_bus.stb.eq(b.stb),
                b.dat_r.eq(csr_bus.dat_r), b.ack.eq(csr_bus.ack),
                b.err.eq(csr_bus.err)
            ).Elif((b.adr >= AUX_OFFSET // 4) &
                   (b.adr < (AUX_OFFSET + AUX_BYTES) // 4),
                aux_bus.cyc.eq(b.cyc), aux_bus.stb.eq(b.stb),
                b.dat_r.eq(aux_bus.dat_r), b.ack.eq(aux_bus.ack),
                b.err.eq(aux_bus.err)
            ).Else(b.err.eq(b.cyc & b.stb))]
