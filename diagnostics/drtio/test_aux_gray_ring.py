# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen import Module, ClockDomain
from migen.sim import run_simulation, passive
from aux_gray_ring_model import AuxGrayRingModel


class RingTests(unittest.TestCase):
    def test_full_reject_drain_and_reuse(self):
        top = Module()
        top.clock_domains.cd_sys = ClockDomain('sys')
        top.clock_domains.cd_rtio_rx = ClockDomain('rtio_rx')
        top.submodules.ring = ring = AuxGrayRingModel()
        state = {'drain': False}
        observed = []
        @passive
        def reader():
            while True:
                if state['drain'] and (yield ring.present):
                    for _ in range(3):
                        yield
                    observed.append((yield ring.read_data))
                    yield ring.consume.eq(1)
                    yield
                    yield ring.consume.eq(0)
                    for _ in range(3):
                        yield
                else:
                    yield
        def writer():
            for batch in range(4):
                state['drain'] = False
                for index in range(7):
                    for _ in range(80):
                        if (yield ring.ready):
                            break
                        yield
                    else:
                        self.fail('Freed slot never became writable')
                    yield ring.write_data.eq(0xabc00000+batch*7+index)
                    yield ring.put.eq(1)
                    yield
                    yield ring.put.eq(0)
                    yield
                for _ in range(6):
                    yield
                self.assertEqual((yield ring.ready), 0)
                # Attempt an eighth write while full: must not alter queued data.
                yield ring.write_data.eq(0xdeadbeef)
                yield ring.put.eq(1)
                for _ in range(5):
                    self.assertEqual((yield ring.ready), 0)
                    yield
                yield ring.put.eq(0)
                state['drain'] = True
                for _ in range(300):
                    if len(observed) == 7*(batch+1) and not (yield ring.present):
                        break
                    yield
                else:
                    self.fail('Ring did not drain')
                for _ in range(10):
                    yield
                self.assertEqual((yield ring.ready), 1)
            self.assertEqual(observed, [0xabc00000+i for i in range(28)])
        run_simulation(top, {'rtio_rx': writer(), 'sys': reader()},
                       clocks={'rtio_rx': 8, 'sys': (22, 3)})

    def test_queued_memory_reset_with_reader_clock_stopped(self):
        self._reset_case(('sys',), ('sys',))

    def test_writer_stop_and_restart_matrix(self):
        for stopped, order in [(('rtio_rx',), ('rtio_rx',)),
                               (('sys', 'rtio_rx'), ('sys', 'rtio_rx')),
                               (('sys', 'rtio_rx'), ('rtio_rx', 'sys'))]:
            with self.subTest(stopped=stopped, restart=order):
                self._reset_case(stopped, order)

    def _reset_case(self, stopped, restart_order):
        from migen.sim import Simulator
        top = Module()
        top.clock_domains.cd_sys = ClockDomain('sys')
        top.clock_domains.cd_rtio_rx = ClockDomain('rtio_rx')
        top.submodules.ring = ring = AuxGrayRingModel()
        top.clock_domains.cd_control = ClockDomain('control')
        state = {'stopped': set(), 'suppressed': {cd: 0 for cd in stopped}}
        def test():
            for value in (0x11111111, 0x22222222):
                yield ring.write_data.eq(value)
                yield ring.put.eq(1)
                yield
                yield ring.put.eq(0)
                yield
            for _ in range(20):
                yield
            self.assertEqual((yield ring.present), 1)
            state['stopped'] = set(stopped)
            for _ in range(20):
                yield
            for cd in stopped:
                self.assertGreater(state['suppressed'][cd], 0)
            # Admission disabled and both pointer owners reset. Memory is retained.
            yield ring.put.eq(0)
            yield ring.consume.eq(0)
            yield top.cd_sys.rst.eq(1)
            yield top.cd_rtio_rx.rst.eq(1)
            for _ in range(12):
                yield
            for cd in restart_order:
                state['stopped'].remove(cd)
                for _ in range(16):
                    yield
            # Reset is held until both domains have resumed; no early release.
            for _ in range(20):
                yield
            yield top.cd_sys.rst.eq(0)
            yield top.cd_rtio_rx.rst.eq(0)
            for _ in range(20):
                self.assertEqual((yield ring.present), 0)
                yield
            self.assertEqual((yield ring.ready), 1)
            # Retained contents are not a published packet, and are not erased.
            self.assertEqual((yield ring.read_data), 0x11111111)
            yield ring.write_data.eq(0xabcdef12)
            yield ring.put.eq(1)
            yield
            yield ring.put.eq(0)
            for _ in range(30):
                yield
            self.assertEqual((yield ring.present), 1)
            self.assertEqual((yield ring.read_data), 0xabcdef12)
            yield ring.consume.eq(1)
            for _ in range(3):
                yield
            yield ring.consume.eq(0)
            for _ in range(20):
                yield
            self.assertEqual((yield ring.present), 0)
            self.assertEqual((yield ring.reader.binary), 1)
            self.assertEqual((yield ring.writer.binary), 1)
        # Stock MemoryToArray makes storage resettable. Model retained SRAM
        # explicitly; do not mistake simulator zeroing for hardware erasure.
        from migen.fhdl.simplify import MemoryToArray
        fragment = top.get_fragment()
        memory_model = MemoryToArray()
        memory_model.transform_fragment(None, fragment)
        for word in memory_model.replacements[ring.memory]:
            word.reset_less = True
        with Simulator(fragment, {'control': test()},
                       clocks={'control': 8, 'rtio_rx': 8, 'sys': (22, 3)}) as sim:
            original_tick = sim.time.tick
            def tick():
                dt, rising, falling = original_tick()
                for cd in state['stopped']:
                    state['suppressed'][cd] += int(cd in rising)
                    rising.discard(cd)
                    falling.discard(cd)
                return dt, rising, falling
            sim.time.tick = tick
            sim.run()


if __name__ == '__main__':
    unittest.main()
