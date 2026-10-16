"""Coherent request snapshots, asynchronous clocks; LGPL-3.0-or-later."""
import unittest
from migen import Module, ResetInserter
from migen.sim import run_simulation, passive
from tsc_snapshot import TSCSnapshot


class SnapshotTests(unittest.TestCase):
    def test_coherence_and_stability(self):
        d=TSCSnapshot();samples=[]
        @passive
        def source():
            n=0
            while True:
                # Large simultaneous bit changes, including backward TSC loads.
                value=((n*0x123456789abcd) ^ 0xffff0000ffff0000)&((1<<64)-1)
                yield d.sample.eq(value);samples.append(value);n+=1
                yield
        def host():
            for _ in range(8):yield
            self.assertEqual((yield d.valid),0)
            for _ in range(20):
                yield d.request.eq(1);yield;yield d.request.eq(0);yield
                for _ in range(100):
                    if (yield d.valid):break
                    # Duplicate request while busy must not queue extra work.
                    yield d.request.eq((yield d.busy));yield
                else:self.fail('snapshot timeout')
                yield d.request.eq(0)
                v=(yield d.value);self.assertIn(v,samples)
                for _ in range(10):
                    yield
                    self.assertEqual((yield d.value),v)
                    self.assertEqual((yield d.busy),0)
        run_simulation(d,{'sys':host(),'sample':source()},clocks={'sys':10,'sample':13})

    def test_common_reset_discards_old_response(self):
        d=ResetInserter(['sys','sample'])(TSCSnapshot())
        def host():
            yield d.sample.eq(0xdeadbeef12345678)
            yield d.request.eq(1);yield;yield d.request.eq(0)
            for _ in range(2):yield
            yield d.reset_sys.eq(1);yield d.reset_sample.eq(1)
            for _ in range(8):yield
            yield d.reset_sys.eq(0);yield d.reset_sample.eq(0)
            for _ in range(20):yield
            self.assertEqual((yield d.valid),0)
            self.assertEqual((yield d.busy),0)
            yield d.sample.eq(0x1234000056780000)
            yield d.request.eq(1);yield;yield d.request.eq(0)
            for _ in range(100):
                if (yield d.valid):break
                yield
            else:self.fail('post-reset snapshot timeout')
            self.assertEqual((yield d.value),0x1234000056780000)
        run_simulation(d,host(),clocks={'sys':10,'sample':17})


if __name__=='__main__':unittest.main()
