# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated length fix derived from ARTIQ gateware/drtio/aux_controller.py.

Original upstream Receiver retained except FRAME limit/priority and DISCARD.
No native installation mutation. Binary pointer CDC remains UNQUALIFIED.
Source attribution: M-Labs ARTIQ, pinned checkout source in evidence report.
"""
from migen import *
from migen.genlib.cdc import MultiReg, PulseSynchronizer
from misoc.interconnect.csr import *
from misoc.interconnect import stream
from artiq.gateware.drtio.aux_controller import max_packet, aux_buffer_count

class BoundedReceiver(Module, AutoCSR):
    def __init__(self, link_layer, min_mem_dw):
        self.aux_rx_present = CSR()
        self.aux_rx_error = CSR()
        self.aux_read_pointer = CSR(log2_int(aux_buffer_count))

        ll_dw = len(link_layer.rx_aux_data)
        mem_dw = max(min_mem_dw, ll_dw)
        self.specials.mem = Memory(mem_dw, aux_buffer_count*max_packet//(mem_dw//8))

        converter = ClockDomainsRenamer("rtio_rx")(
            stream.Converter(ll_dw, mem_dw))
        self.submodules += converter

        # when continuously drained, the Converter accepts data continuously
        frame_r = Signal()
        self.sync.rtio_rx += [
            If(link_layer.rx_aux_stb,
                frame_r.eq(link_layer.rx_aux_frame),
                converter.sink.data.eq(link_layer.rx_aux_data)
            )
        ]
        self.comb += [
            converter.sink.stb.eq(link_layer.rx_aux_stb & frame_r),
            converter.sink.eop.eq(converter.sink.stb & ~link_layer.rx_aux_frame)
        ]

        mem_port = self.mem.get_port(write_capable=True, clock_domain="rtio_rx")
        self.specials += mem_port

        # write pointer represents where the gateware is
        write_pointer = Signal(log2_int(aux_buffer_count))
        write_pointer_sys = Signal.like(write_pointer)
        # read pointer represents where CPU is
        # write reaching read is an error, read reaching write is buffer clear
        read_pointer = Signal.like(write_pointer)
        read_pointer_rx = Signal.like(write_pointer)

        read_pointer.attr.add("no_retiming")
        write_pointer.attr.add("no_retiming")
        signal_error = PulseSynchronizer("rtio_rx", "sys")

        self.specials += [
            MultiReg(read_pointer, read_pointer_rx, "rtio_rx"),
            MultiReg(write_pointer, write_pointer_sys)
        ]

        frame_counter_nbits = bits_for(max_packet) - log2_int(mem_dw//8)
        frame_counter = Signal(frame_counter_nbits)
        # frame counter requires one more bit to represent overflow (bits_for)
        # actual valid packet will be addressed with one bit less
        packet_nbits = frame_counter_nbits - 1
        self.comb += [
            mem_port.adr[:packet_nbits].eq(frame_counter),
            # bits above the frame counter point to current frame
            mem_port.adr[packet_nbits:].eq(write_pointer),
            mem_port.dat_w.eq(converter.source.data),
            converter.source.ack.eq(1),
            self.aux_read_pointer.w.eq(read_pointer)
        ]

        self.submodules += signal_error
        self.sync += [
            If(self.aux_rx_error.re, self.aux_rx_error.w.eq(0)),
            If(signal_error.o, self.aux_rx_error.w.eq(1)),
            self.aux_rx_present.w.eq(~(read_pointer == write_pointer_sys)),
            If(self.aux_rx_present.re & self.aux_rx_present.w,
                read_pointer.eq(read_pointer + 1)),
        ]

        fsm = ClockDomainsRenamer("rtio_rx")(FSM(reset_state="IDLE"))
        self.submodules += fsm

        sop = Signal(reset=1)
        self.sync.rtio_rx += \
            If(converter.source.stb,
                If(converter.source.eop,
                    sop.eq(1)
                ).Else(
                    sop.eq(0)
                )
            )

        fsm.act("IDLE",
            If(converter.source.stb & sop,
                NextValue(frame_counter, frame_counter + 1),
                mem_port.we.eq(1),
                If(converter.source.eop,
                    NextState("SIGNAL_FRAME")
                ).Else(
                    NextState("FRAME")
                )
            ).Else(
                NextValue(frame_counter, 0),
            )
        )
        # Count completed memory words, not bytes. Never write word256 of
        # a256word slot. Oversize rejection takes precedence over EOP publish.
        fsm.act("FRAME",
            If(converter.source.stb,
                If(frame_counter >= max_packet//(mem_dw//8),
                    signal_error.i.eq(1),
                    If(converter.source.eop,
                        NextState("IDLE")
                    ).Else(
                        NextState("DISCARD")
                    )
                ).Else(
                    NextValue(frame_counter, frame_counter + 1),
                    mem_port.we.eq(1),
                    If(converter.source.eop, NextState("SIGNAL_FRAME"))
                )
            )
        )
        fsm.act("DISCARD",
            If(converter.source.stb & converter.source.eop, NextState("IDLE"))
        )

        fsm.act("SIGNAL_FRAME",
            NextState("IDLE"),
            If((write_pointer + 1) == read_pointer_rx,
                # on full buffer, overwrite only current frame
                signal_error.i.eq(1)
            ).Else(
                NextValue(write_pointer, write_pointer + 1)
            ),
            If(converter.source.stb, signal_error.i.eq(1))
        )


