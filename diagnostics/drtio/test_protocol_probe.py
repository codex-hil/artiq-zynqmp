import unittest
from migen import Module, ClockDomain, Signal, Cat
from migen.sim import run_simulation
from protocol_probe import ProtocolProbe, WordAligner, COMMAS

class Wire(Module):
    def __init__(self, offset=0):
        self.clock_domains.cd_gth_tx=ClockDomain('gth_tx')
        self.clock_domains.cd_gth_rx=ClockDomain('gth_rx')
        self.submodules.probe=ProtocolProbe(phase_bits=8)
        previous=Signal(20)
        self.sync.gth_tx += previous.eq(self.probe.tx_raw)
        stream=Cat(previous,self.probe.tx_raw)
        self.comb += self.probe.rx_raw.eq(stream[offset:offset+20])

class ProbeTest(unittest.TestCase):
    def exercise(self,offset,inject=False):
        d=Wire(offset)
        def run():
            # Decoder/descrambler acquisition can produce initial false frames.
            # Validate new errors only after idle alignment has settled.
            for _ in range(200): yield
            baseline={}
            for kind in ('rt','aux'):
                baseline[kind]=(yield getattr(d.probe,kind+'_errors').status)
            yield d.probe.enable.storage.eq(1)
            for _ in range(700): yield
            self.assertEqual((yield d.probe.alignment.status)&1,1)
            for kind in ('rt','aux'):
                self.assertGreater((yield getattr(d.probe,kind+'_frames').status),1)
                self.assertEqual((yield getattr(d.probe,kind+'_errors').status),baseline[kind])
            if inject:
                before=(yield d.probe.rt_errors.status)
                yield d.probe.inject.storage.eq(1)
                for _ in range(300): yield
                self.assertGreater((yield d.probe.rt_errors.status),before)
                yield d.probe.inject.storage.eq(0)
                for _ in range(150): yield
                recovered=(yield d.probe.rt_errors.status)
                for _ in range(300): yield
                self.assertEqual((yield d.probe.rt_errors.status),recovered)
        run_simulation(d,run(),clocks={'sys':8,'gth_tx':8,'gth_rx':(8,2)})
    def test_all_serial_offsets(self):
        for offset in range(20):
            with self.subTest(offset=offset):
                d=WordAligner()
                word=COMMAS[0]
                shifted=((word >> offset) | (word << (20-offset))) & ((1 << 20)-1)
                def acquire():
                    yield d.input.eq(shifted)
                    for _ in range(12): yield
                    self.assertEqual((yield d.aligned),1)
                    self.assertEqual((yield d.offset),(-offset)%20)
                    self.assertEqual((yield d.output),word)
                run_simulation(d,acquire())
    def test_framed_payloads(self): self.exercise(0)
    def test_encoded_bit_corruption(self): self.exercise(7,True)
