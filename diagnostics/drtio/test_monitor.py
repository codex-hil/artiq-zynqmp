import unittest
from migen import Module, ClockDomain, Signal
from migen.sim import run_simulation
from monitor import GrayCounter, Monitor


class MonitorTests(unittest.TestCase):
    def test_counter_wrap_and_stopped_source(self):
        dut = Module()
        dut.clock_domains.cd_sys = ClockDomain('sys')
        dut.clock_domains.cd_gth_rx = ClockDomain('gth_rx')
        dut.submodules.counter = GrayCounter('gth_rx', width=4)
        enable = Signal()
        dut.comb += dut.counter.enable.eq(enable)
        completed = False
        def source():
            nonlocal completed
            yield enable.eq(0)
            for _ in range(3): yield
            yield enable.eq(1)
            for _ in range(37): yield
            yield enable.eq(0)
            for _ in range(3): yield
            completed = True
            for _ in range(20): yield
        def reader():
            while not completed: yield
            for _ in range(10): yield
            self.assertEqual((yield dut.counter.value), 37 % 16)
            for _ in range(5):
                yield
                self.assertEqual((yield dut.counter.value), 37 % 16)
        run_simulation(dut, {'sys': reader(), 'gth_rx': source()}, clocks={'sys':13, 'gth_rx':8})

    def test_event_counter_only_counts_enabled_cycles(self):
        dut = Module()
        dut.clock_domains.cd_sys = ClockDomain('sys')
        dut.clock_domains.cd_gth_rx = ClockDomain('gth_rx')
        dut.submodules.counter = GrayCounter('gth_rx', width=8)
        enable = Signal()
        dut.comb += dut.counter.enable.eq(enable)
        completed = False
        def source():
            nonlocal completed
            yield enable.eq(0)
            yield
            for _ in range(10):
                yield enable.eq(1)
                yield
                yield enable.eq(0)
                for _ in range(4): yield
            completed = True
            for _ in range(30): yield
        def reader():
            while not completed: yield
            for _ in range(10): yield
            self.assertEqual((yield dut.counter.value), 10)
        run_simulation(dut, {'sys': reader(), 'gth_rx': source()}, clocks={'sys':10,'gth_rx':14})

    def test_snapshot_is_held_until_next_request(self):
        dut = Module()
        for name in ('sys', 'gth_rx', 'gth_tx'):
            setattr(dut.clock_domains, 'cd_'+name, ClockDomain(name))
        status, error = Signal(10), Signal()
        dut.submodules.monitor = Monitor(status, error)
        m = dut.monitor
        def test():
            self.assertEqual((yield m.magic.status), 0x44525430)
            self.assertEqual((yield m.reset.storage), 1)
            self.assertEqual((yield m.tx_enable.storage), 0)
            yield status.eq(0x7f)
            for _ in range(15): yield
            yield m.snapshot.re.eq(1)
            yield
            yield m.snapshot.re.eq(0)
            yield
            self.assertEqual((yield m.status.status), 0x7f)
            first = (yield m.boot_ticks.status)
            rx_first = (yield m.rx_ticks.status)
            tx_first = (yield m.tx_ticks.status)
            for _ in range(20): yield
            self.assertEqual((yield m.boot_ticks.status), first)
            yield m.snapshot.re.eq(1)
            yield
            yield m.snapshot.re.eq(0)
            yield
            self.assertGreater((yield m.boot_ticks.status), first)
            self.assertGreater((yield m.rx_ticks.status), rx_first)
            self.assertGreater((yield m.tx_ticks.status), tx_first)
            self.assertEqual((yield m.prbs_errors.status), 0)
        run_simulation(dut, test(), clocks={'sys':8,'gth_rx':10,'gth_tx':12})


if __name__ == '__main__': unittest.main()
