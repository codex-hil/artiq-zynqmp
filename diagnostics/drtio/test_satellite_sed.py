"""Serialized DRTIO writes through real upstream SED and TTL PHY.

LGPL-3.0-or-later. Ideal synchronous packet wires; no GTH/CDC qualification.
"""
import unittest
from types import SimpleNamespace
from migen import Module, Signal, ClockDomainsRenamer
from migen.sim import run_simulation
from artiq.gateware.drtio.core import SyncRTIO
from artiq.gateware.drtio.rt_packet_master import RTPacketMaster
from artiq.gateware.rtio.tsc import TSC
from artiq.gateware.rtio.channel import Channel
from artiq.gateware.rtio.phy.ttl_simple import Output
from satellite_packet import CheckedRTPacketSatellite


def interface():
    return SimpleNamespace(tx_rt_frame=Signal(), tx_rt_data=Signal(16),
                           rx_rt_frame=Signal(), rx_rt_data=Signal(16))


class SatelliteSEDTest(unittest.TestCase):
    def exercise(self, connected, advance=0, load_time=False, stale_write=False):
        dut = Module()
        pad = Signal()
        master_link, satellite_link = interface(), interface()
        dut.submodules.tsc = TSC()
        dut.submodules.phy = ClockDomainsRenamer({'rio_phy': 'sys'})(Output(pad))
        dut.submodules.unused_phy = ClockDomainsRenamer({'rio_phy': 'sys'})(Output(Signal()))
        dut.submodules.rtio = ClockDomainsRenamer({'rio': 'sys'})(
            SyncRTIO(dut.tsc, [Channel.from_phy(dut.phy), Channel.from_phy(dut.unused_phy)],
                     lane_count=8, fifo_depth=128))
        dut.submodules.satellite = CheckedRTPacketSatellite(satellite_link, dut.rtio.cri)
        dut.submodules.master = ClockDomainsRenamer({'rtio_rx': 'sys'})(RTPacketMaster(master_link))
        dut.comb += [satellite_link.rx_rt_frame.eq(master_link.tx_rt_frame if connected else 0),
                     satellite_link.rx_rt_data.eq(master_link.tx_rt_data),
                     master_link.rx_rt_frame.eq(satellite_link.tx_rt_frame),
                     master_link.rx_rt_data.eq(satellite_link.tx_rt_data),
                     dut.tsc.load.eq(dut.satellite.tsc_load),
                     dut.tsc.load_value.eq(dut.satellite.tsc_load_value)]
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
                timestamp = (yield dut.tsc.coarse_ts)
                if (yield dut.satellite.tsc_load):
                    loads.append((yield dut.satellite.tsc_load_value))
                underflows.append(bool((yield dut.rtio.cri.o_status) & 2))
                value = (yield pad)
                if value != previous:
                    edges.append((timestamp, value))
                    previous = value
                if (yield dut.phy.rtlink.o.stb):
                    strobes.append((timestamp, (yield dut.phy.rtlink.o.data)))
                errors.append((yield dut.rtio.async_errors.raw_bits()))
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


if __name__ == '__main__':
    unittest.main()
