"""Finite local I/Q envelope playback, independent of Ethernet arrival timing.

One entry holds duration (JESD cycles), CH0 IQ and CH1 IQ, each signed Q1.15.
The whole program is validated before playback. RAM belongs to the writer
until request, then to the player until acknowledgement (including drain).
This is a local sequencer, not MIQRO or an RTIO timestamp interface.
"""
import env
from migen import *
from migen.genlib.cdc import MultiReg
from misoc.cores.duc import ComplexMultiplier, saturate

DEPTH = 256
START, BYPASS = 1, 2
OK, ABORTED, INVALID = 0, 1, 2

class EnvelopePlayer(Module):
    def __init__(self):
        self.write_address = Signal(10)
        self.write_data = Signal(32)
        self.write_enable = Signal()
        self.read_data = Signal(32)
        self.request = Signal()
        self.ack = Signal()
        self.command = Signal(2)
        self.length = Signal(9)
        self.repeats = Signal(32)
        self.abort_request = Signal()
        self.abort_ack = Signal()
        self.mode = Signal()
        self.playing = Signal()
        self.result = Signal(2)
        self.gains = [Signal(32) for _ in range(2)]
        self.index = Signal(8)
        request, abort = Signal(), Signal()
        self.specials += [MultiReg(self.request, request, 'jesd'),
                          MultiReg(self.abort_request, abort, 'jesd')]
        mem = Memory(96, DEPTH, init=[0]*DEPTH, name='envelope_ram')
        wp = mem.get_port(write_capable=True, we_granularity=32,
                          mode=READ_FIRST, clock_domain='net')
        rp = mem.get_port(mode=READ_FIRST, clock_domain='jesd')
        self.specials += mem, wp, rp
        self.comb += [wp.adr.eq(self.write_address[2:]),
                      wp.dat_w.eq(Replicate(self.write_data, 3)),
                      wp.we.eq(Mux(self.write_enable & (self.write_address[:2] != 3),
                                   1 << self.write_address[:2], 0)),
                      self.read_data.eq(Array([wp.dat_r[:32], wp.dat_r[32:64],
                                               wp.dat_r[64:], Constant(0, 32)])[self.write_address[:2]])]
        idle, dispatch, check_fetch, check_read, prime0, prime1, play, drain = range(8)
        state = Signal(3)
        self.active_config = Signal(43, name="envelope_active_config")
        self.active_config.attr.add("dont_touch")
        self.active_config.attr.add(("extract_enable", "yes"))
        command = self.active_config[:2]
        config_length = self.active_config[2:11]
        config_repeats = self.active_config[11:]
        serving, aborting, abort_token = Signal(), Signal(), Signal()
        length = Signal(9); repeats = Signal(32); remaining = Signal(32)
        check_index = Signal(8); drain_count = Signal(4)
        next_index, ahead = Signal(8), Signal(8)
        self.comb += [
            next_index.eq(Mux(self.index == length-1, 0, self.index+1)),
            ahead.eq(Mux(next_index == length-1, 0, next_index+1)),
            rp.adr.eq(0),
            Case(state, {
                check_fetch: rp.adr.eq(check_index),
                check_read: rp.adr.eq(check_index),
                prime1: rp.adr.eq(Mux(length == 1, 0, 1)),
                play: rp.adr.eq(Mux(remaining == 0, ahead, next_index)),
            })]
        capture = Signal(name="envelope_capture")
        capture.attr.add(("direct_enable", "yes"))
        capture.attr.add("keep")
        self.comb += capture.eq((state == idle) & (request != self.ack) &
                                ~((abort != self.abort_ack) & ~aborting))
        self.sync.jesd += If(capture,
            self.active_config.eq(Cat(self.command, self.length, self.repeats)))
        self.sync.jesd += If((abort != self.abort_ack) & ~aborting,
            aborting.eq(1), abort_token.eq(abort), serving.eq(request),
            If(request != self.ack, self.mode.eq(1)),
            self.playing.eq(0), self.gains[0].eq(0), self.gains[1].eq(0),
            self.result.eq(ABORTED), drain_count.eq(8), state.eq(drain)
        ).Else(Case(state, {
            idle: If(request != self.ack,
                serving.eq(request), state.eq(dispatch)),
            dispatch: [self.result.eq(OK), self.playing.eq(0),
                self.gains[0].eq(0), self.gains[1].eq(0),
                If(command == BYPASS,
                    self.mode.eq(0), drain_count.eq(8), state.eq(drain)
                ).Elif((command != START) | (config_length == 0) |
                       (config_length > DEPTH) | (config_repeats == 0),
                    self.result.eq(INVALID), self.mode.eq(1),
                    drain_count.eq(8), state.eq(drain)
                ).Else(self.mode.eq(1), length.eq(config_length), repeats.eq(config_repeats),
                       check_index.eq(0), state.eq(check_fetch))],
            check_fetch: state.eq(check_read),
            check_read: If(rp.dat_r[:32] == 0,
                self.result.eq(INVALID), drain_count.eq(8), state.eq(drain)
            ).Elif(check_index == length-1, state.eq(prime0)
            ).Else(check_index.eq(check_index+1), state.eq(check_fetch)),
            prime0: state.eq(prime1),
            prime1: [self.index.eq(0), remaining.eq(rp.dat_r[:32]-1),
                     self.gains[0].eq(rp.dat_r[32:64]), self.gains[1].eq(rp.dat_r[64:]),
                     self.playing.eq(1), state.eq(play)],
            play: If(remaining != 0, remaining.eq(remaining-1)).Else(
                If((self.index == length-1) & (repeats == 1),
                    self.playing.eq(0), self.gains[0].eq(0), self.gains[1].eq(0),
                    drain_count.eq(8), state.eq(drain)
                ).Else(
                    If(self.index == length-1, repeats.eq(repeats-1)),
                    self.index.eq(next_index), remaining.eq(rp.dat_r[:32]-1),
                    self.gains[0].eq(rp.dat_r[32:64]), self.gains[1].eq(rp.dat_r[64:]))),
            drain: If(drain_count != 0, drain_count.eq(drain_count-1)).Else(
                self.ack.eq(serving),
                If(aborting, self.abort_ack.eq(abort_token), aborting.eq(0)), state.eq(idle)),
        }))

