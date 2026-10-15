"""Real SED/PHY reset preserves running TSC; LGPL-3.0-or-later."""
import unittest
from migen.sim import run_simulation
import test_satellite_sed as baseline


class SatelliteResetTests(unittest.TestCase):
    def test_clear_pending_events_preserve_tsc_and_reuse(self):
        d,pad=baseline.SatelliteSEDTest.make_dut(self)
        b,m=d.backend,d.master
        edges,replies,loads,reset_times=[],[],[],[]
        def run():
            previous=0
            last_tsc=None
            previous_not=0
            for cycle in range(800):
                yield m.sr_stb.eq(0)
                yield m.buffer_space_not_ack.eq(1)
                if cycle==5:
                    yield m.tsc_value.eq(1000)
                    yield m.set_time_stb.eq(1)
                if (yield m.set_time_ack):yield m.set_time_stb.eq(0)
                if cycle==30 or cycle in (60,80,100,120) or cycle==260:
                    self.assertEqual((yield m.sr_ack),1)
                    yield m.sr_notwrite.eq(0)
                    yield m.sr_address.eq(0)
                    timestamp=1110 if cycle==30 else 1500 if cycle==260 else 1450+(cycle-60)//20*32
                    data=1 if cycle in (30,260) else ((cycle-60)//20)%2
                    yield m.sr_timestamp.eq(timestamp)
                    yield m.sr_data.eq(data)
                    yield m.sr_stb.eq(1)
                if cycle in (160,220):
                    yield m.sr_notwrite.eq(1)
                    yield m.sr_address.eq(0)
                    yield m.sr_stb.eq(1)
                if cycle==180:
                    yield b.rtio_reset.eq(1)
                    yield b.phy_reset.eq(1)
                    reset_times.append((yield b.tsc.coarse_ts))
                if cycle==200:
                    yield b.rtio_reset.eq(0)
                    yield b.phy_reset.eq(0)
                if 186 <= cycle <= 199:
                    self.assertEqual((yield b.reset_applied),1)
                    self.assertEqual((yield pad),0)
                if cycle==205:self.assertEqual((yield b.reset_applied),0)
                timestamp=(yield b.tsc.coarse_ts)
                if 170 <= cycle <= 210 and last_tsc is not None:
                    self.assertEqual(timestamp,last_tsc+1)
                last_tsc=timestamp
                notified=(yield m.buffer_space_not)
                if notified and not previous_not:replies.append((yield m.buffer_space))
                previous_not=notified
                value=(yield pad)
                if value!=previous:edges.append((timestamp,value))
                previous=value
                if (yield b.packet.tsc_load):loads.append((yield b.packet.tsc_load_value))
                self.assertEqual((yield m.err_packet_truncated),0)
                self.assertEqual((yield m.err_unknown_packet_type),0)
                yield
        run_simulation(d,run())
        self.assertEqual(loads,[1000])
        self.assertEqual(replies,[124,128])
        self.assertEqual(len(edges),3)
        self.assertEqual(edges[0],(1121,1))
        self.assertEqual(edges[1][1],0)
        self.assertLessEqual(reset_times[0],edges[1][0])
        self.assertLessEqual(edges[1][0],reset_times[0]+4)
        self.assertEqual(edges[2],(1511,1))

    def test_pending_input_is_cleared_without_phantom_event(self):
        d,pad=baseline.SatelliteSEDTest.make_dut(self,with_input=True)
        b,m=d.backend,d.master
        captures,replies=[],[]
        def run():
            previous_not=0
            for cycle in range(650):
                yield m.sr_stb.eq(0)
                yield m.read_not_ack.eq(1)
                if cycle==30:
                    yield m.sr_notwrite.eq(0);yield m.sr_chan_sel.eq(1)
                    yield m.sr_address.eq(2);yield m.sr_data.eq(1)
                    yield m.sr_timestamp.eq(160);yield m.sr_stb.eq(1)
                if cycle in (80,110):
                    yield m.sr_notwrite.eq(0);yield m.sr_chan_sel.eq(0)
                    yield m.sr_address.eq(0)
                    yield m.sr_data.eq(1 if cycle==80 else 0)
                    yield m.sr_timestamp.eq(240 if cycle==80 else 280)
                    yield m.sr_stb.eq(1)
                if cycle==320:yield b.rtio_reset.eq(1)
                if cycle==340:yield b.rtio_reset.eq(0)
                if cycle==380:
                    self.assertEqual((yield m.sr_ack),1)
                    yield m.sr_notwrite.eq(1);yield m.sr_chan_sel.eq(1)
                    yield m.sr_address.eq(1);yield m.sr_timestamp.eq(420)
                    yield m.sr_stb.eq(1)
                if (yield b.input_phy.rtlink.i.stb):
                    captures.append(((yield b.tsc.coarse_ts),(yield b.input_phy.rtlink.i.data)))
                notified=(yield m.read_not)
                if notified and not previous_not:
                    replies.append(((yield m.read_no_event),(yield m.read_is_overflow)))
                previous_not=notified
                yield
        run_simulation(d,run())
        self.assertEqual(captures,[(253,1)])
        self.assertEqual(replies,[(1,0)])

    def test_queue_only_reset_preserves_output_state(self):
        d,pad=baseline.SatelliteSEDTest.make_dut(self)
        b,m=d.backend,d.master
        replies=[]
        def run():
            previous_not=0
            last_tsc=None
            for cycle in range(600):
                yield m.sr_stb.eq(0)
                yield m.buffer_space_not_ack.eq(1)
                if cycle in (30,80):
                    yield m.sr_notwrite.eq(0);yield m.sr_address.eq(0)
                    yield m.sr_timestamp.eq(120 if cycle==30 else 300)
                    yield m.sr_data.eq(1 if cycle==30 else 0)
                    yield m.sr_stb.eq(1)
                if cycle==200:yield b.rtio_reset.eq(1)
                if cycle==220:yield b.rtio_reset.eq(0)
                if cycle==260:
                    yield m.sr_notwrite.eq(1);yield m.sr_address.eq(0)
                    yield m.sr_stb.eq(1)
                if cycle>=140:self.assertEqual((yield pad),1)
                now=(yield b.tsc.coarse_ts)
                if last_tsc is not None:self.assertEqual(now,last_tsc+1)
                last_tsc=now
                notified=(yield m.buffer_space_not)
                if notified and not previous_not:replies.append((yield m.buffer_space))
                previous_not=notified
                yield
        run_simulation(d,run())
        self.assertEqual(replies,[128])
