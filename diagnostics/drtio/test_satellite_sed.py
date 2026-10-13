"""Serialized DRTIO writes through real upstream SED and TTL PHY.

LGPL-3.0-or-later. Ideal synchronous packet wires; no GTH/CDC qualification.
"""
import unittest
from types import SimpleNamespace
from migen import Module, Signal, ClockDomainsRenamer
from migen.sim import run_simulation
from artiq.gateware.drtio.rt_packet_master import RTPacketMaster
from satellite_backend import SatelliteBackend


def interface():
    return SimpleNamespace(tx_rt_frame=Signal(), tx_rt_data=Signal(16),
                           rx_rt_frame=Signal(), rx_rt_data=Signal(16))


class SatelliteSEDTest(unittest.TestCase):
    def make_dut(self, connected=True, with_input=False):
        dut = Module()
        pad = Signal()
        master_link, satellite_link = interface(), interface()
        dut.submodules.backend = SatelliteBackend(satellite_link, pad,
                                                   pad if with_input else None)
        dut.submodules.master = ClockDomainsRenamer({'rtio_rx': 'sys'})(RTPacketMaster(master_link))
        dut.comb += [satellite_link.rx_rt_frame.eq(master_link.tx_rt_frame if connected else 0),
                     satellite_link.rx_rt_data.eq(master_link.tx_rt_data),
                     master_link.rx_rt_frame.eq(satellite_link.tx_rt_frame),
                     master_link.rx_rt_data.eq(satellite_link.tx_rt_data)]
        return dut, pad

    def exercise(self, connected, advance=0, load_time=False, stale_write=False):
        dut, pad = self.make_dut(connected)
        edges, strobes, errors, loads, underflows = [], [], [], [], []
        base = 1240 if load_time else 240

        def run():
            previous = 0
            for cycle in range(420):
                # Hold set_time until the serializer acknowledges the complete packet.
                if load_time and cycle == 5:
                    yield dut.master.tsc_value.eq(1000)
                    yield dut.master.set_time_stb.eq(1)
                if (yield dut.master.set_time_ack):
                    yield dut.master.set_time_stb.eq(0)
                # Requests arrive long before their execution timestamps.
                if cycle in (40, 80, 120, 160):
                    index = (cycle - 40) // 40
                    self.assertEqual((yield dut.master.sr_ack), 1)
                    yield dut.master.sr_timestamp.eq(base + index * 32 - advance)
                    yield dut.master.sr_data.eq(1 - index % 2)
                    yield dut.master.sr_stb.eq(1)
                elif stale_write and cycle == 25:
                    yield dut.master.sr_timestamp.eq(10)
                    yield dut.master.sr_data.eq(1)
                    yield dut.master.sr_stb.eq(1)
                else:
                    yield dut.master.sr_stb.eq(0)
                timestamp = (yield dut.backend.tsc.coarse_ts)
                if (yield dut.backend.packet.tsc_load):
                    loads.append((yield dut.backend.packet.tsc_load_value))
                underflows.append(bool((yield dut.backend.rtio.cri.o_status) & 2))
                value = (yield pad)
                if value != previous:
                    edges.append((timestamp, value))
                    previous = value
                if (yield dut.backend.phy.rtlink.o.stb):
                    strobes.append((timestamp, (yield dut.backend.phy.rtlink.o.data)))
                errors.append((yield dut.backend.rtio.async_errors.raw_bits()))
                yield
        run_simulation(dut, run())
        self.assertEqual(strobes, [(base + 9 - advance + i * 32, 1 - i % 2) for i in range(4)] if connected else [])
        self.assertEqual(edges, [(base + 11 - advance + i * 32, 1 - i % 2) for i in range(4)] if connected else [])
        self.assertFalse(any(errors))
        self.assertEqual(loads, [1000] if load_time else [])
        self.assertEqual(any(underflows), stale_write)

    def test_scheduled_ttl(self):
        self.exercise(True)

    def test_sender_timestamp_advance(self):
        self.exercise(True, advance=11)

    def test_serialized_time_load_then_ttl(self):
        self.exercise(True, load_time=True)

    def test_stale_write_rejected_without_extra_edge(self):
        self.exercise(True, stale_write=True)

    def test_disconnected_packet_negative_control(self):
        self.exercise(False)


    def test_real_buffer_space_consumption_and_recovery(self):
        dut, pad = self.make_dut()
        replies, errors = [], []

        def run():
            for cycle in range(500):
                yield dut.master.sr_stb.eq(0)
                yield dut.master.buffer_space_not_ack.eq(1)
                if cycle in (20, 170, 420):
                    self.assertEqual((yield dut.master.sr_ack), 1)
                    yield dut.master.sr_notwrite.eq(1)
                    yield dut.master.sr_address.eq(0)
                    yield dut.master.sr_stb.eq(1)
                if cycle in (60, 80, 100, 120):
                    index = (cycle - 60) // 20
                    self.assertEqual((yield dut.master.sr_ack), 1)
                    yield dut.master.sr_notwrite.eq(0)
                    yield dut.master.sr_timestamp.eq(300 + 16 * index)
                    yield dut.master.sr_data.eq(1 - index % 2)
                    yield dut.master.sr_stb.eq(1)
                if (yield dut.master.buffer_space_not):
                    replies.append((yield dut.master.buffer_space))
                errors.append((yield dut.backend.packet.buffer_space_timeout))
                errors.append((yield dut.master.err_unknown_packet_type))
                errors.append((yield dut.master.err_packet_truncated))
                yield
        run_simulation(dut, run())
        self.assertEqual(replies, [128, 124, 128])
        self.assertFalse(any(errors))


    def test_ttl_input_event_and_empty_timeout(self):
        dut, pad = self.make_dut(with_input=True)
        replies, captured, errors = [], [], []

        def run():
            for cycle in range(650):
                yield dut.master.sr_stb.eq(0)
                yield dut.master.read_not_ack.eq(1)
                # Enable rising-edge input sensitivity before the TTL pulse.
                if cycle == 30:
                    yield dut.master.sr_notwrite.eq(0)
                    yield dut.master.sr_chan_sel.eq(1)
                    yield dut.master.sr_address.eq(2)
                    yield dut.master.sr_data.eq(1)
                    yield dut.master.sr_timestamp.eq(160)
                    yield dut.master.sr_stb.eq(1)
                if cycle in (80, 110):
                    yield dut.master.sr_notwrite.eq(0)
                    yield dut.master.sr_chan_sel.eq(0)
                    yield dut.master.sr_address.eq(0)
                    yield dut.master.sr_data.eq(1 if cycle == 80 else 0)
                    yield dut.master.sr_timestamp.eq(240 if cycle == 80 else 280)
                    yield dut.master.sr_stb.eq(1)
                if cycle in (350, 450):
                    self.assertEqual((yield dut.master.sr_ack), 1)
                    yield dut.master.sr_notwrite.eq(1)
                    yield dut.master.sr_chan_sel.eq(1)
                    yield dut.master.sr_address.eq(1)
                    yield dut.master.sr_timestamp.eq(500)
                    yield dut.master.sr_stb.eq(1)
                if (yield dut.backend.input_phy.rtlink.i.stb):
                    captured.append(((yield dut.backend.tsc.coarse_ts),
                                     (yield dut.backend.input_phy.rtlink.i.data)))
                if (yield dut.master.read_not):
                    replies.append(((yield dut.master.read_no_event),
                                    (yield dut.master.read_is_overflow),
                                    (yield dut.master.read_data),
                                    (yield dut.master.read_timestamp)))
                errors.append((yield dut.master.err_unknown_packet_type))
                errors.append((yield dut.master.err_packet_truncated))
                yield
        run_simulation(dut, run())
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0][1], 1)
        self.assertEqual(len(replies), 2)
        # Upstream defines is_overflow as a don't-care when no_event=0.
        self.assertEqual(replies[0][0], 0)
        self.assertEqual(replies[0][2:], (1, captured[0][0]))
        self.assertEqual(captured, [(253, 1)])
        self.assertEqual(replies[1][:2], (1, 0))
        self.assertFalse(any(errors))


if __name__ == '__main__':
    unittest.main()