class EnvelopeStage(Module):
    """Six-cycle complex scaling, saturating Q1.15, equally delayed CW bypass."""
    def __init__(self, samples, player):
        self.samples = []
        mode = [Signal() for _ in range(6)]
        self.sync.jesd += [mode[0].eq(player.mode)] + [mode[k].eq(mode[k-1]) for k in range(1, 6)]
        for ch, inputs in enumerate(samples):
            outputs = []; self.samples.append(outputs)
            for i, q in inputs:
                mul = ClockDomainsRenamer('jesd')(ComplexMultiplier(16, 16, 33))
                self.submodules += mul
                self.comb += [mul.a.i.eq(i), mul.a.q.eq(q),
                              mul.b.i.eq(player.gains[ch][:16]), mul.b.q.eq(player.gains[ch][16:])]
                output = []
                for source, product in [(i, mul.p.i), (q, mul.p.q)]:
                    raw = [Signal((16, True)) for _ in range(6)]
                    scaled = Signal((16, True)); rounded = Signal((19, True)); result = Signal((16, True))
                    self.comb += [rounded.eq((product+16383) >> 15), result.eq(Mux(mode[-1], scaled, raw[-1]))]
                    self.sync.jesd += [raw[0].eq(source)] + [raw[k].eq(raw[k-1]) for k in range(1, 6)]
                    self.sync.jesd += saturate(scaled, rounded)
                    output.append(result)
                outputs.append(tuple(output))
