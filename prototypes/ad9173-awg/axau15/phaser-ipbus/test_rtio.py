import importlib.util
import pytest
from pathlib import Path
import env
from migen import *
from types import SimpleNamespace
from envelope import EnvelopePlayer, ARM, ABORTED
from registers import Registers
from test_envelope_registers import access
from rtio_endpoint import EnvelopeRTIO, start_word, FIRE, CANCEL, STALE_ARM, NOT_ARMED
from rtio_cdc import EnvelopeRTIOBridge

# Use the actual upstream RTLink types without importing a second full ARTIQ
# runtime into the pinned Migen environment. Integrators pass their own module.
RTLINK_PATH = Path('/srv/codex-hil-data/artiq-zynqmp/reference/artiq/artiq/gateware/rtio/rtlink.py')
spec = importlib.util.spec_from_file_location('upstream_rtlink', RTLINK_PATH)
rtlink = importlib.util.module_from_spec(spec);spec.loader.exec_module(rtlink)

class DUT(Module):
    def __init__(self, bridge=False):
        self.submodules.player = p = EnvelopePlayer()
        dsp = SimpleNamespace(held=Signal(672), request=Signal(), ack=Signal(), mute=Signal())
        self.submodules.regs = ClockDomainsRenamer('net')(Registers(dsp, p))
        self.submodules.rtio = (EnvelopeRTIOBridge if bridge else EnvelopeRTIO)(p, rtlink)
        if bridge:
            self.clock_domains.cd_rio_phy = ClockDomain('rio_phy')
            self.clock_domains.cd_jesd = ClockDomain('jesd')


def prepare(d, entries, repeats=1):
    for index, (cycles, a, b) in enumerate(entries):
        for field, value in enumerate((cycles, a, b)):
            yield from access(d.regs, 0x400+index*4+field, value)
    yield from access(d.regs, 0x23, len(entries))
    yield from access(d.regs, 0x24, repeats)
    yield from access(d.regs, 0x25, ARM)
    for _ in range(2000):
        if (yield from access(d.regs, 0x27)):break
    else:raise AssertionError('Not armed')
    assert (yield from access(d.regs, 0x20)) == 1
    return (yield from access(d.regs, 0x28))


def test_arm_prevalidates_and_synchronous_fire_has_no_ram_bubble():
    d = DUT();go = []; samples = []; responses = [];result = {}
    entries = [(1, 11, 21), (1, 12, 22), (3, 13, 23), (1, 14, 24)]
    def host():
        # Endpoint needs valid timeline before ARM; otherwise it holds zero.
        for _ in range(30):yield
        tag = yield from prepare(d, entries, 3)
        for _ in range(30):
            assert (yield d.player.playing) == 0
            assert (yield d.player.gains[0]) == 0
            yield
        for address, value in [(0x400, 2), (0x23, 2), (0x24, 2), (0x14, 1), (0x25, 1)]:
            yield from access(d.regs, address, value, True)
        go.append(tag)
        for _ in range(1000):
            if not (yield from access(d.regs, 0x20)):break
        else:raise AssertionError('No completion')
        result['tag'] = tag
    @passive
    def events():
        yield d.rtio.enable.eq(1)
        sent = False
        while True:
            if go and not sent:
                yield d.rtio.rtlink.o.data.eq(start_word(go[0]))
                yield d.rtio.rtlink.o.stb.eq(1);sent = True
            else:yield d.rtio.rtlink.o.stb.eq(0)
            if (yield d.rtio.rtlink.i.stb):responses.append((yield d.rtio.rtlink.i.data)&15)
            if (yield d.player.playing):samples.append(((yield d.player.gains[0]), (yield d.player.gains[1])))
            yield
    run_simulation(d, {'net':host(), 'jesd':events()}, clocks={'net':10, 'jesd':6})
    assert samples == [(a,b) for cycles,a,b in entries for _ in range(cycles)]*3
    assert responses == [0] and result['tag'] == 1


