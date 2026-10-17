"""Bounded delay, AXI stability and refusal controls; LGPL-3.0-or-later."""
import unittest
from migen.sim import run_simulation
from migen import passive
from litex.soc.interconnect.axi import AXIInterface
from dma_read_delay import DMAReadDelay


class ReadDelayTests(unittest.TestCase):
    def test_bounded_hold_and_retrigger_cannot_extend_it(self):
        u, m = AXIInterface(data_width=64, id_width=4), AXIInterface(data_width=64, id_width=4)
        d = DMAReadDelay(u, m, 7)
        def run():
            yield d.idle.eq(1); yield d.trigger.eq(1); yield
            yield d.trigger.eq(0); yield
            self.assertEqual((yield d.accepted), 1)
            yield m.r.valid.eq(1); yield m.r.data.eq(0xdeadbeef)
            yield m.r.id.eq(1); yield m.r.last.eq(1); yield m.r.resp.eq(2)
            yield u.r.ready.eq(1); yield d.trigger.eq(1)
            held = 0
            for _ in range(12):
                if (yield d.holding):
                    held += 1
                    self.assertEqual((yield u.r.valid), 0)
                    self.assertEqual((yield m.r.ready), 0)
                else:
                    self.assertEqual((yield u.r.valid), 1)
                    self.assertEqual((yield u.r.data), 0xdeadbeef)
                    self.assertEqual((yield u.r.id), 1)
                    self.assertEqual((yield u.r.last), 1)
                    self.assertEqual((yield u.r.resp), 2)
                    self.assertEqual((yield m.r.ready), 1)
                yield
            self.assertEqual(held, 7)
            self.assertEqual((yield d.rejected), 1)
        run_simulation(d, run())

    def test_exposed_stalled_response_never_withdrawn(self):
        u, m = AXIInterface(data_width=64, id_width=4), AXIInterface(data_width=64, id_width=4)
        d = DMAReadDelay(u, m, 7)
        def run():
            yield m.r.valid.eq(1); yield m.r.data.eq(123)
            yield u.r.ready.eq(0); yield d.idle.eq(1); yield; yield
            yield d.trigger.eq(1)
            for _ in range(12):
                yield
                self.assertEqual((yield u.r.valid), 1)
                self.assertEqual((yield u.r.data), 123)
                self.assertEqual((yield d.holding), 0)
                self.assertEqual((yield m.r.ready), 0)
            self.assertEqual((yield d.rejected), 1)
        run_simulation(d, run())

    def test_busy_refused(self):
        u, m = AXIInterface(data_width=64, id_width=4), AXIInterface(data_width=64, id_width=4)
        d = DMAReadDelay(u, m, 1)
        def run():
            yield d.trigger.eq(1)
            for _ in range(4):yield
            self.assertEqual((yield d.accepted), 0)
            self.assertEqual((yield d.rejected), 1)
            self.assertEqual((yield d.holding), 0)
        run_simulation(d, run())

    def test_order_and_stability_with_consumer_backpressure(self):
        u, m = AXIInterface(data_width=64, id_width=4), AXIInterface(data_width=64, id_width=4)
        d = DMAReadDelay(u, m, 5)
        expected=[(100+i, i//4, int(i%4==3), i%3) for i in range(12)]
        received=[]
        @passive
        def consumer():
            cycle=0;stalled=None
            while True:
                value=((yield u.r.data),(yield u.r.id),(yield u.r.last),(yield u.r.resp))
                if stalled is not None:
                    self.assertEqual((yield u.r.valid),1)
                    self.assertEqual(value,stalled)
                stalled=value if (yield u.r.valid) and not (yield u.r.ready) else None
                if (yield u.r.valid) and (yield u.r.ready):received.append(value)
                yield u.r.ready.eq(cycle%4==0)
                cycle+=1
                yield
        def producer():
            yield d.idle.eq(1);yield d.trigger.eq(1);yield
            yield d.trigger.eq(0);yield
            for data,ident,last,resp in expected:
                yield m.r.valid.eq(1);yield m.r.data.eq(data)
                yield m.r.id.eq(ident);yield m.r.last.eq(last);yield m.r.resp.eq(resp)
                yield
                for _ in range(100):
                    if (yield m.r.ready):break
                    yield
                else:self.fail('Response did not drain')
            yield m.r.valid.eq(0)
            for _ in range(3):yield
            self.assertEqual(received,expected)
        run_simulation(d,[producer(),consumer()])

    def test_invalid_bound(self):
        for value in (0, -1, 1048577):
            with self.assertRaises(ValueError):
                DMAReadDelay(AXIInterface(), AXIInterface(), value)
