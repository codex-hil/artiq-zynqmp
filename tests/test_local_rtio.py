"""Simulated AXI -> MiSoC CSR -> real upstream RTIO, not hardware evidence."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from migen import Signal
from migen.sim import run_simulation

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "boards/genesys_zu-5ev/1_gateware"))
from local_rtio import LocalRTIO


class AXIMaster:
    def __init__(self, axi):
        self.axi = axi

    def handshake(self, channel):
        yield channel.valid.eq(1)
        yield
        for _ in range(100):
            if (yield channel.ready):
                yield
                yield channel.valid.eq(0)
                return
            yield
        raise AssertionError("AXI handshake timed out")

    def write(self, address, value):
        a = self.axi
        yield a.aw.addr.eq(address)
        yield a.aw.size.eq(2)
        yield a.aw.burst.eq(1)
        yield a.aw.len.eq(0)
        yield a.aw.id.eq(0x1234)
        yield from self.handshake(a.aw)
        yield a.w.data.eq(value)
        yield a.w.strb.eq(0xF)
        yield a.w.last.eq(1)
        yield from self.handshake(a.w)
        # Delay BREADY to exercise response retention under backpressure.
        for _ in range(3):
            yield
        for _ in range(100):
            if (yield a.b.valid):
                assert (yield a.b.resp) == 0
                assert (yield a.b.id) == 0x1234
                yield a.b.ready.eq(1)
                yield
                yield a.b.ready.eq(0)
                return
            yield
        raise AssertionError("AXI write response timed out")

    def read(self, address):
        a = self.axi
        yield a.ar.addr.eq(address)
        yield a.ar.size.eq(2)
        yield a.ar.burst.eq(1)
        yield a.ar.len.eq(0)
        yield a.ar.id.eq(0x4321)
        yield from self.handshake(a.ar)
        for _ in range(3):
            yield
        for _ in range(100):
            if (yield a.r.valid):
                assert (yield a.r.resp) == 0
                assert (yield a.r.id) == 0x4321
                assert (yield a.r.last) == 1
                value = yield a.r.data
                yield a.r.ready.eq(1)
                yield
                yield a.r.ready.eq(0)
                return value
            yield
        raise AssertionError("AXI read response timed out")


class LocalRTIOTest(unittest.TestCase):
    def test_axi_csr_counter_and_scheduled_ttl(self):
        out = Signal()
        inp = Signal()
        dut = LocalRTIO(out, inp)
        dut.comb += inp.eq(out)  # simulation-only equivalent of JB1 -> JB2 jumper
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "map.json"
            dut.write_map(path)
            registers = json.loads(path.read_text())["registers"]
        master = AXIMaster(dut.axi)
        addr = lambda key: registers[key]["address"]

        def stimulus():
            for _ in range(12):
                yield
            yield from master.write(addr("rtio_counter_update"), 1)
            hi = yield from master.read(addr("rtio_counter"))
            lo = yield from master.read(addr("rtio_counter") + 4)
            self.assertEqual(hi, 0)
            self.assertGreater(lo, 0)
            # Large lead time keeps AXI transfer latency outside RTIO deadlines.
            timestamp = (yield dut.rtio_tsc.full_ts) + 400
            # Schedule an input rising-edge gate before the output pulse.
            yield from master.write(addr("rtio_target"), (1 << 8) | 2)
            yield from master.write(addr("rtio_now"), 0)
            yield from master.write(addr("rtio_now") + 4, timestamp - 50)
            yield from master.write(addr("rtio_o_data") + 15 * 4, 1)
            yield from master.write(addr("rtio_target"), 0)
            yield from master.write(addr("rtio_now"), 0)
            yield from master.write(addr("rtio_now") + 4, timestamp)
            # Last word of the 512-bit o_data register commits the event.
            yield from master.write(addr("rtio_o_data") + 15 * 4, 1)
            status = yield from master.read(addr("rtio_o_status"))
            self.assertEqual(status, 0)
            yield from master.write(addr("rtio_now") + 4, timestamp + 50)
            yield from master.write(addr("rtio_o_data") + 15 * 4, 0)
            self.assertEqual((yield out), 0)
            for _ in range(500):
                yield
                if (yield out):
                    break
            else:
                self.fail("Scheduled TTL event was not executed")
            self.assertGreaterEqual((yield dut.rtio_tsc.full_ts), timestamp)
            rise = yield dut.rtio_tsc.full_ts
            # The upstream output network has a fixed pipeline latency.
            self.assertLessEqual(rise, timestamp + 32)
            for _ in range(100):
                yield
                if not (yield out):
                    break
            else:
                self.fail("Scheduled TTL falling edge was not executed")
            fall = yield dut.rtio_tsc.full_ts
            self.assertEqual(fall - rise, 50)
            yield from master.write(addr("rtio_target"), 1 << 8)
            yield from master.write(addr("rtio_i_timeout"), 0)
            yield from master.write(addr("rtio_i_timeout") + 4, timestamp + 1000)
            for _ in range(20):
                yield
            status = yield from master.read(addr("rtio_i_status"))
            self.assertEqual(status, 0)
            data = yield from master.read(addr("rtio_i_data"))
            self.assertEqual(data, 1)
            high = yield from master.read(addr("rtio_i_timestamp"))
            low = yield from master.read(addr("rtio_i_timestamp") + 4)
            self.assertEqual(high, 0)
            self.assertGreaterEqual(low, timestamp)
            self.assertLessEqual(low, timestamp + 32)
            errors = yield from master.read(addr("rtio_core_async_error"))
            self.assertEqual(errors, 0)

        run_simulation(dut, stimulus(), clocks={"sys": 10, "rio": 10, "rio_phy": 10})


if __name__ == "__main__":
    unittest.main()
