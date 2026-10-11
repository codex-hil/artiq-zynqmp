"""Whole-packet AUX TX crossing, LGPL-3.0-or-later.

PS-side upstream AUX transmitter remains in sys. LinkLayerTX is in gth_tx.
Both domains must reset together: independent GT resets require aborting and
resetting this bridge, not replaying a partially transmitted packet.
"""
from migen import Module, Signal, Cat, If, ClockDomainsRenamer
from migen.genlib.cdc import MultiReg
from migen.genlib.fifo import AsyncFIFOBuffered


class AuxTxCDC(Module):
    def __init__(self, width=4, max_bytes=1024):
        self.input_frame = Signal()
        self.input_data = Signal(width)
        self.input_ack = Signal()
        self.output_frame = Signal()
        self.output_data = Signal(width)
        self.output_ack = Signal()
        self.busy = Signal()
        # Packet plus one end marker; power-of-two capacity for Gray pointers.
        tokens = (max_bytes * 8 + width - 1) // width + 1
        depth = 1 << (tokens - 1).bit_length()
        self.submodules.fifo = ClockDomainsRenamer(
            {'write': 'sys', 'read': 'gth_tx'})(AsyncFIFOBuffered(width + 1, depth))
        f = self.fifo
        request, completed = Signal(), Signal()
        request_tx, completed_sys = Signal(), Signal()
        self.specials += [MultiReg(request, request_tx, 'gth_tx'),
                          MultiReg(completed, completed_sys, 'sys')]
        previous_frame = Signal()
        accept = Signal()
        self.comb += [self.busy.eq(request != completed_sys),
                     self.input_ack.eq(~self.busy & f.writable),
                     accept.eq(self.input_ack & (self.input_frame | previous_frame)),
                     f.din.eq(Cat(self.input_data, self.input_frame)), f.we.eq(accept)]
        self.sync += If(self.input_ack,
            previous_frame.eq(self.input_frame),
            If(previous_frame & ~self.input_frame, request.eq(~request)))
        transmitting = Signal()
        self.comb += [transmitting.eq(request_tx != completed),
                     self.output_frame.eq(transmitting & f.readable & f.dout[width]),
                     self.output_data.eq(f.dout[:width]),
                     f.re.eq(transmitting & f.readable & self.output_ack)]
        self.sync.gth_tx += If(f.re & ~f.dout[width], completed.eq(request_tx))
