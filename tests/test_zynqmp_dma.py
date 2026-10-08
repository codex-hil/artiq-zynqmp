"""RTL simulation only. Adapted M-Labs artiq-zynq test_dma.py (LGPL-3.0).
Uses the same pinned revision as DMA_ORIGIN.json; LiteX AXI memory driver
adds real ready/valid handshakes and FIFO same-ID response order.
"""
import unittest
import random
import itertools

from migen import *
from litex.soc.interconnect.axi import AXIInterface
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"boards/genesys_zu-5ev/1_gateware"))

from artiq.coredevice.exceptions import RTIOUnderflow, RTIODestinationUnreachable
from artiq.gateware import rtio
from artiq.gateware.rtio import cri
from artiq.gateware.rtio.phy import ttl_simple

import zynqmp_dma as dma

def reverse_word(value, size):
    return int.from_bytes(value.to_bytes(size//8,"big"),"little")


class AXIMemorySim:
    def __init__(self, bus, data, max_queue=12):
        self.bus = bus
        self.data = data
        self.max_queue = max_queue
        self.align = len(bus.r.data)//8
        self.queue = []
        self.response = 0

    @passive
    def ar(self):
        bus=self.bus.ar
        while True:
            ready=len(self.queue)<self.max_queue
            yield bus.ready.eq(ready)
            yield
            if ready and (yield bus.valid):
                self.queue.append(((yield bus.addr),(yield bus.len),(yield bus.id)))

    @passive
    def r(self):
        bus=self.bus.r
        while True:
            if self.queue:
                addr,length,ident=self.queue.pop(0)
                for i in range(length+1):
                    if addr % self.align:raise ValueError('unaligned AXI burst')
                    index=addr//self.align+i
                    value=self.data[index] if index<len(self.data) else 0
                    # Actual little-endian DDR lanes for the recorded byte stream.
                    yield bus.data.eq(reverse_word(value,len(bus.data)))
                    yield bus.id.eq(ident)
                    yield bus.last.eq(i==length)
                    yield bus.resp.eq(self.response)
                    yield bus.valid.eq(1)
                    yield
                    while not (yield bus.ready):yield
                    yield bus.valid.eq(0)
                    yield
            else:yield


def encode_n(n, min_length, max_length):
    r = []
    while n:
        r.append(n & 0xff)
        n >>= 8
    r += [0]*(min_length - len(r))
    if len(r) > max_length:
        raise ValueError
    return r


def encode_record(channel, timestamp, address, data):
    r = []
    r += encode_n(channel, 3, 3)
    r += encode_n(timestamp, 8, 8)
    r += encode_n(address, 1, 1)
    r += encode_n(data, 1, 64)
    return encode_n(len(r)+1, 1, 1) + r


def pack(x, size):
    r = []
    for i in range((len(x)+size-1)//size):
        n = 0
        for j in range(i*size, (i+1)*size):
            n <<= 8
            try:
                n |= x[j]
            except IndexError:
                pass
        r.append(n)
    return r


def encode_sequence(writes, ws):
    sequence = [b for write in writes for b in encode_record(*write)]
    sequence.append(0)
    return pack(sequence, ws)


def do_dma(dut, address):
    yield from dut.dma.base_address.write(address)
    yield from dut.enable.write(1)
    yield
    while ((yield from dut.enable.read())):
        yield
    error = yield from dut.cri_master.error.read()
    if error & 1:
        raise RTIOUnderflow
    if error & 2:
        raise RTIODestinationUnreachable


test_writes1 = [
    (0x01, 0x23, 0x12, 0x33),
    (0x901, 0x902, 0x11, 0xeeeeeeeeeeeeeefffffffffffffffffffffffffffffff28888177772736646717738388488),
    (0x81, 0x288, 0x88, 0x8888)
]


test_writes2 = [
    (0x10, 0x10000, 0x20, 0x77),
    (0x11, 0x10001, 0x22, 0x7777),
    (0x12, 0x10002, 0x30, 0x777777),
    (0x13, 0x10003, 0x40, 0x77777788),
    (0x14, 0x10004, 0x50, 0x7777778899),
]


prng = random.Random(0)


class TB(Module):
    def __init__(self, ws):
        sequence1 = encode_sequence(test_writes1, ws)
        sequence2 = encode_sequence(test_writes2, ws)
        offset = 512//ws
        assert len(sequence1) < offset
        sequence = (
            sequence1 +
            [prng.randrange(2**(ws*8)) for _ in range(offset-len(sequence1))] +
            sequence2)

        bus = AXIInterface(data_width=ws*8, address_width=49, id_width=6)
        self.memory = AXIMemorySim(bus, sequence)
        self.submodules.dut = dma.DMA(bus)


test_writes_full_stack = [
    (0, 512, 0, 1),
    (1, 520, 0, 1),
    (0, 528, 0, 0),
    (1, 530, 0, 0),
]


class FullStackTB(Module):
    def __init__(self, ws):
        self.ttl0 = Signal()
        self.ttl1 = Signal()

        self.submodules.phy0 = ttl_simple.Output(self.ttl0)
        self.submodules.phy1 = ttl_simple.Output(self.ttl1)

        rtio_channels = [
            rtio.Channel.from_phy(self.phy0),
            rtio.Channel.from_phy(self.phy1)
        ]

        sequence = encode_sequence(test_writes_full_stack, ws)

        bus = AXIInterface(data_width=ws*8, address_width=49, id_width=6)
        self.memory = AXIMemorySim(bus, sequence)
        self.submodules.dut = dma.DMA(bus)
        self.submodules.tsc = rtio.TSC()
        self.submodules.rtio = rtio.Core(self.tsc, rtio_channels)
        self.comb += self.dut.cri.connect(self.rtio.cri)


class TestDMA(unittest.TestCase):
    def test_axi_error_latched_and_cleared_on_next_playback(self):
        tb = TB(8)
        tb.memory.response = 2  # SLVERR, actual accepted R beat
        def stimulus():
            yield from do_dma(tb.dut, 0)
            self.assertEqual((yield tb.dut.dma.wb_reader.bus_error.status), 1)
            tb.memory.response = 0
            yield from do_dma(tb.dut, 512)
            self.assertEqual((yield tb.dut.dma.wb_reader.bus_error.status), 0)
        run_simulation(tb, [stimulus(), tb.memory.ar(), tb.memory.r()])

    def test_dma_noerror(self):
        tb = TB(8)

        def do_writes():
            yield from do_dma(tb.dut, 0)
            yield from do_dma(tb.dut, 512)

        received = []
        @passive
        def rtio_sim():
            dut_cri = tb.dut.cri
            while True:
                cmd = yield dut_cri.cmd
                if cmd == cri.commands["nop"]:
                    pass
                elif cmd == cri.commands["write"]:
                    channel = yield dut_cri.chan_sel
                    timestamp = yield dut_cri.o_timestamp
                    address = yield dut_cri.o_address
                    data = yield dut_cri.o_data
                    received.append((channel, timestamp, address, data))

                    yield dut_cri.o_status.eq(1)
                    for i in range(prng.randrange(10)):
                        yield
                    yield dut_cri.o_status.eq(0)
                else:
                    self.fail("unexpected RTIO command")
                yield

        run_simulation(tb, [do_writes(), rtio_sim(), tb.memory.ar(), tb.memory.r()])
        self.assertEqual(received, test_writes1 + test_writes2)

    def test_full_stack(self):
        tb = FullStackTB(8)

        ttl_changes = []
        @passive
        def monitor():
            old_ttl_states = [0, 0]
            for time in itertools.count():
                ttl_states = [
                    (yield tb.ttl0),
                    (yield tb.ttl1)
                ]
                for i, (old, new) in enumerate(zip(old_ttl_states, ttl_states)):
                    if new != old:
                        ttl_changes.append((time, i))
                old_ttl_states = ttl_states
                yield

        run_simulation(tb, {"sys": [
            do_dma(tb.dut, 0), monitor(),
            (None for _ in range(600)),
            tb.memory.ar(), tb.memory.r()
        ]}, {"sys": 8, "rsys": 8, "rio": 8, "rio_phy": 8})

        correct_changes = [(timestamp + 11, channel)
                           for channel, timestamp, _, _ in test_writes_full_stack]
        self.assertEqual(ttl_changes, correct_changes)
