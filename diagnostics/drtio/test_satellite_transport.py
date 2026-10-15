"""Decoded RT request/response CDC and real SED; LGPL-3.0-or-later."""
import unittest
from types import SimpleNamespace
from migen import Module, Signal, ClockDomain, ClockDomainsRenamer
from migen.sim import run_simulation, passive
from artiq.gateware.drtio.rt_packet_master import RTPacketMaster
from satellite_transport import SatelliteTransport, RTReplyCDC


class TransportTests(unittest.TestCase):
    def exercise(self, ready=True, fine_bits=0):
        d = Module()
        for name in ('rtio_rx','gth_tx','master_tx'):
            setattr(d.clock_domains,'cd_'+name,ClockDomain(name))
        pad = Signal()
        endpoint = SimpleNamespace(rx=SimpleNamespace(rt_frame=Signal(),rt_data=Signal(16)),
            tx=SimpleNamespace(rt_frame=Signal(),rt_data=Signal(16)),rx_ready=Signal(reset=int(ready)))
        master_link = SimpleNamespace(rx_rt_frame=endpoint.tx.rt_frame,
            rx_rt_data=endpoint.tx.rt_data,tx_rt_frame=endpoint.rx.rt_frame,
            tx_rt_data=endpoint.rx.rt_data)
        d.submodules.transport = t = SatelliteTransport(endpoint,pad,glbl_fine_ts_width=fine_bits)
        d.submodules.master = m = ClockDomainsRenamer({'sys':'master_tx','rtio_rx':'gth_tx'})(RTPacketMaster(master_link))
        replies, edges, errors = [], [], []
        def run():
            previous = 0
            previous_not = 0
            for cycle in range(800):
                yield m.buffer_space_not_ack.eq(1)
                yield m.sr_stb.eq(0)
                if cycle==5:
                    yield m.tsc_value.eq(1000)
                    yield m.set_time_stb.eq(1)
                if (yield m.set_time_ack): yield m.set_time_stb.eq(0)
                if cycle in (60,200):
                    self.assertEqual((yield m.sr_ack),1)
                    yield m.sr_notwrite.eq(1)
                    yield m.sr_address.eq(0)
                    yield m.sr_stb.eq(1)
                if cycle==100:
                    yield m.sr_notwrite.eq(0)
                    yield m.sr_address.eq(0)
                    yield m.sr_timestamp.eq(1450 << fine_bits)
                    yield m.sr_data.eq(1)
                    yield m.sr_stb.eq(1)
                notified = (yield m.buffer_space_not)
                if notified and not previous_not: replies.append((yield m.buffer_space))
                previous_not = notified
                value = (yield pad)
                if value!=previous: edges.append(((yield t.backend.tsc.coarse_ts),value))
                previous=value
                errors.append((yield t.reply_fault) | (yield m.err_unknown_packet_type) | (yield m.err_packet_truncated))
                yield
            self.assertEqual((yield t.tsc_load_count),int(ready))
        run_simulation(d,{'master_tx':run()},clocks={'sys':13,'master_tx':8,'rtio_rx':8,'gth_tx':(11,3)})
        self.assertEqual(replies,[128,127] if ready else [])
        self.assertEqual(edges,[(1461,1)] if ready else [])
        self.assertFalse(any(errors))

    def test_time_load_scheduled_ttl_and_async_buffer_replies(self):
        self.exercise()

    def test_kasli_three_fine_bits_preserve_coarse_scheduled_edge(self):
        self.exercise(fine_bits=3)

    def test_unready_rx_cannot_load_time_or_toggle_ttl(self):
        self.exercise(ready=False)

    def test_busy_reply_is_dropped_whole_and_latches_fault(self):
        d=RTReplyCDC()
        packets=[]
        def source():
            # Slow TX keeps first whole packet pending while second arrives.
            for values in ([0x1234,0x5678],[0xdead,0xbeef]):
                yield d.frame.eq(1)
                for value in values:
                    yield d.data.eq(value)
                    yield
                yield d.frame.eq(0)
                for _ in range(2): yield
            for _ in range(100): yield
            self.assertEqual((yield d.fault),1)
        @passive
        def sink():
            previous=0
            while True:
                frame=(yield d.output_frame)
                if frame and not previous: packets.append([])
                if frame: packets[-1].append((yield d.output_data))
                previous=frame
                yield
        run_simulation(d,{'rtio_rx':source(),'gth_tx':sink()},clocks={'rtio_rx':8,'gth_tx':(31,3)})
        self.assertEqual(packets,[[0x1234,0x5678]])
