"""Time-slotted packet loopback through one physical raw20 GTH.

Upstream RT packet engines are unchanged. A CRI diagnostic responder checks
fields, not a local RTIO/SED or production satellite. LGPL-3.0-or-later.
"""
from types import SimpleNamespace
from migen import Module, Signal, Cat, If, Mux, ClockDomainsRenamer
from migen.genlib.cdc import MultiReg, PulseSynchronizer
from migen.genlib.fifo import AsyncFIFO
from misoc.interconnect.csr import AutoCSR, CSRStorage, CSRStatus
from artiq.gateware.drtio.link_layer import LinkLayerTX, LinkLayerRX
from artiq.gateware.drtio.rt_packet_master import RTPacketMaster
from satellite_packet import CheckedRTPacketSatellite
from artiq.gateware.rtio.cri import commands
from raw20_codec import Raw20Codec
from protocol_probe import WordAligner
from monitor import GrayCounter

TIMESTAMP = 0x1122334455667788
CHANNEL = 0x123456
ADDRESS = 0x5a
WRITE_DATA = 0x12345678 | (1 << 400)
READ_DATA = 0x6a5b4c3d
BUFFER_SPACE = 0x3456


def packet_interface():
    return SimpleNamespace(tx_rt_frame=Signal(), tx_rt_data=Signal(16),
                           rx_rt_frame=Signal(), rx_rt_data=Signal(16))


