# SPDX-License-Identifier: LGPL-3.0-or-later
"""Behavioral pointer checks, not physical CDC or SRAM qualification."""
import unittest
from migen import Module, ClockDomain
from migen.sim import run_simulation, passive
from aux_gray_pointer import AuxGrayPointer


class GrayPointerTests(unittest.TestCase):
    def test_wrap_settle_and_coordinated_reset(self):
        top = Module()
        top.clock_domains.cd_sys = ClockDomain('sys')
        top.clock_domains.cd_rtio_rx = ClockDomain('rtio_rx')
        top.submodules.pointer = p = AuxGrayPointer()
        def test():
            previous = 0
            for count in range(1, 25):
                yield p.advance.eq(1)
                yield
                yield p.advance.eq(0)
                # Let every destination synchronizer stage settle before compare.
                for _ in range(12):
                    yield
                expected = count % 8
                actual = (yield p.gray)
                self.assertEqual((actual ^ previous).bit_count(), 1)
                self.assertEqual(actual, expected ^ (expected >> 1))
                self.assertEqual((yield p.binary), expected)
                self.assertEqual((yield p.remote), expected)
                previous = actual
            # Nonzero state before reset, so clearing is observable.
            yield p.advance.eq(1)
            yield
            yield p.advance.eq(0)
            for _ in range(12):
                yield
            self.assertEqual((yield p.remote), 1)
            yield top.cd_sys.rst.eq(1)
            yield top.cd_rtio_rx.rst.eq(1)
            for _ in range(12):
                yield
            yield top.cd_sys.rst.eq(0)
            yield top.cd_rtio_rx.rst.eq(0)
            for _ in range(12):
                yield
            self.assertEqual((yield p.binary), 0)
            self.assertEqual((yield p.gray), 0)
            self.assertEqual((yield p.remote), 0)
        run_simulation(top, {'rtio_rx': test()}, clocks={'sys': 8, 'rtio_rx': 14})

    def test_fast_producer_skipped_samples(self):
        top = Module()
        top.clock_domains.cd_sys = ClockDomain('sys')
        top.clock_domains.cd_rtio_rx = ClockDomain('rtio_rx')
        top.submodules.pointer = p = AuxGrayPointer(width=8)
        samples = []
        @passive
        def observer():
            while True:
                samples.append((yield p.remote))
                yield
        def producer():
            yield p.advance.eq(1)
            for _ in range(100):
                yield
            yield p.advance.eq(0)
            for _ in range(40):
                yield
            self.assertEqual((yield p.binary), 100)
            self.assertEqual((yield p.remote), 100)
        run_simulation(top, {'rtio_rx': producer(), 'sys': observer()},
                       clocks={'rtio_rx': 8, 'sys': (22, 3)})
        self.assertTrue(all(a <= b for a, b in zip(samples, samples[1:])))
        self.assertTrue(any(b-a > 1 for a, b in zip(samples, samples[1:])))
        self.assertTrue(all(0 <= x <= 100 for x in samples))

    def test_unbounded_lap_alias_is_not_full_detection(self):
        top = Module()
        top.clock_domains.cd_sys = ClockDomain('sys')
        top.clock_domains.cd_rtio_rx = ClockDomain('rtio_rx')
        top.submodules.pointer = p = AuxGrayPointer()
        def producer():
            self.assertEqual((yield p.remote), 0)
            yield p.advance.eq(1)
            for _ in range(8):
                yield
            yield p.advance.eq(0)
            for _ in range(30):
                yield
            # Eight unconsumed advances alias empty. Caller MUST bound producer
            # occupancy; the pointer module deliberately supplies no queue policy.
            self.assertEqual((yield p.binary), 0)
            self.assertEqual((yield p.remote), 0)
        run_simulation(top, {'rtio_rx': producer()},
                       clocks={'rtio_rx': 8, 'sys': 22})

    def test_invalid_contract_refused(self):
        for width in (0, 1, -1, True, 3.5):
            with self.subTest(width=width), self.assertRaises(ValueError):
                AuxGrayPointer(width)
        with self.assertRaises(ValueError):
            AuxGrayPointer(source='sys', destination='sys')

if __name__ == '__main__':
    unittest.main()
