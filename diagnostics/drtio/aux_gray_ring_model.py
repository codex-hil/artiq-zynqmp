# SPDX-License-Identifier: LGPL-3.0-or-later
"""One-word-per-slot dual-clock SRAM harness; NOT native AUX packet storage.

Reader must allow two destination edges after present or consume before sampling
read_data. Coordinated reset/admission, physical CDC bounds and BRAM inference
remain unqualified. This deliberately simple harness tests ownership only.
"""
from migen import Module, Signal, Memory
from aux_gray_pointer import AuxGrayPointer


class AuxGrayRingModel(Module):
    def __init__(self):
        self.put = Signal()
        self.write_data = Signal(32)
        self.ready = Signal()
        self.consume = Signal()
        self.present = Signal()
        self.read_data = Signal(32)
        self.submodules.writer = w = AuxGrayPointer()
        self.submodules.reader = r = AuxGrayPointer(source='sys', destination='rtio_rx')
        next_write = Signal(3)
        self.memory = Memory(32, 8)
        wp = self.memory.get_port(write_capable=True, clock_domain='rtio_rx')
        rp = self.memory.get_port(clock_domain='sys')
        self.specials += self.memory, wp, rp
        self.comb += [next_write.eq(w.binary+1), self.ready.eq(next_write != r.remote),
            w.advance.eq(self.put & self.ready), wp.we.eq(w.advance),
            wp.adr.eq(w.binary), wp.dat_w.eq(self.write_data),
            self.present.eq(r.binary != w.remote),
            r.advance.eq(self.consume & self.present),
            rp.adr.eq(r.binary), self.read_data.eq(rp.dat_r)]
