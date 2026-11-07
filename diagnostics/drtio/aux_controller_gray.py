# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated controller derived from M-Labs ARTIQ DRTIOAuxController.

Preserves native transmitter and Wishbone/CSR layout, replacing RX only.
Candidate DW32 only. No physical CDC/reset or PS AXI integration qualification.
"""
from migen import Module, log2_int
from migen.fhdl.simplify import FullMemoryWE
from misoc.interconnect import wishbone
from artiq.gateware.drtio.aux_controller import Transmitter, max_packet, aux_buffer_count
from aux_receiver_gray import GrayBoundedReceiver


@FullMemoryWE()
class GrayAuxController(Module):
    def __init__(self, link_layer, dw=32):
        if dw != 32:
            raise ValueError('Only qualified candidate DW32 layout is supported')
        wsb = log2_int(dw//8)
        self.bus = wishbone.Interface(data_width=dw, adr_width=32-wsb)
        self.submodules.transmitter = Transmitter(link_layer, dw)
        self.submodules.receiver = GrayBoundedReceiver(link_layer, dw)
        tx = wishbone.SRAM(self.transmitter.mem, read_only=False, data_width=dw)
        rx = wishbone.SRAM(self.receiver.mem, read_only=True, data_width=dw)
        select_bit = log2_int(max_packet*aux_buffer_count)-wsb
        decoder = wishbone.Decoder(self.bus,
            [(lambda a: a[select_bit] == 0, tx.bus),
             (lambda a: a[select_bit] == 1, rx.bus)], register=True)
        self.submodules += tx, rx, decoder

    def get_csrs(self):
        return self.transmitter.get_csrs() + self.receiver.get_csrs()
