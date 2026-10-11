"""Upstream DRTIO master/satellite packets across encoded raw20 wires.

LGPL-3.0-or-later test glue. No physical or latency qualification implied.
"""
import unittest
from unittest.mock import patch
from migen import Module, ClockDomainsRenamer
from migen.sim import run_simulation
from artiq.gateware.test.drtio import test_full_stack as upstream
from raw20_codec import Raw20Codec
from protocol_probe import WordAligner


class EncodedPair(Module):
    def __init__(self, nwords):
        if nwords != 2: raise ValueError('Raw20 requires two symbols')
        self.submodules.a = Raw20Codec()
        self.submodules.b = Raw20Codec()
        self.submodules.align_a = ClockDomainsRenamer('rtio_rx')(WordAligner())
        self.submodules.align_b = ClockDomainsRenamer('rtio_rx')(WordAligner())
        self.alice, self.bob = self.a.channel, self.b.channel
        self.comb += [self.align_a.input.eq(self.b.tx_raw),
                     self.align_b.input.eq(self.a.tx_raw),
                     self.a.rx_raw.eq(self.align_a.output),
                     self.b.rx_raw.eq(self.align_b.output)]
        for codec, aligner in ((self.a,self.align_a),(self.b,self.align_b)):
            self.comb += [codec.rx_reset_done.eq(1), codec.rx_clock_active.eq(1),
                          codec.word_aligned.eq(aligner.aligned)]


class PacketTest(unittest.TestCase):
    def test_echo_and_scheduled_ttl(self):
        # Keep the upstream master, satellite, SED, TTL and kernel initiator.
        with patch.object(upstream, 'DummyTransceiverPair', EncodedPair):
            tb = upstream.OutputsTestbench()
        dut = tb.dut
        dut.submodules.encoded_pair = dut.transceivers
        changes = []
        done = [False]

        def test():
            yield from tb.init()
            packet = dut.master.rt_packet
            baseline = (yield packet.packet_cnt_rx)
            yield packet.echo_stb.eq(1)
            yield
            for _ in range(500):
                if (yield packet.echo_ack): break
                yield
            else: self.fail('Echo TX timeout')
            yield packet.echo_stb.eq(0)
            for _ in range(500):
                if (yield packet.packet_cnt_rx) > baseline: break
                yield
            else: self.fail('Echo response timeout')
            tb.now = (yield dut.tsc_master.full_ts_cri) + 300
            yield from tb.write(0, 1)
            tb.delay(20)
            yield from tb.write(0, 0)
            tb.delay(30)
            yield from tb.write(1, 1)
            tb.delay(20)
            yield from tb.write(1, 0)
            yield from tb.sync()
            done[0] = True

        def watchdog():
            for _ in range(3000):
                if done[0]: return
                yield
            self.fail('Master/satellite simulation timeout')

        run_simulation(dut, {'sys':[test(), watchdog(), tb.check_ttls(changes)]},
                       upstream.TestFullStack.clocks)
        self.assertEqual([channel for _,channel in changes], [0,0,1,1])
        self.assertEqual([changes[i+1][0]-changes[i][0] for i in range(3)],
                         [20,30,20])