def test_stale_start_rejected_and_abort_wins():
    d = DUT(); commands = [];responses = []
    def host():
        for _ in range(30):yield
        old = yield from prepare(d, [(100, 11, 21)])
        yield from access(d.regs, 0x26, 1)
        for _ in range(100):
            if not (yield from access(d.regs, 0x20)):break
        tag = yield from prepare(d, [(100, 12, 22)])
        assert tag != old
        commands.append(start_word(old))
        for _ in range(30):yield
        assert (yield d.player.armed) and not (yield d.player.playing)
        commands.append(CANCEL)
        for _ in range(100):
            if not (yield from access(d.regs, 0x20)):break
        commands.append(start_word(tag))
        for _ in range(30):yield
        assert (yield d.player.mode) and not (yield d.player.playing)
    @passive
    def events():
        yield d.rtio.enable.eq(1)
        while True:
            yield d.rtio.rtlink.o.stb.eq(0)
            if commands:
                yield d.rtio.rtlink.o.data.eq(commands.pop(0));yield d.rtio.rtlink.o.stb.eq(1)
            if (yield d.rtio.rtlink.i.stb):responses.append((yield d.rtio.rtlink.i.data)&15)
            yield
    run_simulation(d, {'net':host(), 'jesd':events()}, clocks={'net':10, 'jesd':6})
    assert responses == [STALE_ARM, 0, NOT_ARMED]


def test_asynchronous_mailbox_fire_and_disable_flush():
    d = DUT(bridge=True); commands = [];responses = [];seen = [];disable = [];done = []
    def host():
        for _ in range(100):yield
        tag = yield from prepare(d, [(100000, 11, 21)])
        commands.append(start_word(tag))
        for _ in range(500):
            yield
            if (yield d.player.playing):break
        else:raise AssertionError('Bridge did not start')
        disable.append(True)
        for _ in range(100):yield
        assert not (yield d.player.playing) and not (yield d.player.armed)
        assert (yield d.player.mode) == 1
        for _ in range(100):
            if not (yield from access(d.regs, 0x20)):break
        done.append(True)
    @passive
    def events():
        yield d.rtio.enable.eq(1)
        while True:
            yield d.rtio.rtlink.o.stb.eq(0)
            if disable:yield d.rtio.enable.eq(0)
            if commands and (yield d.rtio.ready):
                yield d.rtio.rtlink.o.data.eq(commands.pop(0));yield d.rtio.rtlink.o.stb.eq(1)
            if (yield d.rtio.rtlink.i.stb):responses.append((yield d.rtio.rtlink.i.data)&15)
            yield
    run_simulation(d, {'net':host(), 'rio_phy':events()}, clocks={'net':10, 'rio_phy':8, 'jesd':6})
    assert done and not commands


@pytest.mark.parametrize("domain_reset", [False, True])
def test_bridge_source_reset_discards_old_start_before_rearm(domain_reset):
    d = DUT(bridge=True);commands=[];reset=[];rearm=[];responses=[]
    def host():
        for _ in range(100):yield
        old = yield from prepare(d, [(100000, 17, 29)])
        commands.append(start_word(old))
        for _ in range(100):yield
        reset.append(True)
        for _ in range(100):yield
        assert not (yield d.player.playing)
        for _ in range(100):
            if not (yield from access(d.regs, 0x20)):break
        rearm.append(True)
        for _ in range(100):yield
        tag = yield from prepare(d, [(100000, 31, 41)])
        assert tag != old
        commands.append(start_word(old))
        for _ in range(100):yield
        assert (yield d.player.armed) and not (yield d.player.playing)
        commands.append(start_word(tag))
        for _ in range(100):yield
        assert (yield d.player.playing)
        commands.append(CANCEL)
        for _ in range(100):yield
        assert not (yield d.player.playing)
    @passive
    def events():
        yield d.rtio.enable.eq(1)
        while True:
            if domain_reset:yield d.cd_rio_phy.rst.eq(bool(reset) and not rearm)
            else:yield d.rtio.reset.eq(bool(reset) and not rearm)
            yield d.rtio.rtlink.o.stb.eq(0)
            if commands and (yield d.rtio.ready):
                yield d.rtio.rtlink.o.data.eq(commands.pop(0));yield d.rtio.rtlink.o.stb.eq(1)
            if (yield d.rtio.rtlink.i.stb):responses.append((yield d.rtio.rtlink.i.data)&15)
            yield
    run_simulation(d, {'net':host(), 'rio_phy':events()}, clocks={'net':10, 'rio_phy':14, 'jesd':6})
    assert responses == [0, STALE_ARM, 0, 0]


