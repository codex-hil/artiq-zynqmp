import env
from types import SimpleNamespace
from migen import *
from registers import Registers
from envelope import EnvelopePlayer

class DUT(Module):
    def __init__(self):
        dsp = SimpleNamespace(held=Signal(672), request=Signal(), ack=Signal(), mute=Signal())
        self.submodules.player = p = EnvelopePlayer()
        self.submodules.regs = ClockDomainsRenamer('net')(Registers(dsp, p))


def access(r, addr, value=None, error=False):
    yield r.address.eq(addr); yield r.write.eq(value is not None)
    yield r.wdata.eq(value or 0); yield r.strobe.eq(1)
    for _ in range(20):
        yield
        if (yield r.ack):break
    else:raise AssertionError('No bus acknowledgement')
    assert bool((yield r.err)) == error
    result = (yield r.rdata)
    yield r.strobe.eq(0)
    for _ in range(3):yield
    return result


def test_memory_ownership_abort_and_bypass():
    d = DUT(); r = d.regs
    def test():
        assert (yield from access(r, 1)) == 0x10002
        assert (yield from access(r, 8)) == 3
        for address in [0x400, 0x7fc]:
            for offset, value in enumerate([1000000, 0x12345678, 0x87654321, 0]):
                yield from access(r, address+offset, value)
                assert (yield from access(r, address+offset)) == value
        yield from access(r, 0x403, 1, True)
        yield from access(r, 0x23, 0, True)
        yield from access(r, 0x23, 257, True)
        yield from access(r, 0x24, 0, True)
        yield from access(r, 0x25, 4, True)
        yield from access(r, 0x24, 0xffffffff)
        assert (yield from access(r, 0x24)) == 0xffffffff
        yield from access(r, 0x25, 1)
        assert (yield from access(r, 0x20)) == 1
        for addr, value in [(0x400, 4), (0x23, 2), (0x24, 2), (0x25, 1), (0x14, 1)]:
            yield from access(r, addr, value, True)
        yield from access(r, 0x26, 1)
        for _ in range(100):
            if not (yield from access(r, 0x20)):break
        else:raise AssertionError('Abort did not drain')
        assert (yield from access(r, 0x21)) == 0x11
        assert (yield from access(r, 0x22)) == 1
        yield from access(r, 0x25, 2)
        for _ in range(100):
            if not (yield from access(r, 0x20)):break
        assert (yield from access(r, 0x21)) == 0
        assert (yield from access(r, 0x22)) == 2
        assert (yield from access(r, 0x400)) == 1000000
    run_simulation(d, {'net': test()}, clocks={'net': 10, 'jesd': 6})


def test_pending_request_locks_ram_before_destination_clock():
    d = DUT(); r = d.regs
    def test():
        yield from access(r, 0x25, 1)
        assert (yield from access(r, 0x20)) == 1
        yield from access(r, 0x400, 1, True)
        yield from access(r, 0x25, 1, True)
        assert (yield from access(r, 0x22)) == 0
    run_simulation(d, {'net': test()}, clocks={'net': 10, 'jesd': 10000})


def test_host_encoder_boundaries():
    import pytest
    from envelope_client import encode_program, pack_gain
    assert pack_gain(1) == 32767
    assert pack_gain(1j) == 32767<<16
    assert pack_gain(-1) == 32768
    assert encode_program([(1, .5, -.5j)]) == [1, 0x4000, 0xc0000000, 0]
    for entries in [[], [(0, 0, 0)], [(1.5, 0, 0)], [(True, 0, 0)], [(1, 1+1j, 0)], [(1, float('nan'), 0)], [(1, 0, 0)]*257]:
        with pytest.raises(ValueError):encode_program(entries)
