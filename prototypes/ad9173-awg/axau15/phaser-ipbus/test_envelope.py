import env
from migen import *
from envelope import EnvelopePlayer, EnvelopeStage, START, OK, INVALID, ABORTED


def run_program(entries, repeats=1, abort_after=None):
    d = EnvelopePlayer(); observed = []; result = {}
    def host():
        for index, entry in enumerate(entries):
            for field, value in enumerate(entry):
                yield d.write_address.eq(index*4+field)
                yield d.write_data.eq(value)
                yield d.write_enable.eq(1)
                yield
                yield d.write_enable.eq(0)
                yield
        yield d.length.eq(len(entries)); yield d.repeats.eq(repeats)
        yield d.command.eq(START); yield d.request.eq(1)
        for _ in range(5000):
            yield
            if (yield d.ack):
                result['code'] = (yield d.result)
                result['mode'] = (yield d.mode)
                result['gains'] = [(yield d.gains[0]), (yield d.gains[1])]
                result['abort_ack'] = (yield d.abort_ack)
                return
        raise AssertionError('Playback did not acknowledge')
    @passive
    def sample():
        while True:
            if (yield d.playing):
                observed.append(((yield d.gains[0]), (yield d.gains[1])))
                if abort_after is not None and len(observed) == abort_after:
                    yield d.abort_request.eq(1)
            yield
    run_simulation(d, {'net': host(), 'jesd': sample()}, clocks={'net': 10, 'jesd': 6})
    return observed, result


def test_single_cycle_entries_and_repeat_boundary():
    entries = [(1, 11, 21), (1, 12, 22), (3, 13, 23), (1, 14, 24)]
    samples, result = run_program(entries, repeats=3)
    expected = [(a, b) for duration, a, b in entries for _ in range(duration)]*3
    assert samples == expected
    assert result == {'code': OK, 'mode': 1, 'gains': [0, 0], 'abort_ack': 0}


def test_single_entry_and_maximum_length():
    assert run_program([(1, 0x7fff, 0x7fff0000)], 4)[0] == [(0x7fff, 0x7fff0000)]*4
    entries = [(1+(i%3), i+1, 255-i) for i in range(256)]
    samples, result = run_program(entries)
    assert samples == [(a, b) for duration, a, b in entries for _ in range(duration)]
    assert result['code'] == OK


def test_invalid_program_never_emits_partial_pulse():
    samples, result = run_program([(10, 11, 21), (0, 12, 22)])
    assert samples == [] and result['code'] == INVALID
    samples, result = run_program([(1, 1, 1)], repeats=0)
    assert samples == [] and result['code'] == INVALID


def test_abort_drains_and_acknowledges():
    samples, result = run_program([(0xffffffff, 11, 21)], repeats=0xffffffff, abort_after=10)
    assert 10 <= len(samples) <= 14
    assert result['code'] == ABORTED and result['abort_ack'] == 1
    assert result['gains'] == [0, 0]


def test_complex_scaling_saturation_and_bypass():
    m = Module(); player = EnvelopePlayer()
    inputs = [[(Signal((16, True)), Signal((16, True))) for _ in range(2)] for _ in range(2)]
    m.submodules.stage = stage = EnvelopeStage(inputs, player)
    def test():
        for mode, sample, gain in [(0, (32767, -32768), (0, 0)),
                                    (1, (16000, -8000), (16384, 0)),
                                    (1, (16000, -8000), (0, 16384)),
                                    (1, (32767, -32768), (32767, 32767))]:
            yield player.mode.eq(mode)
            for ch in range(2):
                yield player.gains[ch].eq((gain[0]&65535) | ((gain[1]&65535)<<16))
                for i, q in inputs[ch]:
                    yield i.eq(sample[0]); yield q.eq(sample[1])
            for _ in range(12):yield
            if not mode:expected = sample
            else:
                real = sample[0]*gain[0]-sample[1]*gain[1]
                imag = sample[0]*gain[1]+sample[1]*gain[0]
                expected = tuple(max(-32768, min(32767, (v+16383)>>15)) for v in [real, imag])
            for ch in stage.samples:
                for i, q in ch:
                    assert ((yield i), (yield q)) == expected
    run_simulation(m, {'jesd': test()}, clocks={'jesd': 6})


def test_sample_pipeline_alignment_at_every_cycle():
    """Changing mode, gain and every sample lane must share exactly six clocks."""
    m = Module(); player = EnvelopePlayer()
    inputs = [[(Signal((16, True)), Signal((16, True))) for _ in range(2)] for _ in range(2)]
    m.submodules.stage = stage = EnvelopeStage(inputs, player)
    def test():
        expected = []
        for cycle in range(90):
            mode = int(12 <= cycle < 55 or cycle >= 67)
            gains = [(16384, 0), (0, -16384)] if cycle % 3 else [(0, 0), (32767, 0)]
            yield player.mode.eq(mode)
            frame = []
            for ch in range(2):
                a, b = gains[ch]
                yield player.gains[ch].eq((a&65535) | ((b&65535)<<16))
                for lane, (i, q) in enumerate(inputs[ch]):
                    x, y = 1000+cycle*101+ch*300+lane*50, -2000+cycle*13+lane*71
                    yield i.eq(x); yield q.eq(y)
                    frame.append((x, y) if not mode else tuple((v+16383)>>15 for v in (x*a-y*b, x*b+y*a)))
            expected.append(frame)
            yield
            if cycle >= 6:
                got = []
                for channel in stage.samples:
                    for i, q in channel:got.append(((yield i), (yield q)))
                assert got == expected[cycle-6], (cycle, got, expected[cycle-6])
    run_simulation(m, {'jesd': test()}, clocks={'jesd': 6})


def test_abort_pending_start_before_playback_enters_zero_mode():
    d = EnvelopePlayer()
    def test():
        yield d.command.eq(START);yield d.length.eq(1);yield d.repeats.eq(1)
        yield d.request.eq(1);yield d.abort_request.eq(1)
        for _ in range(100):
            yield
            if (yield d.abort_ack):break
        else:raise AssertionError('Pending abort was not acknowledged')
        assert (yield d.ack) == 1
        assert (yield d.mode) == 1 and (yield d.playing) == 0
        assert (yield d.result) == ABORTED
    run_simulation(d, {'net':test()}, clocks={'net':10, 'jesd':60})