def test_exact_fire_to_sample_pipeline_latency():
    from envelope import EnvelopeStage
    d=DUT();inputs=[[(Signal((16,True),reset=16384), Signal((16,True))) for _ in range(2)] for _ in range(2)]
    d.submodules.stage=stage=EnvelopeStage(inputs,d.player)
    go=[];trace=[]
    def host():
        for _ in range(30):yield
        tag=yield from prepare(d,[(1,16384,16384),(1,0,0)])
        for _ in range(20):yield
        go.append(tag)
        for _ in range(100):yield
    @passive
    def events():
        yield d.rtio.enable.eq(1)
        sent=False
        while True:
            yield d.rtio.rtlink.o.stb.eq(0)
            if go and not sent:
                yield d.rtio.rtlink.o.data.eq(start_word(go[0]));yield d.rtio.rtlink.o.stb.eq(1);sent=True
            trace.append(((yield d.rtio.rtlink.o.stb),(yield d.player.started),(yield stage.samples[0][0][0])))
            yield
    run_simulation(d,{'net':host(),'jesd':events()},clocks={'net':10,'jesd':6})
    fire=next(i for i,row in enumerate(trace) if row[0])
    started=next(i for i,row in enumerate(trace) if row[1])
    nonzero=[i for i,row in enumerate(trace) if i>=fire and row[2]]
    assert started==fire+1
    assert nonzero==[started+6]
    assert trace[nonzero[0]][2]==8192


def test_bridge_back_to_back_queries_have_exactly_one_response():
    d=DUT(bridge=True);received=[];sent=Signal(7)
    # RTL producer drives at the first available cycle, avoiding simulator
    # generator/delta-cycle ambiguity when sampling ready then driving stb.
    d.comb += [d.rtio.rtlink.o.data.eq(0),
               d.rtio.rtlink.o.stb.eq(d.rtio.ready & (sent < 50))]
    d.sync.rio_phy += If(d.rtio.rtlink.o.stb & ~d.rtio.rtlink.o.busy, sent.eq(sent+1))
    def events():
        yield d.rtio.enable.eq(1)
        for _ in range(10000):
            if (yield d.rtio.rtlink.i.stb):received.append((yield d.rtio.rtlink.i.data)&15)
            if len(received)==50:
                for _ in range(30):
                    yield
                    assert not (yield d.rtio.rtlink.i.stb)
                assert (yield sent)==50
                return
            yield
        raise AssertionError(((yield sent),len(received)))
    run_simulation(d,{'rio_phy':events()},clocks={'net':10,'rio_phy':8,'jesd':14})
    assert received==[0]*50


def test_one_source_cycle_reset_is_held_until_slow_jesd_observes_it():
    d=DUT(bridge=True);pulse=[];pulsed=[]
    def host():
        for _ in range(400):yield
        yield from prepare(d,[(100000,17,29)])
        pulse.append(True)
        for _ in range(1200):yield
        assert pulsed
        assert not (yield d.player.playing) and not (yield d.player.armed)
        assert (yield d.player.result)==ABORTED
        assert (yield d.rtio.ready)
        assert not (yield from access(d.regs,0x20))
    @passive
    def events():
        yield d.rtio.enable.eq(1)
        while True:
            yield d.rtio.reset.eq(0)
            if pulse and not pulsed:
                yield d.rtio.reset.eq(1);pulsed.append(True)
            yield
    run_simulation(d,{'net':host(),'rio_phy':events()},clocks={'net':10,'rio_phy':8,'jesd':100})
