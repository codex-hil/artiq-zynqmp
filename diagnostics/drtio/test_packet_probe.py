"""Time-slotted single-GTH packet probe simulation; LGPL-3.0-or-later."""
import unittest
from migen import Module, ClockDomain, Signal, Cat
from migen.sim import run_simulation
from packet_probe import PacketProbe

class Wire(Module):
    def __init__(self,offset=0):
        self.clock_domains.cd_gth_tx = ClockDomain('gth_tx')
        self.clock_domains.cd_gth_rx = ClockDomain('gth_rx')
        self.submodules.probe = PacketProbe(phase_bits=8, counter_width=8)
        old = Signal(20)
        self.sync.gth_tx += old.eq(self.probe.tx_raw)
        stream = Cat(old,self.probe.tx_raw)
        self.comb += self.probe.rx_raw.eq(stream[offset:offset+20])

class ProbeTest(unittest.TestCase):
    def exercise(self,cases,offset=0):
        d=Wire(offset)
        p=d.probe
        names=list(p.counts)
        def counts():
            result={}
            for name in names:result[name]=(yield getattr(p,name).status)
            return result
        def run():
            for _ in range(300):yield
            self.assertEqual((yield p.alignment.status)&1,1)
            for cmd,drop,expected in cases:
                yield p.enable.storage.eq(0)
                for _ in range(280):yield
                yield p.command.storage.eq(cmd)
                yield p.drop_reply.storage.eq(drop)
                for _ in range(20):yield
                before=yield from counts()
                yield p.enable.storage.eq(1)
                for _ in range(540):yield
                yield p.enable.storage.eq(0)
                for _ in range(280):yield
                after=yield from counts()
                delta={k:after[k]-before[k] for k in names}
                self.assertGreaterEqual(delta['requests'],2,(cmd,delta))
                for key in expected:self.assertGreaterEqual(delta[key],2,(cmd,delta))
                if cmd < 7:
                    self.assertEqual(delta['sat_errors'],0,(cmd,delta))
                    self.assertEqual(delta['master_errors'],0,(cmd,delta))
                self.assertEqual(delta['fifo_errors'],0,(cmd,delta))
                if drop:self.assertEqual(delta['echo_replies'],0,(cmd,delta))
        run_simulation(d,run(),clocks={'sys':8,'gth_tx':8,'gth_rx':(8,2)})
    def test_echo_time_write_buffer(self):
        self.exercise([(0,0,['echo_replies']),(1,0,['time_loads']),
                       (2,0,['writes']),(3,0,['buffer_replies'])])
    def test_read_replies(self):
        self.exercise([(4,0,['read_replies']),(5,0,['read_replies']),
                       (6,0,['read_replies'])],7)
    def test_negative_controls(self):
        self.exercise([(0,1,['timeouts']),(8,0,['sat_errors','unknown_errors']),
                       (9,0,['sat_errors','truncated_errors']),(0,0,['echo_replies'])],3)
