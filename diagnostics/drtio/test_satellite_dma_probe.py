"""Decode the exact host DDR image using native ARTIQ; LGPL-3.0-or-later."""
import unittest
from migen import passive
from migen.sim import run_simulation
from artiq.gateware.rtio.dma import RecordSlicer
from satellite_dma_probe import trace_bytes,make_tcl

class ProbeTests(unittest.TestCase):
    def test_exact_ddr_bytes_decode_with_native_record_slicer(self):
        d=RecordSlicer(64);data=trace_bytes();records=[];terminated=[]
        @passive
        def monitor():
            while True:
                if (yield d.source.stb) and (yield d.source.ack):
                    records.append(((yield d.source.channel),(yield d.source.timestamp),
                                    (yield d.source.address),(yield d.source.data)))
                if (yield d.end_marker_found):terminated.append(1)
                yield
        def run():
            yield d.source.ack.eq(1)
            # DMAReader reverses little-endian DDR words before RecordSlicer.
            for offset in range(0,256,8):
                yield d.sink.data.eq(int.from_bytes(data[offset:offset+8],'big'))
                yield d.sink.stb.eq(1);yield
                for _ in range(100):
                    if (yield d.sink.ack) or terminated:break
                    yield
                else:self.fail('Native decoder stalled')
                yield d.sink.stb.eq(0);yield
                if terminated:break
            for _ in range(30):yield
        run_simulation(d,[run(),monitor()])
        expected=[(1,0,2,3)]
        for i in range(4):
            t=1000000+i*80000
            expected.extend([(0,t,0,1),(0,t+8000,0,0)])
        expected.append((1,2000000,2,0))
        self.assertEqual(records,expected)
        self.assertTrue(terminated)
        self.assertEqual(len(data),2048)
        self.assertFalse(any(data[171:]))

    def test_invalid_epoch_or_arena_rejected_before_hardware(self):
        for ts in (0,-8,9,2**63):
            with self.assertRaises(ValueError):make_tcl({},ts)
        with self.assertRaisesRegex(ValueError,'arena'):make_tcl({},8000)

if __name__=='__main__':unittest.main()
