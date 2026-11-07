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

if __name__ == '__main__':
    unittest.main()