class PacketProbe(Module, AutoCSR):
    def __init__(self, phase_bits=15, counter_width=32):
        if phase_bits < 8: raise ValueError('Packet slots require at least 256 cycles')
        if not 8 <= counter_width <= 32: raise ValueError('Counter width must be 8..32')
        self.enable = CSRStorage(1, name='enable')
        self.command = CSRStorage(4, name='command')
        self.drop_reply = CSRStorage(1, name='drop_reply')
        self.alignment = CSRStatus(6, name='alignment')
        self.tx_raw, self.rx_raw = Signal(20), Signal(20)
        self.submodules.aligner = ClockDomainsRenamer('gth_rx')(WordAligner())
        self.submodules.codec = ClockDomainsRenamer('gth_tx')(Raw20Codec(rx_domain='gth_rx'))
        self.submodules.tx = ClockDomainsRenamer('gth_tx')(LinkLayerTX(self.codec.encoder))
        self.submodules.rx = ClockDomainsRenamer('gth_rx')(LinkLayerRX(self.codec.decoders))
        self.comb += [self.aligner.input.eq(self.rx_raw),
                     self.codec.rx_raw.eq(self.aligner.output),
                     self.tx_raw.eq(self.codec.tx_raw)]
        enabled, command, drop, aligned_tx = Signal(), Signal(4), Signal(), Signal()
        command_rx = Signal(4)
        self.specials += [MultiReg(self.enable.storage, enabled, 'gth_tx'),
                         MultiReg(self.command.storage, command, 'gth_tx'),
                         MultiReg(self.command.storage, command_rx, 'gth_rx'),
                         MultiReg(self.drop_reply.storage, drop, 'gth_tx'),
                         MultiReg(self.aligner.aligned, aligned_tx, 'gth_tx'),
                         MultiReg(Cat(self.aligner.aligned,self.aligner.offset),self.alignment.status)]
        phase = Signal(phase_bits)
        self.sync.gth_tx += phase.eq(phase+1)
        direction = phase[-1]
        direction_rx = Signal()
        self.specials += MultiReg(direction, direction_rx, 'gth_rx')
        guard = min(128, 1 << (phase_bits-3))
        start = (phase == guard) & enabled & aligned_tx
        master_ll, satellite_ll = packet_interface(), packet_interface()
        self.submodules.master = ClockDomainsRenamer({'sys':'gth_tx','rtio_rx':'gth_rx'})(RTPacketMaster(master_ll))
        self.submodules.satellite = ClockDomainsRenamer('gth_rx')(CheckedRTPacketSatellite(satellite_ll))
        m, s = self.master, self.satellite
        self.comb += [satellite_ll.rx_rt_frame.eq(self.rx.rt_frame & self.aligner.aligned & ~direction_rx),
                     satellite_ll.rx_rt_data.eq(self.rx.rt_data),
                     master_ll.rx_rt_frame.eq(self.rx.rt_frame & self.aligner.aligned & direction_rx),
                     master_ll.rx_rt_data.eq(self.rx.rt_data)]
        echo_pending, time_pending = Signal(), Signal()
        self.sync.gth_tx += [If(start & (command == 0), echo_pending.eq(1)),
                            If(m.echo_ack, echo_pending.eq(0)),
                            If(start & (command == 1), time_pending.eq(1)),
                            If(m.set_time_ack, time_pending.eq(0))]
        self.comb += [m.echo_stb.eq(echo_pending), m.set_time_stb.eq(time_pending),
                     m.tsc_value.eq(TIMESTAMP),
                     m.sr_stb.eq(start & (command >= 2) & (command <= 7)),
                     m.sr_notwrite.eq(command != 2),
                     m.sr_timestamp.eq(TIMESTAMP), m.sr_chan_sel.eq(CHANNEL),
                     m.sr_address.eq(Mux(command == 2, ADDRESS, Mux((command == 3) | (command == 7),0,1))),
                     m.sr_data.eq(WRITE_DATA), m.buffer_space_not_ack.eq(1), m.read_not_ack.eq(1)]
        # Diagnostic CRI backend. All fields are checked; no TTL/SED claim.
        self.comb += [s.cri.o_buffer_space_valid.eq(command_rx != 7),
                     s.cri.o_buffer_space.eq(BUFFER_SPACE),
                     s.cri.i_status.eq(Mux(command_rx == 5,1,Mux(command_rx == 6,2,0))),
                     s.cri.i_data.eq(READ_DATA), s.cri.i_timestamp.eq(TIMESTAMP+1)]
        self.submodules.reply_fifo = ClockDomainsRenamer({'write':'gth_rx','read':'gth_tx'})(AsyncFIFO(17,64))
        f = self.reply_fifo
        previous = Signal()
        self.sync.gth_rx += previous.eq(satellite_ll.tx_rt_frame)
        capture = satellite_ll.tx_rt_frame | previous
        # Include one frame=0 end marker, preserving complete packet boundaries.
        self.comb += [f.din.eq(Cat(satellite_ll.tx_rt_data,satellite_ll.tx_rt_frame)),
                     f.we.eq(capture), f.re.eq(direction & f.readable & (phase >= (1 << (phase_bits-1))+guard))]
        malformed = (command == 8) | (command == 9)
        self.comb += [self.tx.rt_frame.eq(Mux(direction,
            f.re & f.dout[16] & ~drop,
            Mux(malformed, Mux(command == 8, enabled & aligned_tx &
                (phase >= guard) & (phase < guard+6), start), master_ll.tx_rt_frame))),
            self.tx.rt_data.eq(Mux(direction,f.dout[:16],
            Mux(malformed,Mux(command == 8,0xff,2),master_ll.tx_rt_data)))]
        self.counts = {}
        names = ('requests','echo_replies','buffer_replies','read_replies','writes',
                 'time_loads','sat_errors','master_errors','timeouts','fifo_errors',
                 'unknown_errors','truncated_errors','buffer_timeouts')
        domains = ('gth_tx','gth_rx','gth_tx','gth_tx','gth_rx',
                   'gth_rx','gth_rx','gth_tx','gth_tx','gth_rx',
                   'gth_rx','gth_rx','gth_rx')
        for name, domain in zip(names,domains):
            c = GrayCounter(domain, width=counter_width)
            setattr(self.submodules,name+'_count',c)
            self.counts[name] = c
            reg = CSRStatus(32,name=name)
            setattr(self,name,reg)
            self.comb += reg.status.eq(c.value)
        write = s.cri.cmd == commands['write']
        bad_write = write & ((s.cri.o_data != WRITE_DATA) | (s.cri.o_timestamp != TIMESTAMP) |
                            (s.cri.chan_sel != CHANNEL) | (s.cri.o_address != ADDRESS))
        read = s.cri.cmd == commands['read']
        bad_read = read & ((s.cri.i_timeout != TIMESTAMP) | (s.cri.chan_sel != CHANNEL))
        buffer = s.cri.cmd == commands['get_buffer_space']
        bad_buffer = buffer & (s.cri.chan_sel != (CHANNEL & 0xff0000))
        bad_read_reply = m.read_not & ((m.read_no_event != ((command == 5) | (command == 6))) |
            (m.read_no_event & (m.read_is_overflow != (command == 6))) |
            (~m.read_no_event & ((m.read_data != READ_DATA) | (m.read_timestamp != TIMESTAMP+1))))
        self.comb += [self.counts['unknown_errors'].enable.eq(s.unknown_packet_type),
                     self.counts['truncated_errors'].enable.eq(s.packet_truncated),
                     self.counts['buffer_timeouts'].enable.eq(s.buffer_space_timeout),
                     self.counts['requests'].enable.eq(start),
                     self.counts['echo_replies'].enable.eq(m.echo_received_now),
                     self.counts['buffer_replies'].enable.eq(m.buffer_space_not),
                     self.counts['read_replies'].enable.eq(m.read_not),
                     self.counts['writes'].enable.eq(write),
                     self.counts['time_loads'].enable.eq(s.tsc_load),
                     self.counts['sat_errors'].enable.eq(s.unknown_packet_type | s.packet_truncated |
                        s.buffer_space_timeout | bad_write | bad_read | bad_buffer |
                        (s.tsc_load & (s.tsc_load_value != TIMESTAMP))),
                     self.counts['master_errors'].enable.eq(m.err_unknown_packet_type | m.err_packet_truncated |
                        bad_read_reply | (m.buffer_space_not & (m.buffer_space != BUFFER_SPACE)) |
                        (m.sr_stb & ~m.sr_ack)),
                     self.counts['fifo_errors'].enable.eq(capture & ~f.writable)]
        self.submodules.echo_notify = PulseSynchronizer('gth_rx','gth_tx')
        self.comb += self.echo_notify.i.eq(m.echo_received_now)
        completed, armed = Signal(), Signal()
        self.sync.gth_tx += [If(start,completed.eq(0),armed.eq(1)),
                            If(phase == (1 << phase_bits)-1,armed.eq(0)),
                            If(self.echo_notify.o | m.read_not | m.buffer_space_not,completed.eq(1))]
        expected_reply = (command == 0) | (command == 3) | ((command >= 4) & (command <= 6))
        self.comb += self.counts['timeouts'].enable.eq((phase == (1 << phase_bits)-1) &
                                                     armed & aligned_tx & expected_reply & ~completed)
