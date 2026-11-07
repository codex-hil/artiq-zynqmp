# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated length fix derived from ARTIQ gateware/drtio/aux_controller.py.

Upstream Receiver retained except FRAME limit/priority, DISCARD modulo full check and registered Gray pointer ownership.
No native installation mutation. Registered Gray pointer CDC candidate; physical timing/reset remains UNQUALIFIED.
Source attribution: M-Labs ARTIQ, pinned checkout source in evidence report.
"""
from migen import *
from migen.genlib.cdc import MultiReg, PulseSynchronizer
from misoc.interconnect.csr import *
from misoc.interconnect import stream
from artiq.gateware.drtio.aux_controller import max_packet, aux_buffer_count

class GrayBoundedReceiver(Module, AutoCSR):
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

        # Registered source Gray words cross; decoded binary stays local.
        from aux_gray_pointer import AuxGrayPointer
        self.submodules.write_position = wp = AuxGrayPointer(log2_int(aux_buffer_count))
        self.submodules.read_position = rp = AuxGrayPointer(log2_int(aux_buffer_count),
            source="sys", destination="rtio_rx")
        write_pointer, write_pointer_sys = wp.binary, wp.remote
        read_pointer, read_pointer_rx = rp.binary, rp.remote
        signal_error = PulseSynchronizer("rtio_rx", "sys")
        self.comb += rp.advance.eq(self.aux_rx_present.re & self.aux_rx_present.w)

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

        # Explicit modulo pointer width: Migen addition otherwise grows a bit.
        next_write_pointer = Signal.like(write_pointer)
        self.comb += next_write_pointer.eq(write_pointer + 1)
        fsm.act("SIGNAL_FRAME",
            NextState("IDLE"),
            If(next_write_pointer == read_pointer_rx,
                # on full buffer, overwrite only current frame
                signal_error.i.eq(1)
            ).Else(
                wp.advance.eq(1)
            ),
            If(converter.source.stb, signal_error.i.eq(1))
        )


